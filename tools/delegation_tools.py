"""Delegation tools for the Financial Audit Orchestrator.

Instead of giving the orchestrator direct access to BigQuery/GCS tools,
we wrap each subagent as a delegation tool. The orchestrator calls these
functions, which internally spawn a specialist subagent with restricted
tool access, run it, and return the result.

This enforces true separation of concerns:
  - Data Researcher: read-only BigQuery + GCS listing
  - Invoice Analyzer: read-only GCS PDF extraction
  - Reconciler: write audit results to BigQuery
"""
from google.antigravity import Agent

# Module-level config — set by main.py before the orchestrator starts
_project_id = None
_workspace = None
_reconciler_policies = None


def configure(project_id: str, workspace: str, reconciler_policies: list):
    """Initialize delegation config. Called once from main.py before agent starts.

    Args:
        project_id: GCP project ID for Vertex AI.
        workspace: Absolute path to the project workspace.
        reconciler_policies: Policy list for the reconciler (mode-dependent).
    """
    global _project_id, _workspace, _reconciler_policies
    _project_id = project_id
    _workspace = workspace
    _reconciler_policies = reconciler_policies


async def delegate_to_data_researcher(quarter: str = "Q3") -> str:
    """Delegate to the Data Researcher subagent to query BigQuery for
    pending vendor transactions and list invoice PDFs in GCS.

    The Data Researcher has READ-ONLY access to BigQuery and GCS.
    It cannot write audit results or modify any data.

    Args:
        quarter: The fiscal quarter to research (e.g. "Q3").

    Returns:
        JSON string with transaction records and invoice file listing.
    """
    from agents.data_researcher import get_data_researcher_config

    config = get_data_researcher_config(
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as researcher:
        response = await researcher.chat(
            f"Query all PENDING vendor transactions for quarter '{quarter}' "
            f"from BigQuery. Also list all invoice PDF files in the GCS bucket. "
            f"Return the complete results as structured JSON with two sections: "
            f"'transactions' and 'invoices'."
        )
        return await response.text()


async def delegate_to_invoice_analyzer(invoice_path: str) -> str:
    """Delegate to the Invoice Analyzer subagent to read and extract
    structured data from a single invoice PDF in GCS.

    The Invoice Analyzer has READ-ONLY access to GCS.
    It cannot query BigQuery or write any data.

    Args:
        invoice_path: Path to the invoice in GCS (e.g. "Q3/INV-8492-Q3-001.pdf").

    Returns:
        JSON string with extracted invoice data (vendor_id, invoice_num,
        base_amount, tax_rate, tax_amount, total_amount, currency).
    """
    from agents.invoice_analyzer import get_invoice_analyzer_config

    config = get_invoice_analyzer_config(
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as analyzer:
        response = await analyzer.chat(
            f"Read the invoice PDF at path '{invoice_path}' from the GCS bucket. "
            f"Extract all structured fields: vendor_id, vendor_name, invoice_num, "
            f"base_amount, tax_rate, tax_amount, total_amount, and currency. "
            f"Return the extracted data as a JSON object."
        )
        return await response.text()


async def delegate_to_reconciler(
    transactions_json: str,
    invoices_json: str,
    execution_id: str = "AUDIT-Q3",
) -> str:
    """Delegate to the Reconciliation Engine subagent to compare transactions
    against invoices, classify findings, and write audit results to BigQuery.

    The Reconciler is the ONLY subagent with write access to BigQuery
    (subject to the current policy tier: dev/staging/prod).

    Args:
        transactions_json: JSON string with transaction records from BigQuery.
        invoices_json: JSON string with extracted invoice data from all PDFs.
        execution_id: Unique ID for this audit run.

    Returns:
        Text report with reconciliation findings and write confirmations.
    """
    from agents.reconciler import get_reconciler_config

    config = get_reconciler_config(
        policies=_reconciler_policies,
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as reconciler:
        response = await reconciler.chat(
            f"Reconcile the following transaction records against the extracted "
            f"invoice data. For each transaction-invoice pair:\n"
            f"  - Match by vendor_id and invoice_num\n"
            f"  - Compare transaction amount vs invoice total_amount (tolerance: $0.01)\n"
            f"  - Verify tax_rate matches\n"
            f"  - Check currency consistency\n"
            f"  - Classify as MATCHED, DISCREPANCY, or UNMATCHED\n"
            f"  - If discrepancy exceeds $1,000, set status to ESCALATED\n\n"
            f"For EACH reconciled pair, call write_audit_result() with "
            f"execution_id='{execution_id}'.\n\n"
            f"TRANSACTIONS:\n{transactions_json}\n\n"
            f"INVOICES:\n{invoices_json}\n\n"
            f"After writing all results, produce a summary of your findings."
        )
        return await response.text()


DELEGATION_TOOLS = [
    delegate_to_data_researcher,
    delegate_to_invoice_analyzer,
    delegate_to_reconciler,
]
