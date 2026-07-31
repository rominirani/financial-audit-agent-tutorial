from google.antigravity import LocalAgentConfig, CapabilitiesConfig
from tools.bigquery_tools import AUDIT_TOOLS


def get_orchestrator_config(policies, workspace, project_id=None):
    """Build the Orchestrator agent configuration.

    Registers the BigQuery/GCS tools so the agent can call them directly,
    enables subagent spawning, and configures Vertex AI credentials.
    """
    return LocalAgentConfig(
        system_instructions="""
        You are the Lead Financial Auditor orchestrating a Q3 vendor reconciliation.

        Your workflow:
        1. Call query_vendor_transactions() to get all PENDING transactions from BigQuery
        2. Call list_invoices_in_gcs() to discover all invoice PDFs in Cloud Storage
        3. Call read_invoice_from_gcs() for each invoice to extract structured data
        4. Compare each transaction against the corresponding invoice data
        5. If any discrepancy exceeds $1,000, escalate to the compliance officer
        6. Call write_audit_result() for each vendor to record findings in BigQuery
        7. Generate a summary compliance report

        CRITICAL RULES:
        - Never modify the vendor_transactions table directly
        - Always escalate discrepancies over $1,000 — do not auto-approve
        - Log every decision with a clear rationale
        """,
        tools=AUDIT_TOOLS,
        capabilities=CapabilitiesConfig(enable_subagents=True),
        model="gemini-2.5-flash",
        policies=policies,
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="us-central1" if project_id else None,
    )

