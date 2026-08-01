"""Delegation tools for the HR Onboarding Compliance Agent Team.

These tools wrap subagent execution so the Orchestrator can delegate
to specialist agents without having direct access to data tools.

Architecture:
  Orchestrator (has ONLY these delegation tools)
    ├── delegate_to_hr_researcher()         → spawns read-only BigQuery agent
    ├── delegate_to_document_verifier()     → spawns read-only PDF extraction agent
    └── delegate_to_compliance_checker()    → spawns write-enabled compliance agent

The module accumulates FULL results from each delegation call so the
Compliance Checker can access all prior data. However, it returns CONCISE
summaries to the Orchestrator to keep its context window manageable.
"""
from google.antigravity import Agent

# Module-level config — set by main.py before the orchestrator starts
_project_id = None
_workspace = None
_checker_policies = None

# Accumulated FULL results from prior delegation calls.
_research_results = None
_document_results = []
_expected_document_paths = []


def configure(project_id: str, workspace: str, checker_policies: list):
    """Initialize delegation config. Called once from main.py before agent starts.

    Args:
        project_id: GCP project ID for Vertex AI routing.
        workspace: Absolute path to the project workspace directory.
        checker_policies: Mode-dependent policy list (dev/staging/prod).
    """
    global _project_id, _workspace, _checker_policies
    global _research_results, _document_results, _expected_document_paths
    _project_id = project_id
    _workspace = workspace
    _checker_policies = checker_policies
    # Reset accumulated results for each new run
    _research_results = None
    _document_results = []
    _expected_document_paths = []


def _truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to keep orchestrator context manageable."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated — full data ({len(text)} chars) saved for compliance checker]"


async def delegate_to_hr_researcher() -> str:
    """Delegate to the HR Data Researcher subagent to query BigQuery for
    pending new hires and department-specific document requirements.

    The HR Researcher has READ-ONLY access to BigQuery.
    It cannot write compliance results or modify any data.

    Returns:
        Summary of pending hires and their document requirements.
    """
    global _research_results
    from agents.hr_researcher import get_hr_researcher_config

    config = get_hr_researcher_config(
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as researcher:
        response = await researcher.chat(
            "Query all PENDING new hires from BigQuery. For each hire, also query "
            "the department requirements to determine which documents they need. "
            "Return the complete results as structured JSON."
        )
        result = await response.text()
        # Store full result for the compliance checker
        _research_results = result
        # Extract document paths from the result for the guardrail
        import re
        _expected_document_paths.clear()
        for match in re.findall(r'(EMP-[\w-]+/[\w_]+\.pdf)', result):
            if match not in _expected_document_paths:
                _expected_document_paths.append(match)
        # Return concise summary
        doc_list = ', '.join(_expected_document_paths) if _expected_document_paths else 'none found'
        return (
            f"✅ HR Research complete. Found {len(_expected_document_paths)} documents "
            f"to verify: [{doc_list}]. "
            f"You MUST call delegate_to_document_verifier() for each one before checking compliance."
        )


async def delegate_to_document_verifier(document_path: str) -> str:
    """Delegate to the Document Verifier subagent to read and extract
    structured data from a single onboarding document PDF in GCS.

    The Document Verifier has READ-ONLY access to GCS.
    It cannot query BigQuery or write any data.

    Args:
        document_path: Path to the document in GCS (e.g., "EMP-2847/ID.pdf").

    Returns:
        Summary of extracted document fields.
    """
    from agents.document_verifier import get_document_verifier_config

    config = get_document_verifier_config(
        workspace=_workspace,
        project_id=_project_id,
    )

    async with Agent(config) as verifier:
        response = await verifier.chat(
            f"Read the onboarding document at path '{document_path}' from the GCS bucket. "
            f"Extract all structured fields: document type, employee name, issue date, "
            f"expiry date, certification name, and issuing authority. "
            f"Return the extracted data as a JSON object."
        )
        result = await response.text()
        # Store full result for the compliance checker
        _document_results.append(result)
        # Return concise summary with progress tracking
        return f"✅ Document '{document_path}' verified ({len(_document_results)} total so far). {_truncate(result)}"


async def delegate_to_compliance_checker(execution_id: str = "ONBOARDING-RUN") -> str:
    """Delegate to the Compliance Checker subagent to cross-reference documents
    against department requirements and write compliance results to BigQuery.

    The Compliance Checker automatically receives all hire data and document data
    collected by prior delegation calls. You do NOT need to pass the data —
    it is injected from the accumulated results.

    The Compliance Checker is the ONLY subagent with write access to BigQuery
    (subject to the current policy tier: dev/staging/prod).

    Args:
        execution_id: Unique ID for this compliance run (default: "ONBOARDING-RUN").

    Returns:
        Text report with compliance findings and write confirmations.
    """
    # GUARDRAIL: Refuse to check compliance if not all documents have been verified
    if _expected_document_paths:
        verified_count = len(_document_results)
        expected_count = len(_expected_document_paths)
        if verified_count < expected_count:
            return (
                f"❌ BLOCKED: Only {verified_count} of {expected_count} documents have been "
                f"verified. You must call delegate_to_document_verifier() for ALL documents "
                f"before checking compliance. Verify the remaining "
                f"{expected_count - verified_count} document(s) first, then call "
                f"delegate_to_compliance_checker() again."
            )

    from agents.compliance_checker import get_compliance_checker_config

    config = get_compliance_checker_config(
        policies=_checker_policies,
        workspace=_workspace,
        project_id=_project_id,
    )

    # Build the combined data payload from accumulated FULL results
    documents_combined = "\n---\n".join(_document_results) if _document_results else "No documents verified."

    async with Agent(config) as checker:
        response = await checker.chat(
            f"Cross-reference the following new hire records and department requirements "
            f"against the extracted document data. For each employee:\n"
            f"  - Verify all mandatory documents are present\n"
            f"  - Check expiry dates to ensure no document is expired\n"
            f"  - Verify the name on the document matches the HR record\n"
            f"  - Classify as COMPLIANT, NON_COMPLIANT, ESCALATED, or PENDING_REVIEW\n\n"
            f"For EACH employee, call write_compliance_result() with "
            f"execution_id='{execution_id}'.\n\n"
            f"HIRE RECORDS & REQUIREMENTS:\n{_research_results}\n\n"
            f"DOCUMENTS:\n{documents_combined}\n\n"
            f"After writing all results, produce a summary of your findings."
        )
        return await response.text()


DELEGATION_TOOLS = [
    delegate_to_hr_researcher,
    delegate_to_document_verifier,
    delegate_to_compliance_checker,
]
