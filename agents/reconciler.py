"""Reconciliation Engine subagent configuration.

This is the ONLY subagent with write access to BigQuery. It receives
transaction and invoice data from the orchestrator, reconciles them,
and writes results via write_audit_result(). Write access is governed
by a hardcoded status validation policy (defense in depth) PLUS any
mode-dependent policies passed from the orchestrator tier.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.bigquery_tools import write_audit_result

# Defense in depth: only allow writes with valid status values.
# Even if the LLM hallucinates a status like "APPROVED" or "DELETE_ALL",
# this policy rejects it because it's not in VALID_STATUSES.
VALID_STATUSES = {"MATCHED", "DISCREPANCY", "ESCALATED", "UNMATCHED"}

RECONCILER_WRITE_POLICY = policy.allow(
    "write_audit_result",
    when=lambda args: args.get("status", "") in VALID_STATUSES,
    name="allow_valid_audit_writes",
)


def get_reconciler_config(policies, workspace, project_id=None):
    """Build the Reconciliation Engine subagent configuration.

    Args:
        policies: Mode-dependent policy list from the orchestrator tier.
        workspace: Absolute path to the project workspace.
        project_id: GCP project ID for Vertex AI.
    """
    # Combine mode policies with the hardcoded write validation.
    # The write validation is always active regardless of dev/staging/prod.
    reconciler_policies = list(policies) + [RECONCILER_WRITE_POLICY]

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
        model="gemini-3.6-flash",
        policies=reconciler_policies,
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global" if project_id else None,
    )

