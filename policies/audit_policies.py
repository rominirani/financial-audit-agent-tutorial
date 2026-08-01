from google.antigravity.hooks import policy

VALID_STATUSES = {"MATCHED", "DISCREPANCY", "ESCALATED", "UNMATCHED"}

async def compliance_officer_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions in staging.

    Receives a types.ToolCall object. Use tool_call.name for the tool name
    and tool_call.args for the arguments dict.
    """
    # Pull accumulated context from delegation tools for a richer prompt
    try:
        import tools.delegation_tools as dt
        invoice_count = len(dt._invoice_results)
        has_research = dt._research_results is not None
    except Exception:
        invoice_count = 0
        has_research = False

    execution_id = tool_call.args.get("execution_id", "AUDIT-Q3")

    print(f"\n{'='*60}")
    print(f"🚨 COMPLIANCE OFFICER APPROVAL REQUIRED 🚨")
    print(f"{'='*60}")
    print(f"")
    print(f"  Action:       Delegate to Reconciliation Engine")
    print(f"  Execution ID: {execution_id}")
    print(f"  Data Ready:   {'✅ Transactions loaded' if has_research else '❌ No transaction data'}")
    print(f"  Invoices:     {invoice_count} PDF(s) analyzed")
    print(f"")
    print(f"  ⚠️  The Reconciler will:")
    print(f"     1. Compare transactions against invoice data")
    print(f"     2. Classify each pair (MATCHED / DISCREPANCY / ESCALATED)")
    print(f"     3. WRITE audit results to BigQuery")
    print(f"")
    print(f"{'='*60}")

    response = input("  Approve reconciliation and BigQuery writes? (y/n): ")
    print()
    return response.lower() == 'y'


# --- Development: full permissions, no restrictions ---
DEVELOPMENT_POLICIES = [
    policy.allow_all(),
]


# --- Staging: human approval required before reconciler writes to BigQuery ---
# The orchestrator only has delegation tools (no direct data access), so
# we don't need deny_all. We just gate the reconciler behind human approval.
STAGING_POLICIES = [
    policy.allow("delegate_to_data_researcher"),
    policy.allow("delegate_to_invoice_analyzer"),
    # Reconciler delegation — human must approve (triggers BigQuery writes)
    policy.ask_user("delegate_to_reconciler", handler=compliance_officer_approval_handler),
]


# --- Production: fully autonomous, no human prompts ---
# All delegation tools auto-allowed. Each subagent enforces its own
# internal policies (e.g., the reconciler validates write_audit_result status).
PRODUCTION_POLICIES = [
    policy.allow_all(),
]
