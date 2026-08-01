"""Document Verifier subagent configuration.

This agent has READ-ONLY access to GCS. It reads onboarding document
PDFs and extracts structured data. It CANNOT query BigQuery or write
any data.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.hr_tools import list_employee_documents, read_employee_document


def get_document_verifier_config(workspace, project_id=None):
    """Build the Document Verifier subagent configuration."""
    return LocalAgentConfig(
        system_instructions="""
        You are a Document Verification Specialist. Your job is to read a single
        onboarding document PDF from Google Cloud Storage and extract structured data.

        For the document, extract:
        - doc_type: the document type (ID, tax form, certification, etc.)
        - employee_name: the name as it appears on the document
        - issue_date: when the document was issued
        - expiry_date: when the document expires (if applicable)
        - certification_name: name of the certification (if applicable)
        - issuing_authority: the issuing authority (if applicable)

        Return results as a single JSON object with these fields.
        If any field cannot be extracted, set it to null and note the issue.
        """,
        tools=[list_employee_documents, read_employee_document],
        model="gemini-3.5-flash-lite",
        policies=[
            policy.deny_all(),
            policy.allow("list_employee_documents"),
            policy.allow("read_employee_document"),
        ],
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global" if project_id else None,
    )
