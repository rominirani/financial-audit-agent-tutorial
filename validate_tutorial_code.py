"""
Syntax validation for all tutorial Python code blocks.
This script imports and validates the code patterns used in the tutorial.
"""

# ─── Test 1: Policy imports and API ───────────────────────────────────────
print("Test 1: Policy API...")
try:
    # Simulate the policy pattern (we test syntax, not runtime)
    code = '''
from google.antigravity.hooks import policy

async def compliance_officer_approval_handler(tool_call) -> bool:
    """Escalation handler for high-risk actions."""
    print(f"ESCALATION REQUIRED")
    print(f"Action requested: {tool_call.tool_name}")
    print(f"Arguments: {tool_call.arguments}")
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
'''
    compile(code, "audit_policies.py", "exec")
    print("  ✅ audit_policies.py syntax valid")
except SyntaxError as e:
    print(f"  ❌ Syntax error: {e}")

# ─── Test 2: Agent configs ────────────────────────────────────────────────
print("Test 2: Agent configs...")
for name, code in {
    "orchestrator.py": '''
from google.antigravity import LocalAgentConfig, CapabilitiesConfig

def get_orchestrator_config(policies, workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are the Lead Financial Auditor orchestrating a Q3 vendor reconciliation.
        """,
        capabilities=CapabilitiesConfig(enable_subagents=True),
        policies=policies,
        workspaces=[workspace],
    )
''',
    "data_researcher.py": '''
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy

def get_data_researcher_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are a Data Research Specialist. You have READ-ONLY access.
        """,
        policies=[
            policy.deny_all(),
            policy.allow("bigquery_query",
                         when=lambda args: args.get("Query", "").strip().upper().startswith("SELECT"),
                         name="allow_bq_select_only"),
        ],
        workspaces=[workspace],
    )
''',
    "invoice_analyzer.py": '''
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy

def get_invoice_analyzer_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are an Invoice Analysis Specialist.
        """,
        policies=[
            policy.deny_all(),
            policy.allow("view_file"),
            policy.allow("list_dir"),
        ],
        workspaces=[workspace],
    )
''',
    "reconciler.py": '''
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy

def get_reconciler_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are a Reconciliation Engine.
        """,
        policies=[
            policy.deny_all(),
            policy.allow("view_file"),
        ],
        workspaces=[workspace],
    )
''',
}.items():
    try:
        compile(code, name, "exec")
        print(f"  ✅ {name} syntax valid")
    except SyntaxError as e:
        print(f"  ❌ {name} syntax error: {e}")

# ─── Test 3: Observability hooks ──────────────────────────────────────────
print("Test 3: Hooks...")
try:
    code = '''
from google.antigravity.hooks import hooks
from google.antigravity import types
import json
from datetime import datetime

@hooks.on_session_start
async def audit_session_start():
    print(f"FINANCIAL AUDIT SESSION STARTED — {datetime.utcnow().isoformat()}Z")

@hooks.post_tool_call
async def audit_tool_invocation(data):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_id": str(data.agent_id) if hasattr(data, "agent_id") else "unknown",
        "tool": data.tool_name if hasattr(data, "tool_name") else str(data),
        "event": "TOOL_INVOCATION",
    }
    print(f"[AUDIT] {json.dumps(log_entry)}")

@hooks.on_session_end
async def audit_session_end():
    print(f"FINANCIAL AUDIT SESSION COMPLETED — {datetime.utcnow().isoformat()}Z")

AUDIT_HOOKS = [audit_session_start, audit_tool_invocation, audit_session_end]
'''
    compile(code, "observability.py", "exec")
    print("  ✅ observability.py syntax valid")
except SyntaxError as e:
    print(f"  ❌ Syntax error: {e}")

# ─── Test 4: Main script ─────────────────────────────────────────────────
print("Test 4: main.py...")
try:
    code = '''
import asyncio
import argparse
import os
from google.antigravity import Agent
from agents.orchestrator import get_orchestrator_config
from policies.audit_policies import DEVELOPMENT_POLICIES, STAGING_POLICIES, PRODUCTION_POLICIES
from hooks.observability import AUDIT_HOOKS

async def main():
    parser = argparse.ArgumentParser(description="Financial Audit Agent Team")
    parser.add_argument("--mode", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument("--quarter", default="Q3")
    args = parser.parse_args()
    
    policies = {"dev": DEVELOPMENT_POLICIES, "staging": STAGING_POLICIES, "prod": PRODUCTION_POLICIES}[args.mode]
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    
    config = get_orchestrator_config(
        policies=policies,
        workspace=workspace_dir
    )
    config.hooks = AUDIT_HOOKS
    
    print(f"Starting Financial Audit — Mode: {args.mode}, Quarter: {args.quarter}")
    print(f"Policies: {len(policies)} rules loaded")
    
    async with Agent(config=config) as agent:
        response = await agent.chat(
            f"Execute the Q3 vendor invoice reconciliation workflow. "
            f"Query all PENDING transactions for {args.quarter} from BigQuery, "
            f"retrieve corresponding invoice PDFs from Drive, and reconcile "
            f"each transaction. Flag any discrepancy over $1,000 for human review."
        )
        
        print(await response.text())
        
        usage = agent.conversation.total_usage
        print(f"Prompt tokens:    {usage.prompt_token_count}")
        print(f"Output tokens:    {usage.candidates_token_count}")
        print(f"Thinking tokens:  {usage.thoughts_token_count}")
        print(f"Total tokens:     {usage.total_token_count}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    compile(code, "main.py", "exec")
    print("  ✅ main.py syntax valid")
except SyntaxError as e:
    print(f"  ❌ Syntax error: {e}")

# ─── Test 5: PDF generator ───────────────────────────────────────────────
print("Test 5: generate_sample_invoices.py...")
try:
    code = '''
import os
from reportlab.pdfgen import canvas

def create_invoice(vendor_id, vendor_name, inv_num, amount, currency, tax_rate, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    c = canvas.Canvas(os.path.join(output_dir, f"{inv_num}.pdf"))
    c.drawString(100, 750, f"INVOICE: {inv_num}")
    c.drawString(100, 730, f"Vendor: {vendor_name} (ID: {vendor_id})")
    
    base_amount = amount / (1 + tax_rate)
    tax_amount = amount - base_amount
    
    c.drawString(100, 690, f"Base Amount: {base_amount:.2f} {currency}")
    c.drawString(100, 670, f"Tax Rate: {tax_rate * 100}%")
    c.drawString(100, 650, f"Tax Amount: {tax_amount:.2f} {currency}")
    c.drawString(100, 610, f"TOTAL: {amount:.2f} {currency}")
    c.save()

create_invoice("1022", "OfficeSupplies Co", "INV-1022-Q3-014", 4500.00, "USD", 0.05, "../data/invoices")
create_invoice("8492", "TechCorp", "INV-8492-Q3-001", 138750.00, "USD", 0.0625, "../data/invoices") 
create_invoice("3301", "Global Services", "INV-3301-Q3-099", 87500.00, "EUR", 0.10, "../data/invoices")
create_invoice("5567", "Consulting Group", "INV-5567-Q3-001", 23400.00, "USD", 0.0, "../data/invoices")
'''
    compile(code, "generate_sample_invoices.py", "exec")
    print("  ✅ generate_sample_invoices.py syntax valid")
except SyntaxError as e:
    print(f"  ❌ Syntax error: {e}")

print("\n✅ All syntax checks complete!")
