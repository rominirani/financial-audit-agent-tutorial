"""Main orchestration script for the HR Onboarding Compliance Agent Team.

Usage:
    python main.py --mode=dev --project-id=YOUR_PROJECT_ID

The orchestrator delegates to specialist subagents:
  - HR Researcher: queries BigQuery for hires + requirements (read-only)
  - Document Verifier: reads and parses onboarding PDFs (read-only)
  - Compliance Checker: cross-references and writes results (write access)
"""
import asyncio
import argparse
import os
from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from policies.compliance_policies import DEVELOPMENT_POLICIES, STAGING_POLICIES, PRODUCTION_POLICIES
from hooks.observability import ONBOARDING_HOOKS
import tools.delegation_tools as delegation_tools

async def main():
    parser = argparse.ArgumentParser(description="HR Onboarding Compliance Agent Team")
    parser.add_argument("--mode", choices=["dev", "staging", "prod"], default="dev")
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
    # to create their own Vertex AI connections. The compliance checker also needs
    # the mode-dependent policies to control write access.
    delegation_tools.configure(
        project_id=args.project_id,
        workspace=workspace_dir,
        checker_policies=policies,
    )

    # Build orchestrator config — uses delegation tools, NOT direct data tools
    config = get_orchestrator_config(
        policies=policies,
        workspace=workspace_dir,
        project_id=args.project_id,
    )
    config.hooks = ONBOARDING_HOOKS

    print(f"🚀 Starting HR Onboarding — Mode: {args.mode}")
    print(f"📋 Policies: {len(policies)} rules loaded")
    print(f"🔗 Vertex AI: {args.project_id}")
    print(f"🤖 Subagents: HR Researcher → Document Verifier → Compliance Checker\n")

    async with Agent(config) as agent:
        response = await agent.chat(
            "Process all pending new hire onboarding verifications. "
            "Delegate to your specialist subagents: "
            "first the HR Researcher to gather hire records and requirements, "
            "then the Document Verifier for each submitted PDF, "
            "then the Compliance Checker to cross-reference and write results. "
            "Produce the final compliance report when all subagents have reported back."
        )

        # Print the agent's response
        print("\n" + "=" * 60)
        print("📊 COMPLIANCE RESULTS")
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
