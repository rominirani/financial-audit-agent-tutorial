"""HR Data Researcher subagent configuration.

This agent has READ-ONLY access to BigQuery. It queries
pending new hires and department requirements. It CANNOT write
compliance results or modify any data.
"""
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.hr_tools import query_pending_hires, get_department_requirements


def get_hr_researcher_config(workspace, project_id=None):
    """Build the HR Researcher subagent configuration."""
    return LocalAgentConfig(
        system_instructions="""
        You are an HR Data Research Specialist. Your job is to:
        1. Query BigQuery for PENDING new hire records
        2. Query department-specific document requirements for each hire's department

        You have READ-ONLY access. You CANNOT write compliance results or modify data.

        Return your results as structured JSON with sections:
        {
            "hires": [
                {"emp_id": "...", "name": "...", "role": "...", "department": "...", "start_date": "..."},
                ...
            ],
            "requirements": {
                "Engineering": [{"doc_type": "...", "mandatory": true}, ...],
                ...
            },
            "documents_to_verify": [
                "EMP-xxxx/doc_type.pdf",
                ...
            ]
        }
        """,
        tools=[query_pending_hires, get_department_requirements],
        model="gemini-3.5-flash-lite",
        policies=[
            policy.deny_all(),
            policy.allow("query_pending_hires"),
            policy.allow("get_department_requirements"),
        ],
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global" if project_id else None,
    )
