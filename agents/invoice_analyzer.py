from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy


def get_invoice_analyzer_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are an Invoice Analysis Specialist. Your job is to read invoice
        PDF files from Google Drive and extract structured data.

        For each invoice, extract:
        - Vendor name and ID
        - Invoice number
        - Line item amounts
        - Tax amounts and rates
        - Total invoice amount
        - Currency

        Return results as structured JSON.
        """,
        policies=[
            policy.deny_all(),
            policy.allow("view_file"),
            policy.allow("list_dir"),
        ],
        workspaces=[workspace],
    )
