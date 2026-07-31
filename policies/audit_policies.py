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
    policy.allow("view_file"),
    policy.allow("list_dir"),
    policy.allow("grep_search"),
    policy.allow("bigquery_query"),
    policy.ask_user("run_command", handler=compliance_officer_approval_handler),
]

PRODUCTION_POLICIES = [
    policy.deny_all(),
    policy.allow("view_file"),
    policy.allow("list_dir"),
    policy.allow("grep_search"),
    policy.allow("bigquery_query",
                 when=lambda args: args.get("Query", "").strip().upper().startswith("SELECT"),
                 name="allow_bq_select_only"),
    policy.deny("run_command",
                when=lambda args: any(cmd in args.get("CommandLine", "") for cmd in ["rm", "DROP", "DELETE", "kubectl"]),
                name="deny_destructive_commands"),
    policy.ask_user("write_to_file",
                    when=lambda args: "audit_results" in args.get("TargetFile", ""),
                    handler=compliance_officer_approval_handler),
]
