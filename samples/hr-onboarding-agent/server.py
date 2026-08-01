"""HTTP server for running the HR Onboarding Agent on Cloud Run.

Wraps the agent in a Flask endpoint so it can be invoked via HTTP POST.
Uses PRODUCTION_POLICIES (fully autonomous, no human prompts) since
there's no terminal for interactive approval on Cloud Run.

Usage (local testing):
    export PROJECT_ID="your-project-id"
    python server.py

Invoke:
    curl -X POST http://localhost:8080/verify \
      -H "Content-Type: application/json" \
      -d '{}'
"""
import asyncio
import json
import os

from flask import Flask, request, jsonify
from google.antigravity import Agent

from agents.orchestrator import get_orchestrator_config
from policies.compliance_policies import PRODUCTION_POLICIES
from hooks.observability import ONBOARDING_HOOKS
import tools.delegation_tools as delegation_tools

app = Flask(__name__)


@app.route("/verify", methods=["POST"])
def verify_onboarding():
    """Execute the onboarding compliance workflow and return results as JSON."""
    data = request.get_json(silent=True) or {}
    project_id = os.environ.get("PROJECT_ID")

    if not project_id:
        return jsonify({"error": "PROJECT_ID environment variable is not set"}), 500

    # Run the async agent in a sync Flask handler
    result = asyncio.run(_execute_verification(project_id))
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({"status": "healthy"}), 200


async def _execute_verification(project_id: str) -> dict:
    """Run the agent and return structured results."""
    workspace_dir = os.path.abspath(os.path.dirname(__file__))

    # Configure delegation tools for production
    delegation_tools.configure(
        project_id=project_id,
        workspace=workspace_dir,
        checker_policies=PRODUCTION_POLICIES,
    )

    config = get_orchestrator_config(
        policies=PRODUCTION_POLICIES,
        workspace=workspace_dir,
        project_id=project_id,
    )
    config.hooks = ONBOARDING_HOOKS

    async with Agent(config) as agent:
        response = await agent.chat(
            "Process all pending new hire onboarding verifications. "
            "Delegate to your specialist subagents: "
            "first the HR Researcher to gather hire records and requirements, "
            "then the Document Verifier for each submitted PDF, "
            "then the Compliance Checker to cross-reference and write results. "
            "Produce the final compliance report when all subagents have reported back."
        )

        report = await response.text()
        usage = agent.conversation.total_usage

    return {
        "report": report,
        "token_usage": {
            "prompt_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "thinking_tokens": usage.thoughts_token_count,
            "total_tokens": usage.total_token_count,
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
