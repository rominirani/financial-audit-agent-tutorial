"""Compliance Checker subagent configuration.

This is the ONLY subagent with write access to BigQuery. It receives
hire and document data from the orchestrator, cross-references them,
and writes results via write_compliance_result(). Write access is governed
by a hardcoded status validation policy (defense in depth) PLUS any
mode-dependent policies passed from the orchestrator tier.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.hr_tools import write_compliance_result

# Defense in depth: only allow writes with valid status values.
VALID_STATUSES = {"COMPLIANT", "NON_COMPLIANT", "ESCALATED", "PENDING_REVIEW"}

CHECKER_WRITE_POLICY = policy.allow(
    "write_compliance_result",
    when=lambda args: args.get("status", "") in VALID_STATUSES,
    name="allow_valid_compliance_writes",
)


def get_compliance_checker_config(policies, workspace, project_id=None):
    """Build the Compliance Checker subagent configuration.

    Args:
        policies: Mode-dependent policy list from the orchestrator tier.
        workspace: Absolute path to the project workspace.
        project_id: GCP project ID for Vertex AI.
    """
    # Combine mode policies with the hardcoded write validation.
    checker_policies = list(policies) + [CHECKER_WRITE_POLICY]

    return LocalAgentConfig(
        system_instructions="""
        You are a Compliance Verification Engine. You receive two datasets:
        1. New hire records and department requirements from BigQuery (provided in the prompt)
        2. Document data extracted from onboarding PDFs (provided in the prompt)

        For each new hire:
        - Cross-reference submitted documents against department requirements
        - Check that all mandatory documents are present
        - Verify expiry dates are in the future (not expired)
        - Compare employee name on documents against HR record
        - Identify any missing, expired, or mismatched documents

        Classify each hire as:
        - COMPLIANT: all required documents present and valid
        - NON_COMPLIANT: missing or expired documents found
        - ESCALATED: name mismatch or critical security document missing
        - PENDING_REVIEW: minor issues requiring HR manager attention

        For EACH employee, call write_compliance_result() with:
        - execution_id (provided in the prompt)
        - emp_id, department
        - status (COMPLIANT/NON_COMPLIANT/ESCALATED/PENDING_REVIEW)
        - missing_documents, expired_documents
        - compliance_notes (rationale for the classification)
        - reviewed_by (always "compliance-checker")

        After writing all results, produce a summary of your findings.
        """,
        tools=[write_compliance_result],
        model="gemini-3.6-flash",
        policies=checker_policies,
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global" if project_id else None,
    )
