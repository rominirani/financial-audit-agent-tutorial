"""Main orchestration script for the Financial Audit Agent Team.

Usage:
    python main.py --mode=dev --quarter=Q3 --project-id=YOUR_PROJECT_ID
"""
import asyncio
import argparse
import os
from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from policies.audit_policies import DEVELOPMENT_POLICIES, STAGING_POLICIES, PRODUCTION_POLICIES
from hooks.observability import AUDIT_HOOKS

async def main():
    parser = argparse.ArgumentParser(description="Financial Audit Agent Team")
    parser.add_argument("--mode", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument("--quarter", default="Q3")
    parser.add_argument("--project-id", default=None, help="GCP project ID for Vertex AI")
    args = parser.parse_args()

    # Select policy set
    policies = {
        "dev": DEVELOPMENT_POLICIES,
        "staging": STAGING_POLICIES,
        "prod": PRODUCTION_POLICIES,
    }[args.mode]

    workspace_dir = os.path.abspath(os.path.dirname(__file__))

    # Build orchestrator config
    config = get_orchestrator_config(
        policies=policies,
        workspace=workspace_dir,
        project_id=args.project_id,
        quarter=args.quarter,
    )
    config.hooks = AUDIT_HOOKS

    print(f"🚀 Starting Financial Audit — Mode: {args.mode}, Quarter: {args.quarter}")
    print(f"📋 Policies: {len(policies)} rules loaded")
    print(f"🔗 Vertex AI: {args.project_id}\n")

    async with Agent(config) as agent:
        response = await agent.chat(
            f"Execute the full {args.quarter} vendor invoice reconciliation now. "
            f"Complete ALL steps: query transactions, list invoices, read EVERY invoice PDF, "
            f"reconcile each transaction against its invoice, write audit results, "
            f"and produce the final compliance report. Do not stop until the report is complete."
        )

        # Print the agent's response
        print("\n" + "=" * 60)
        print("📊 AUDIT RESULTS")
        print("=" * 60)
        print(await response.text())

        # Token usage summary
        usage = agent.conversation.total_usage
        print(f"\n💰 Token Usage Summary:")
        print(f"   Prompt tokens:    {usage.prompt_token_count}")
        print(f"   Output tokens:    {usage.candidates_token_count}")
        print(f"   Thinking tokens:  {usage.thoughts_token_count}")
        print(f"   Total tokens:     {usage.total_token_count}")

if __name__ == "__main__":
    asyncio.run(main())
