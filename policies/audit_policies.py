from google.antigravity.hooks import policy

async def compliance_officer_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions.

    Receives a types.ToolCall object. Use tool_call.name for the tool name
    and tool_call.args for the arguments dict.
    """
    print(f"\n🚨 ESCALATION REQUIRED 🚨")
    print(f"Action requested: {tool_call.name}")
    print(f"Arguments: {tool_call.args}")

    # In a real environment, this would ping Slack/Email and wait.
    # For this tutorial, we simulate a prompt.
    response = input("Compliance Officer, approve this action? (y/n): ")
    return response.lower() == 'y'

DEVELOPMENT_POLICIES = [
    policy.allow_all(),
]

STAGING_POLICIES = [
    policy.deny_all(),
    # Read-only tools — allowed without approval
    policy.allow("query_vendor_transactions"),
    policy.allow("list_invoices_in_gcs"),
    policy.allow("read_invoice_from_gcs"),
    # Write tools — require human approval
    policy.ask_user("write_audit_result", handler=compliance_officer_approval_handler),
]

PRODUCTION_POLICIES = [
    policy.deny_all(),
    # Read-only tools — allowed without approval
    policy.allow("query_vendor_transactions"),
    policy.allow("list_invoices_in_gcs"),
    policy.allow("read_invoice_from_gcs"),
    # Write tools — require approval and only for recording audit findings
    policy.ask_user("write_audit_result", handler=compliance_officer_approval_handler),
]
