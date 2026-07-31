from google.antigravity.hooks import policy

VALID_STATUSES = {"MATCHED", "DISCREPANCY", "ESCALATED", "UNMATCHED"}

async def compliance_officer_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions in staging.

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


# --- Development: full permissions, no restrictions ---
DEVELOPMENT_POLICIES = [
    policy.allow_all(),
]


# --- Staging: reads auto-allowed, writes require human approval ---
# Use this when testing interactively. You sit at the terminal and
# approve/reject each write_audit_result call before it hits BigQuery.
STAGING_POLICIES = [
    policy.deny_all(),
    # Read-only tools — allowed without approval
    policy.allow("query_vendor_transactions"),
    policy.allow("list_invoices_in_gcs"),
    policy.allow("read_invoice_from_gcs"),
    # Write tools — human must approve each one
    policy.ask_user("write_audit_result", handler=compliance_officer_approval_handler),
]


# --- Production: fully autonomous, no human prompts ---
# Use this for unattended execution (Cloud Run, cron jobs).
# Writes are auto-allowed but ONLY if the status is valid.
# No ask_user — there's no human at the terminal in production.
PRODUCTION_POLICIES = [
    policy.deny_all(),
    # Read-only tools — allowed
    policy.allow("query_vendor_transactions"),
    policy.allow("list_invoices_in_gcs"),
    policy.allow("read_invoice_from_gcs"),
    # Write tools — auto-allowed but only with valid status values
    policy.allow("write_audit_result",
                 when=lambda args: args.get("status", "") in VALID_STATUSES,
                 name="allow_valid_audit_writes"),
]
