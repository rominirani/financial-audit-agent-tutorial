"""
Financial Audit Agent — End-to-End Validation Script

Approach: Do the data fetching + reconciliation in Python, then hand
the structured findings to the Antigravity agent to analyze, write
audit results to BigQuery, and produce the final compliance report.
"""
import asyncio
import json
import os
from google.cloud import bigquery
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from hooks.observability import AUDIT_HOOKS

PROJECT_ID = "gcp-experiments-349209"
DATASET = "financial_audit"


def fetch_and_reconcile():
    """Fetch transactions + invoices from BigQuery and reconcile locally."""
    client = bigquery.Client(project=PROJECT_ID)

    # Fetch transactions
    txn_rows = client.query(f"""
        SELECT vendor_id, vendor_name, invoice_num, amount, currency, tax_rate
        FROM `{PROJECT_ID}.{DATASET}.vendor_transactions`
        WHERE status = 'PENDING' AND quarter = 'Q3'
        ORDER BY vendor_id, invoice_num
    """).result()
    transactions = [dict(r) for r in txn_rows]

    # Fetch invoices
    inv_rows = client.query(f"""
        SELECT vendor_id, vendor_name, invoice_num, invoice_amount, tax_amount, currency
        FROM `{PROJECT_ID}.{DATASET}.vendor_invoices`
        ORDER BY vendor_id, invoice_num
    """).result()
    invoices = {(r["vendor_id"], r["invoice_num"]): dict(r) for r in inv_rows}

    # Reconcile
    findings = []
    for txn in transactions:
        key = (txn["vendor_id"], txn["invoice_num"])
        inv = invoices.get(key)

        if not inv:
            findings.append({
                "vendor_id": txn["vendor_id"],
                "vendor_name": txn["vendor_name"],
                "invoice_num": txn["invoice_num"],
                "txn_amount": txn["amount"],
                "inv_amount": None,
                "discrepancy": txn["amount"],
                "status": "UNMATCHED",
                "reason": "No matching invoice found in vendor_invoices table",
            })
        elif txn["currency"] != inv["currency"]:
            findings.append({
                "vendor_id": txn["vendor_id"],
                "vendor_name": txn["vendor_name"],
                "invoice_num": txn["invoice_num"],
                "txn_amount": txn["amount"],
                "txn_currency": txn["currency"],
                "inv_amount": inv["invoice_amount"],
                "inv_currency": inv["currency"],
                "discrepancy": 0,
                "status": "DISCREPANCY",
                "reason": f"Currency mismatch: transaction={txn['currency']}, invoice={inv['currency']}",
            })
        elif abs(txn["amount"] - inv["invoice_amount"]) > 0.01:
            diff = txn["amount"] - inv["invoice_amount"]
            findings.append({
                "vendor_id": txn["vendor_id"],
                "vendor_name": txn["vendor_name"],
                "invoice_num": txn["invoice_num"],
                "txn_amount": txn["amount"],
                "inv_amount": inv["invoice_amount"],
                "discrepancy": round(diff, 2),
                "status": "DISCREPANCY",
                "reason": f"Amount mismatch: transaction=${txn['amount']:,.2f} vs invoice=${inv['invoice_amount']:,.2f} (diff=${diff:,.2f})",
            })
        else:
            findings.append({
                "vendor_id": txn["vendor_id"],
                "vendor_name": txn["vendor_name"],
                "invoice_num": txn["invoice_num"],
                "txn_amount": txn["amount"],
                "inv_amount": inv["invoice_amount"],
                "discrepancy": 0,
                "status": "MATCHED",
                "reason": "Amounts and currencies match",
            })

    # Check for duplicate invoice numbers
    seen_invoices = {}
    for txn in transactions:
        key = txn["invoice_num"]
        if key in seen_invoices:
            prev = seen_invoices[key]
            if prev["amount"] != txn["amount"]:
                # Mark the second occurrence
                for f in findings:
                    if f["vendor_id"] == txn["vendor_id"] and f["invoice_num"] == key and f["status"] == "MATCHED":
                        f["status"] = "DISCREPANCY"
                        f["reason"] = (
                            f"Duplicate invoice number {key}: "
                            f"first amount=${prev['amount']:,.2f}, second amount=${txn['amount']:,.2f}"
                        )
                        f["discrepancy"] = round(txn["amount"] - prev["amount"], 2)
        else:
            seen_invoices[key] = txn

    return transactions, findings


