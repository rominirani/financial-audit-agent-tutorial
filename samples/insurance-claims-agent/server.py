"""HTTP server for running the Insurance Claims Agent on Cloud Run.

Wraps the agent in a Flask endpoint so it can be invoked via HTTP POST.
Uses PRODUCTION_POLICIES.
"""
import asyncio
import json
import os

from flask import Flask, request, jsonify
from google.antigravity import Agent

from tools.delegation_tools import configure
from agents.orchestrator import get_orchestrator_config
from policies.claims_policies import PRODUCTION_POLICIES, ADJUDICATOR_WRITE_POLICY
from hooks.observability import CLAIMS_HOOKS

app = Flask(__name__)


@app.route("/process", methods=["POST"])
def run_process():
    """Execute the claims processing workflow and return results as JSON."""
    data = request.get_json(silent=True) or {}
    project_id = os.environ.get("PROJECT_ID")

    if not project_id:
        return jsonify({"error": "PROJECT_ID environment variable is not set"}), 500

    result = asyncio.run(_execute_process(project_id))
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({"status": "healthy"}), 200


async def _execute_process(project_id: str) -> dict:
    """Run the agent and return structured results."""
    workspace_dir = os.path.abspath(os.path.dirname(__file__))

    # Configure delegation state
    configure(project_id=project_id, workspace=workspace_dir, adjudicator_policies=ADJUDICATOR_WRITE_POLICY)

    config = get_orchestrator_config(
        workspace=workspace_dir,
        project_id=project_id,
    )
    config.policies = PRODUCTION_POLICIES
    config.hooks = CLAIMS_HOOKS

    async with Agent(config) as agent:
        response = await agent.chat(
            "Process all pending insurance claims using your delegation tools."
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
