"""Main orchestration script for the Financial Audit Agent Team.

Usage:
    python main.py --mode=dev --quarter=Q3 --project-id=YOUR_PROJECT_ID

The orchestrator delegates to specialist subagents:
  - Data Researcher: queries BigQuery + lists GCS invoices (read-only)
  - Invoice Analyzer: reads and parses individual PDFs (read-only)
  - Reconciler: reconciles data + writes audit results (write access)
"""
import asyncio
import argparse
import os
from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from policies.audit_policies import DEVELOPMENT_POLICIES, STAGING_POLICIES, PRODUCTION_POLICIES
from hooks.observability import AUDIT_HOOKS
import tools.delegation_tools as delegation_tools

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

    # Configure delegation tools — subagents need project_id and workspace
    # to create their own Vertex AI connections. The reconciler also needs
    # the mode-dependent policies to control write access.
    delegation_tools.configure(
        project_id=args.project_id,
        workspace=workspace_dir,
        reconciler_policies=policies,
    )

    # Build orchestrator config — uses delegation tools, NOT direct data tools
    config = get_orchestrator_config(
        policies=policies,
        workspace=workspace_dir,
        project_id=args.project_id,
        quarter=args.quarter,
    )
    config.hooks = AUDIT_HOOKS

    print(f"🚀 Starting Financial Audit — Mode: {args.mode}, Quarter: {args.quarter}")
    print(f"📋 Policies: {len(policies)} rules loaded")
    print(f"🔗 Vertex AI: {args.project_id}")
    print(f"🤖 Subagents: Data Researcher → Invoice Analyzer → Reconciler\n")

    async with Agent(config) as agent:
        response = await agent.chat(
            f"Execute the full {args.quarter} vendor invoice reconciliation now. "
            f"Delegate to your specialist subagents: "
            f"first the Data Researcher to gather transaction data and invoice listings, "
            f"then the Invoice Analyzer for each PDF, "
            f"then the Reconciler to compare and write audit results. "
            f"Produce the final compliance report when all subagents have reported back."
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
