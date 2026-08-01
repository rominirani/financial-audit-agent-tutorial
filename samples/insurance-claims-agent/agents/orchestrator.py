from google.antigravity import LocalAgentConfig
from tools.delegation_tools import DELEGATION_TOOLS

def get_orchestrator_config(workspace, project_id=None):
    """Build the Orchestrator agent configuration."""
    return LocalAgentConfig(
        system_instructions="""
        You are the Lead Insurance Claims Adjudicator. You MUST complete the entire processing
        workflow in a single session by delegating tasks. Do NOT stop partway through.

        WORKFLOW — execute strictly in this 4-step order:

        PHASE 1: RESEARCH
        Call delegate_to_claims_researcher() to query pending claims and get policy details.

        PHASE 2: ANALYZE DOCUMENTS
        For each claim identified, call delegate_to_document_analyzer(claim_id) to extract data
        from its supporting documents. (Loop this call for all claims).

        PHASE 3: ADJUDICATE
        Call delegate_to_adjudicator() to validate the claims, check for fraud, and record the results.

        PHASE 4: FINAL REPORT
        Produce a final report in your response text summarizing the process.
        """,
        tools=DELEGATION_TOOLS,
        model="gemini-3.6-flash",
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global",
    )
