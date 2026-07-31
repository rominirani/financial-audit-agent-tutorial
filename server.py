"""HTTP server for running the Financial Audit Agent on Cloud Run.

Wraps the agent in a Flask endpoint so it can be invoked via HTTP POST.
Uses PRODUCTION_POLICIES (fully autonomous, no human prompts) since
there's no terminal for interactive approval on Cloud Run.

Usage (local testing):
    export PROJECT_ID="your-project-id"
    python server.py

Invoke:
    curl -X POST http://localhost:8080/audit \
      -H "Content-Type: application/json" \
      -d '{"quarter": "Q3"}'
"""
import asyncio
import json
import os

from flask import Flask, request, jsonify
from google.antigravity import Agent

from agents.orchestrator import get_orchestrator_config
from policies.audit_policies import PRODUCTION_POLICIES
from hooks.observability import AUDIT_HOOKS

app = Flask(__name__)


@app.route("/audit", methods=["POST"])
def run_audit():
    """Execute the financial audit workflow and return results as JSON."""
    data = request.get_json(silent=True) or {}
    quarter = data.get("quarter", "Q3")
    project_id = os.environ.get("PROJECT_ID")

    if not project_id:
        return jsonify({"error": "PROJECT_ID environment variable is not set"}), 500

    # Run the async agent in a sync Flask handler
    result = asyncio.run(_execute_audit(quarter, project_id))
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({"status": "healthy"}), 200


async def _execute_audit(quarter: str, project_id: str) -> dict:
    """Run the agent and return structured results."""
    workspace_dir = os.path.abspath(os.path.dirname(__file__))

    config = get_orchestrator_config(
        policies=PRODUCTION_POLICIES,
        workspace=workspace_dir,
        project_id=project_id,
        quarter=quarter,
    )
    config.hooks = AUDIT_HOOKS

    async with Agent(config) as agent:
        response = await agent.chat(
            f"Execute the full {quarter} vendor invoice reconciliation now. "
            f"Complete ALL steps: query transactions, list invoices, read EVERY invoice PDF, "
            f"reconcile each transaction against its invoice, write audit results, "
            f"and produce the final compliance report. Do not stop until the report is complete."
        )

        report = await response.text()
        usage = agent.conversation.total_usage

    return {
        "quarter": quarter,
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
