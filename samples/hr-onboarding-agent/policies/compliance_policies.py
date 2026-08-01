from google.antigravity.hooks import policy

VALID_STATUSES = {"COMPLIANT", "NON_COMPLIANT", "ESCALATED", "PENDING_REVIEW"}

async def hr_manager_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions in staging.

    Receives a types.ToolCall object. Use tool_call.name for the tool name
    and tool_call.args for the arguments dict.
    """
    # Pull accumulated context from delegation tools for a richer prompt
    try:
        import tools.delegation_tools as dt
        doc_count = len(dt._document_results)
        has_research = dt._research_results is not None
    except Exception:
        doc_count = 0
        has_research = False

    execution_id = tool_call.args.get("execution_id", "ONBOARDING-RUN")

    print(f"\n{'='*60}")
    print(f"🚨 HR MANAGER APPROVAL REQUIRED 🚨")
    print(f"{'='*60}")
    print(f"")
    print(f"  Action:       Delegate to Compliance Checker")
    print(f"  Execution ID: {execution_id}")
    print(f"  Data Ready:   {'✅ Hire records loaded' if has_research else '❌ No hire data'}")
    print(f"  Documents:    {doc_count} PDF(s) verified")
    print(f"")
    print(f"  ⚠️  The Compliance Checker will:")
    print(f"     1. Cross-reference documents against requirements")
    print(f"     2. Classify each hire (COMPLIANT / NON_COMPLIANT / ESCALATED)")
    print(f"     3. WRITE compliance results to BigQuery")
    print(f"")
    print(f"{'='*60}")

    response = input("  Approve compliance check and BigQuery writes? (y/n): ")
    print()
    return response.lower() == 'y'


# --- Development: full permissions, no restrictions ---
DEVELOPMENT_POLICIES = [
    policy.allow_all(),
]


# --- Staging: human approval required before compliance checker writes to BigQuery ---
STAGING_POLICIES = [
    policy.allow("delegate_to_hr_researcher"),
    policy.allow("delegate_to_document_verifier"),
    # Compliance checker delegation — human must approve (triggers BigQuery writes)
    policy.ask_user("delegate_to_compliance_checker", handler=hr_manager_approval_handler),
]


# --- Production: fully autonomous, no human prompts ---
# All delegation tools auto-allowed. The compliance checker enforces its own
# internal policies (validates write_compliance_result status).
PRODUCTION_POLICIES = [
    policy.allow_all(),
]
