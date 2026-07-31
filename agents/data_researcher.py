"""Data Researcher subagent configuration.

This agent has READ-ONLY access to BigQuery and GCS. It queries
vendor transactions and lists invoice PDFs. It CANNOT write audit
results or modify any data.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.bigquery_tools import query_vendor_transactions, list_invoices_in_gcs


def get_data_researcher_config(workspace, project_id=None):
    """Build the Data Researcher subagent configuration.

    Args:
        workspace: Absolute path to the project workspace.
        project_id: GCP project ID for Vertex AI.
    """
    return LocalAgentConfig(
        system_instructions="""
        You are a Data Research Specialist. Your job is to:
        1. Query BigQuery for PENDING vendor transaction records
        2. List all invoice PDF files in the GCS bucket

        You have READ-ONLY access. You CANNOT write audit results or modify data.

        Return your results as structured JSON with two sections:
        {
            "transactions": [
                {"vendor_id": "...", "invoice_num": "...", "amount": ..., "currency": "...", "tax_rate": ..., "status": "..."},
                ...
            ],
            "invoices": [
                {"path": "Q3/INV-xxxx.pdf", "name": "INV-xxxx.pdf"},
                ...
            ],
            "summary": {
                "total_transactions": N,
                "total_invoices": N,
                "data_quality_issues": ["...", ...]
            }
        }
        """,
        tools=[query_vendor_transactions, list_invoices_in_gcs],
        model="gemini-2.5-flash",
        policies=[
            policy.deny_all(),
            policy.allow("query_vendor_transactions"),
            policy.allow("list_invoices_in_gcs"),
        ],
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="us-central1" if project_id else None,
    )
