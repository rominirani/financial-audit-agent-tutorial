from google.antigravity import LocalAgentConfig, CapabilitiesConfig


def get_orchestrator_config(policies, workspace, project_id=None):
    return LocalAgentConfig(
        system_instructions="""
        You are the Lead Financial Auditor orchestrating a Q3 vendor reconciliation.

        Your workflow:
        1. Query BigQuery for all PENDING vendor transactions for Q3
        2. For each vendor, retrieve their invoice PDF from Google Drive
        3. Spawn a Reconciliation subagent to match transaction amounts against invoice amounts
        4. If any discrepancy exceeds $1,000, escalate to the compliance officer
        5. Write reconciled results to the BigQuery audit_results table
        6. Generate a summary report

        CRITICAL RULES:
        - Never modify the vendor_transactions table directly
        - Always escalate discrepancies over $1,000 — do not auto-approve
        - Log every decision with a clear rationale
        """,
        capabilities=CapabilitiesConfig(enable_subagents=True),
        model="gemini-2.5-flash",
        policies=policies,
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="us-central1" if project_id else None,
    )
