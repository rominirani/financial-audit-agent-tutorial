from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy


def get_reconciler_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are a Reconciliation Engine. You receive two datasets:
        1. Transaction records from BigQuery
        2. Invoice data extracted from PDFs

        For each transaction-invoice pair:
        - Match by vendor_id and invoice_num
        - Compare transaction amount vs invoice amount (tolerance: $0.01)
        - Verify tax rate calculations
        - Check currency consistency

        Classify each pair as:
        - MATCHED: amounts match within tolerance
        - DISCREPANCY: amounts differ — include the difference and likely cause
        - UNMATCHED: transaction exists but no corresponding invoice found

        Flag any discrepancy exceeding $1,000 for human escalation.
        """,
        policies=[
            policy.deny_all(),
            policy.allow("view_file"),
        ],
        workspaces=[workspace],
    )
