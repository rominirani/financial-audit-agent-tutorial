from google.antigravity.hooks import policy

def compliance_officer_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions with a rich context box."""
    import tools.delegation_tools as dt
    
    # Calculate claims count and data ready status from state
    claims_count = len(dt._document_results)
    data_ready = bool(dt._research_results and dt._document_results)
    
    print("\n" + "═" * 60)
    print("🚨 COMPLIANCE OFFICER APPROVAL REQUIRED 🚨".center(60))
    print("═" * 60)
    print(f"Action Requested: {tool_call.name}")
    print(f"Execution ID:     {tool_call.args.get('execution_id', 'Unknown')}")
    print(f"Claims Processed: {claims_count}")
    print(f"Data Ready:       {'✅ Yes' if data_ready else '❌ No'}")
    print("═" * 60)
    
    response = input("\nCompliance Officer, approve this adjudication run? (y/n): ")
    return response.lower() == 'y'

# --- Development: full permissions, no restrictions ---
DEVELOPMENT_POLICIES = [
    policy.allow_all(),
]

# --- Staging: allow delegation, but require human approval before adjudicating ---
STAGING_POLICIES = [
    policy.deny_all(),
    policy.allow("delegate_to_claims_researcher"),
    policy.allow("delegate_to_document_analyzer"),
    policy.ask_user("delegate_to_adjudicator", handler=compliance_officer_approval_handler),
]

# --- Production: fully autonomous, no human prompts (defense-in-depth in adjudicator) ---
PRODUCTION_POLICIES = [
    policy.allow_all(),
]

VALID_STATUSES = {"APPROVED", "DENIED", "ESCALATED", "FLAGGED"}

ADJUDICATOR_WRITE_POLICY = [
    policy.allow("write_adjudication_result",
                 when=lambda args: args.get("status", "") in VALID_STATUSES,
                 name="allow_valid_adjudication_writes"),
]
