from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy
from tools.insurance_tools import query_pending_claims, get_policy_details

def get_researcher_config(workspace, project_id=None):
    return LocalAgentConfig(
        system_instructions="""
        You are the Claims Researcher. Query pending claims, then get policy details for each.
        Summarize the data and list the claim IDs.
        """,
        tools=[query_pending_claims, get_policy_details],
        policies=[
            policy.deny_all(),
            policy.allow("query_pending_claims"),
            policy.allow("get_policy_details"),
        ],
        model="gemini-3.5-flash-lite",
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global",
    )