def write_results_to_bigquery(findings):
    """Write all audit results to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET}.audit_results"
    from datetime import datetime, UTC

    rows = []
    for f in findings:
        rows.append({
            "execution_id": "AUDIT-Q3-2026-LIVE-001",
            "vendor_id": f["vendor_id"],
            "invoice_num": f["invoice_num"],
            "transaction_amount": f["txn_amount"],
            "invoice_amount": f.get("inv_amount") or 0.0,
            "discrepancy_amount": f["discrepancy"],
            "status": f["status"],
            "agent_notes": f["reason"],
            "reviewed_by": "antigravity-agent",
            "timestamp": datetime.now(UTC).isoformat(),
        })

    errors = client.insert_rows_json(table_ref, rows)
    return errors


async def main():
    print("=" * 60)
    print("🔍 FINANCIAL AUDIT — LIVE VALIDATION")
    print("=" * 60)

    # Phase 1: Fetch and reconcile
    print("\n📊 Phase 1: Fetching data from BigQuery...")
    transactions, findings = fetch_and_reconcile()

    matched = sum(1 for f in findings if f["status"] == "MATCHED")
    discrepancies = [f for f in findings if f["status"] == "DISCREPANCY"]
    unmatched = [f for f in findings if f["status"] == "UNMATCHED"]

    print(f"   Transactions: {len(transactions)}")
    print(f"   Matched:      {matched}")
    print(f"   Discrepancies: {len(discrepancies)}")
    print(f"   Unmatched:    {len(unmatched)}")

    # Phase 2: Write results to BigQuery
    print("\n📝 Phase 2: Writing audit results to BigQuery...")
    errors = write_results_to_bigquery(findings)
    if errors:
        print(f"   ❌ Errors: {errors}")
    else:
        print(f"   ✅ {len(findings)} audit results written successfully")

    # Phase 3: Agent analysis
    print("\n🤖 Phase 3: Agent analysis and compliance report...")

    findings_json = json.dumps(findings, indent=2)

    config = LocalAgentConfig(
        system_instructions="""You are a Senior Financial Compliance Analyst.
        You will receive the results of an automated Q3 vendor invoice reconciliation.
        Analyze the findings and produce a formal compliance report with:
        1. Executive Summary
        2. Detailed findings table
        3. Risk assessment for each discrepancy
        4. Recommended actions
        5. Escalation requirements (any discrepancy over $1,000 must be escalated)
        """,
        model="gemini-2.5-flash",
        policies=[policy.allow_all()],
        hooks=AUDIT_HOOKS,
        vertex=True,
        project=PROJECT_ID,
        location="us-central1",
    )

    async with Agent(config) as agent:
        response = await agent.chat(
            f"Here are the reconciliation findings from Q3 vendor invoice audit. "
            f"There are {len(findings)} total findings: {matched} matched, "
            f"{len(discrepancies)} discrepancies, {len(unmatched)} unmatched.\n\n"
            f"FINDINGS:\n{findings_json}\n\n"
            f"Produce a formal compliance report as text output. "
            f"Do NOT create any files. Write the full report directly in your response."
        )

        report = await response.text()

        print("\n" + "=" * 60)
        print("📋 COMPLIANCE REPORT")
        print("=" * 60)
        print(report)

        usage = agent.conversation.total_usage
        print(f"\n💰 Token Usage:")
        print(f"   Prompt:   {usage.prompt_token_count}")
        print(f"   Output:   {usage.candidates_token_count}")
        print(f"   Thinking: {usage.thoughts_token_count}")
        print(f"   Total:    {usage.total_token_count}")

    # Phase 4: Verify results in BigQuery
    print("\n🔎 Phase 4: Verification — querying audit_results from BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)
    verify = client.query(f"""
        SELECT status, COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET}.audit_results`
        WHERE execution_id = 'AUDIT-Q3-2026-LIVE-001'
        GROUP BY status
    """).result()
    for row in verify:
        print(f"   {row['status']}: {row['count']}")

    print("\n✅ AUDIT COMPLETE")

    # Flush traces and logs
    try:
        from hooks.observability import CLOUD_TRACE_ENABLED
        if CLOUD_TRACE_ENABLED:
            from opentelemetry import trace as otel_trace
            provider = otel_trace.get_tracer_provider()
            if hasattr(provider, 'force_flush'):
                provider.force_flush()
            if hasattr(provider, 'shutdown'):
                provider.shutdown()
            print("📡 Cloud Trace spans flushed.")
    except Exception as e:
        print(f"⚠️  Trace flush warning: {e}")

    try:
        from hooks.observability import CLOUD_LOGGING_ENABLED, _logging_client
        if CLOUD_LOGGING_ENABLED:
            _logging_client.logging_api.transport.flush()
            print("📡 Cloud Logging flushed.")
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
