"""Evaluation runner for the Insurance Claims Agent.

Loads test cases from a JSONL dataset, sends each prompt to the agent,
and checks whether expected keywords appear in the response.
"""
import asyncio
import argparse
import json
import os
import sys

# Add project root to path so we can import agents/ and tools/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from tools.delegation_tools import configure
from policies.claims_policies import DEVELOPMENT_POLICIES, ADJUDICATOR_WRITE_POLICY
from hooks.observability import CLAIMS_HOOKS


async def run_eval(eval_file: str, project_id: str):
    """Run each eval case and check agent output against expected keywords."""

    # Load test cases
    with open(eval_file) as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"📋 Loaded {len(cases)} eval cases from {eval_file}\n")

    workspace_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    passed = 0
    failed = 0

    for i, case in enumerate(cases, 1):
        print(f"--- Eval Case {i}/{len(cases)}: {case['input']} ---")

        # Must configure per evaluation run to reset state
        configure(project_id=project_id, workspace=workspace_dir, adjudicator_policies=ADJUDICATOR_WRITE_POLICY)

        # Build agent config (same as main.py, using dev policies)
        config = get_orchestrator_config(
            workspace=workspace_dir,
            project_id=project_id,
        )
        config.policies = DEVELOPMENT_POLICIES
        config.hooks = CLAIMS_HOOKS

        async with Agent(config) as agent:
            # Send the eval prompt to the agent
            response = await agent.chat(case["input"])
            result = await response.text()

            # Check if ALL expected keywords appear in the response
            keywords = [kw.strip().lower() for kw in case["expected_outcome"].split(",")]
            result_lower = result.lower()
            missing = [kw for kw in keywords if kw not in result_lower]

            if not missing:
                print(f"✅ PASS\n")
                passed += 1
            else:
                print(f"❌ FAIL — missing keywords: {missing}")
                print(f"   Response preview: {result[:300]}...\n")
                failed += 1

    # Summary
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"📊 EVAL RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run agent evaluations")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--dataset", default="eval/eval_dataset.jsonl", help="Path to eval dataset")
    args = parser.parse_args()

    success = asyncio.run(run_eval(args.dataset, args.project_id))
    sys.exit(0 if success else 1)
