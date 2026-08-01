"""Delegation tools for the Financial Audit Agent Team.

These tools wrap subagent execution so the Orchestrator can delegate
to specialist agents without having direct access to data tools.

Architecture:
  Orchestrator (has ONLY these delegation tools)
    ├── delegate_to_data_researcher()   → spawns read-only BigQuery/GCS agent
    ├── delegate_to_invoice_analyzer()  → spawns read-only PDF extraction agent
    └── delegate_to_reconciler()        → spawns write-enabled reconciliation agent

The module accumulates FULL results from each delegation call so the
Reconciler can access all prior data. However, it returns CONCISE summaries
to the Orchestrator to keep its context window manageable — this prevents
the "model produced invalid output" errors that occur when the context
grows too large after multiple tool calls.
"""
from google.antigravity import Agent

# Module-level config — set by main.py before the orchestrator starts
_project_id = None
_workspace = None
_reconciler_policies = None

# Accumulated FULL results from prior delegation calls.
# The reconciler reads these directly; the orchestrator only sees summaries.
_research_results = None
_invoice_results = []


def configure(project_id: str, workspace: str, reconciler_policies: list):
    """Initialize delegation config. Called once from main.py before agent starts.

    Args:
        project_id: GCP project ID for Vertex AI routing.
        workspace: Absolute path to the project workspace directory.
        reconciler_policies: Mode-dependent policy list (dev/staging/prod).
    """
    global _project_id, _workspace, _reconciler_policies
    global _research_results, _invoice_results
    _project_id = project_id
    _workspace = workspace
    _reconciler_policies = reconciler_policies
    # Reset accumulated results for each new run
    _research_results = None
    _invoice_results = []


def _truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to keep orchestrator context manageable."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated — full data ({len(text)} chars) saved for reconciler]"


async def delegate_to_data_researcher(quarter: str = "Q3") -> str:
    """Delegate to the Data Researcher subagent to query BigQuery for
    pending vendor transactions and list invoice PDFs in GCS.

    The Data Researcher has READ-ONLY access to BigQuery and GCS.
    It cannot write audit results or modify any data.

    Args:
        quarter: The fiscal quarter to query (e.g., "Q3").

    Returns:
        Summary of transaction records and invoice file listings.
    """
    global _research_results
    from agents.data_researcher import get_data_researcher_config

    config = get_data_researcher_config(
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as researcher:
        response = await researcher.chat(
            f"Query all PENDING vendor transactions for quarter '{quarter}' "
            f"from BigQuery. Also list all invoice PDF files in the GCS bucket. "
            f"Return the complete results as structured JSON."
        )
        result = await response.text()
        # Store full result for the reconciler
        _research_results = result
        # Return concise summary to the orchestrator
        return _truncate(result)


async def delegate_to_invoice_analyzer(invoice_path: str) -> str:
    """Delegate to the Invoice Analyzer subagent to read and extract
    structured data from a single invoice PDF in GCS.

    The Invoice Analyzer has READ-ONLY access to GCS.
    It cannot query BigQuery or write any data.

    Args:
        invoice_path: Path to the invoice PDF in GCS (e.g., "Q3/INV-8492-Q3-001.pdf").

    Returns:
        Summary of extracted invoice fields.
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
        result = await response.text()
        # Store full result for the reconciler
        _invoice_results.append(result)
        # Return concise summary to the orchestrator
        return _truncate(result)


async def delegate_to_reconciler(execution_id: str = "AUDIT-Q3") -> str:
    """Delegate to the Reconciliation Engine subagent to compare transactions
    against invoices, classify findings, and write audit results to BigQuery.

    The Reconciler automatically receives all transaction and invoice data
    collected by prior delegation calls. You do NOT need to pass the data —
    it is injected from the accumulated results.

    The Reconciler is the ONLY subagent with write access to BigQuery
    (subject to the current policy tier: dev/staging/prod).

    Args:
        execution_id: Unique ID for this audit run (default: "AUDIT-Q3").

    Returns:
        Text report with reconciliation findings and write confirmations.
    """
    from agents.reconciler import get_reconciler_config

    config = get_reconciler_config(
        policies=_reconciler_policies,
        workspace=_workspace,
        project_id=_project_id,
    )

    # Build the combined data payload from accumulated FULL results
    invoices_combined = "\n---\n".join(_invoice_results) if _invoice_results else "No invoices analyzed."

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
            f"TRANSACTIONS:\n{_research_results}\n\n"
            f"INVOICES:\n{invoices_combined}\n\n"
            f"After writing all results, produce a summary of your findings."
        )
        return await response.text()


DELEGATION_TOOLS = [
    delegate_to_data_researcher,
    delegate_to_invoice_analyzer,
    delegate_to_reconciler,
]
