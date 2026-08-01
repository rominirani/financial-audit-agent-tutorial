from google.antigravity import LocalAgentConfig
from tools.insurance_tools import write_adjudication_result

VALID_STATUSES = {'APPROVED', 'DENIED', 'ESCALATED', 'FLAGGED'}

def get_adjudicator_config(write_policies, workspace, project_id=None):
    from google.antigravity.hooks import policy
    
    # Internal baseline policies + injected write policy
    policies = [
        policy.deny_all(),
    ] + write_policies
    
    return LocalAgentConfig(
        system_instructions=f"""
        You are the Adjudication Engine. You will receive researched claim data and extracted document info.
        You must:
        1. Validate claims against rules (max_coverage, deductible, exclusions).
        2. Check for fraud indicators.
        3. Determine status ({', '.join(VALID_STATUSES)}).
        4. Call write_adjudication_result for each claim.
        """,
        tools=[write_adjudication_result],
        policies=policies,
        model="gemini-3.6-flash",
        workspaces=[workspace],
        vertex=True if project_id else None,
        project=project_id,
        location="global",
    )
