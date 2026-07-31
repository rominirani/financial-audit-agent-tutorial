"""Invoice Analyzer subagent configuration.

This agent has READ-ONLY access to GCS. It reads invoice PDF files
and extracts structured data. It CANNOT query BigQuery or write
any data.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.bigquery_tools import read_invoice_from_gcs


def get_invoice_analyzer_config(workspace, project_id=None):
    """Build the Invoice Analyzer subagent configuration.

    Args:
        workspace: Absolute path to the project workspace.
        project_id: GCP project ID for Vertex AI.
    """
    return LocalAgentConfig(
        system_instructions="""
        You are an Invoice Analysis Specialist. Your job is to read a single
        invoice PDF from Google Cloud Storage and extract structured data.

        For the invoice, extract:
        - vendor_id: the vendor identifier
        - vendor_name: the vendor's name
        - invoice_num: the invoice number
        - base_amount: the pre-tax amount
        - tax_rate: the tax rate as a decimal (e.g. 0.10)
        - tax_amount: the calculated tax
        - total_amount: the total including tax
        - currency: the currency code (e.g. "USD")

        Return results as a single JSON object with these fields.
        If any field cannot be extracted, set it to null and note the issue.
        """,
        tools=[read_invoice_from_gcs],
        model="gemini-2.5-flash",
        policies=[
            policy.deny_all(),
            policy.allow("read_invoice_from_gcs"),
        ],
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="us-central1" if project_id else None,
    )
