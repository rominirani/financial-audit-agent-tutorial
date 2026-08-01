"""Main orchestration script for the Insurance Claims Processing Agent Team.

Usage:
    python main.py --mode=dev --project-id=YOUR_PROJECT_ID
"""
import asyncio
import argparse
import os
from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from tools.delegation_tools import configure
from policies.claims_policies import DEVELOPMENT_POLICIES, STAGING_POLICIES, PRODUCTION_POLICIES, ADJUDICATOR_WRITE_POLICY
from hooks.observability import CLAIMS_HOOKS

async def main():
    parser = argparse.ArgumentParser(description="Insurance Claims Processing Agent Team")
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

    # Configure delegation state and inject adjudicator policies
    configure(project_id=args.project_id, workspace=workspace_dir, adjudicator_policies=ADJUDICATOR_WRITE_POLICY)

    # Build orchestrator config
    config = get_orchestrator_config(
        workspace=workspace_dir,
        project_id=args.project_id,
    )
    config.policies = policies
    config.hooks = CLAIMS_HOOKS

    print(f"🚀 Starting Claims Processing (Delegation Architecture) — Mode: {args.mode}")
    print(f"📋 Policies: {len(policies)} rules loaded")
    print(f"🔗 Vertex AI: {args.project_id}\n")

    async with Agent(config) as agent:
        response = await agent.chat(
            "Process all pending insurance claims using your delegation tools."
        )

        # Print the agent's response
        print("\n" + "=" * 60)
        print("📊 CLAIMS REPORT")
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
