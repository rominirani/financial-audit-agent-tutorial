"""Reconciliation Engine subagent configuration.

This is the ONLY subagent with write access to BigQuery. It receives
transaction and invoice data from the orchestrator, reconciles them,
and writes results via write_audit_result(). Write access is governed
by the current policy tier (dev/staging/prod).
"""
from google.antigravity import LocalAgentConfig
from tools.bigquery_tools import write_audit_result


def get_reconciler_config(policies, workspace, project_id=None):
    """Build the Reconciliation Engine subagent configuration.

    Args:
        policies: Mode-dependent policy list (dev/staging/prod).
                  Controls whether write_audit_result() requires approval.
        workspace: Absolute path to the project workspace.
        project_id: GCP project ID for Vertex AI.
    """
    return LocalAgentConfig(
        system_instructions="""
        You are a Reconciliation Engine. You receive two datasets:
        1. Transaction records from BigQuery (provided in the prompt)
        2. Invoice data extracted from PDFs (provided in the prompt)

        For each transaction-invoice pair:
        - Match by vendor_id and invoice_num
        - Compare transaction amount vs invoice total_amount (tolerance: $0.01)
        - Verify tax_rate matches
        - Check currency consistency

        Classify each pair as:
        - MATCHED: amounts match within tolerance
        - DISCREPANCY: amounts differ — include the difference and likely cause
        - UNMATCHED: transaction exists but no corresponding invoice found
        - ESCALATED: discrepancy exceeds $1,000 — requires human review

        For EACH reconciled pair, call write_audit_result() with:
        - execution_id (provided in the prompt)
        - vendor_id, invoice_num
        - transaction_amount, invoice_amount
        - status (MATCHED/DISCREPANCY/UNMATCHED/ESCALATED)
        - finding_details (rationale for the classification)
        - auditor (always "reconciliation-engine")

        After writing all results, produce a summary of your findings.
        """,
        tools=[write_audit_result],
        model="gemini-2.5-flash",
        policies=policies,
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="us-central1" if project_id else None,
    )
