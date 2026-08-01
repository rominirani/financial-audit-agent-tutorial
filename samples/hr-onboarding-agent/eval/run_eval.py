"""Evaluation runner for the HR Onboarding Compliance Agent Team.

Usage:
    python -m eval.run_eval --dataset eval/eval_dataset.jsonl --project-id YOUR_PROJECT_ID

Evaluates the agent against a JSONL dataset of input prompts and expected
tool invocations to verify the delegation architecture works correctly.
"""
import argparse
import json
import os

from google.antigravity import Agent, EvalConfig
from agents.orchestrator import get_orchestrator_config
from policies.compliance_policies import DEVELOPMENT_POLICIES
import tools.delegation_tools as delegation_tools


def run_eval(dataset_path: str, project_id: str):
    """Run eval for the HR Onboarding Agent Team."""

    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Configure delegation tools — subagents need project_id and workspace
    delegation_tools.configure(
        project_id=project_id,
        workspace=workspace_dir,
        checker_policies=DEVELOPMENT_POLICIES,
    )

    config = get_orchestrator_config(
        policies=DEVELOPMENT_POLICIES,
        workspace=workspace_dir,
        project_id=project_id,
    )

    print(f"📋 Running evaluation on: {dataset_path}")
    print(f"🔗 Project: {project_id}")

    eval_config = EvalConfig(
        agent_config=config,
        dataset_path=dataset_path,
    )

    results = eval_config.run()

    # Print summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}")
    for r in results:
        status = "✅" if r.passed else "❌"
        print(f"  {status} {r.test_case_id}: {r.summary}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HR Onboarding Agent Eval Runner")
    parser.add_argument("--dataset", default="eval/eval_dataset.jsonl",
                        help="Path to JSONL evaluation dataset")
    parser.add_argument("--project-id", default=None,
                        help="GCP project ID for Vertex AI")
    args = parser.parse_args()

    project_id = args.project_id or os.environ.get("PROJECT_ID")
    if not project_id:
        print("Error: --project-id or PROJECT_ID env var required")
        exit(1)

    run_eval(args.dataset, project_id)
