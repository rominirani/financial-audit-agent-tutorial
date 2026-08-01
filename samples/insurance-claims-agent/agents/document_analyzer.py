from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.insurance_tools import list_claim_documents, read_claim_document

def get_analyzer_config(workspace, project_id=None):
    return LocalAgentConfig(
        system_instructions="""
        You are the Document Analyzer. For the requested claim ID or document path,
        list the documents and read them to extract key claim data (amounts, dates, etc.).
        """,
        tools=[list_claim_documents, read_claim_document],
        policies=[
            policy.deny_all(),
            policy.allow("list_claim_documents"),
            policy.allow("read_claim_document"),
        ],
        model="gemini-3.5-flash-lite",
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global",
    )
