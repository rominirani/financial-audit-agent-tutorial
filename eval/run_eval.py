"""Evaluation runner for the Financial Audit Agent.

Loads test cases from a JSONL dataset, sends each prompt to the agent,
and checks whether expected keywords appear in the response.

Usage:
    python eval/run_eval.py --project-id=YOUR_PROJECT_ID
    python eval/run_eval.py --project-id=YOUR_PROJECT_ID --dataset=eval/eval_dataset.jsonl
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
from policies.audit_policies import DEVELOPMENT_POLICIES
from hooks.observability import AUDIT_HOOKS
import tools.delegation_tools as delegation_tools


async def run_eval(eval_file: str, project_id: str):
    """Run each eval case and check agent output against expected keywords."""

    # Load test cases
    with open(eval_file) as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"📋 Loaded {len(cases)} eval cases from {eval_file}\n")

    workspace_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Configure delegation tools — subagents need project_id and workspace
    # to create their own Vertex AI connections.
    delegation_tools.configure(
        project_id=project_id,
        workspace=workspace_dir,
        reconciler_policies=DEVELOPMENT_POLICIES,
    )

    # Build agent config (same as main.py, using dev policies)
    config = get_orchestrator_config(
        policies=DEVELOPMENT_POLICIES,
        workspace=workspace_dir,
        project_id=project_id,
    )
    config.hooks = AUDIT_HOOKS

    passed = 0
    failed = 0

    async with Agent(config) as agent:
        for i, case in enumerate(cases, 1):
            print(f"--- Eval Case {i}/{len(cases)}: {case['input']} ---")

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
