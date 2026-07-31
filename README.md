# Financial Audit Agent Team

An autonomous multi-agent financial reconciliation system built with the [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) and Google Cloud Platform.

## Overview

This project implements a team of specialized AI agents that reconcile vendor transactions (from BigQuery) against invoice PDFs (from Cloud Storage), flag discrepancies, and escalate findings above $1,000 for human review.

## Why the Google Antigravity SDK?

Building a production-grade multi-agent system from raw LLM API calls means wiring up agent lifecycle management, tool registration, inter-agent communication, policy enforcement, and observability — before writing any business logic. The [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) handles all of that:

| Capability | What the SDK Provides |
|:---|:---|
| **Agent Configuration** | `LocalAgentConfig` — declarative definitions with system instructions, tools, and sub-agent spawning |
| **Tool Registration** | Pass plain Python functions as `tools=[...]` — schemas are auto-generated from type hints and docstrings |
| **Safety Policies** | `policy.allow()`, `policy.deny()`, `policy.ask_user()` — composable rules that gate every tool call |
| **Lifecycle Hooks** | `@on_session_start`, `@post_tool_call`, `@on_session_end` — inject logging and tracing without touching agent logic |
| **Vertex AI Integration** | Native Gemini model connection via Application Default Credentials |

The key design principle is **separation of concerns**: an agent's *reasoning* (system instructions + tools) is defined independently from its *governance* (policies + hooks). You can swap from a permissive dev policy to a locked-down production policy without changing a single line of agent code.

## Architecture

- **Audit Orchestrator** — Manages the 4-phase workflow and delegates to subagents
- **Data Researcher** — Queries BigQuery for pending vendor transactions (read-only)
- **Invoice Analyzer** — Extracts structured data from PDF invoices in GCS (read-only)
- **Reconciliation Engine** — Compares datasets and flags mismatches
- **Human Compliance Gate** — Pauses execution for manual review of high-value discrepancies

## Prerequisites

- Python 3.11+
- A Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Vertex AI API enabled

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/rominirani/financial-audit-agent-tutorial.git
cd financial-audit-agent-tutorial
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure your project (PROJECT_ID is read from the environment, no file edits needed)
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable bigquery.googleapis.com storage.googleapis.com \
  logging.googleapis.com cloudtrace.googleapis.com aiplatform.googleapis.com

# 4. Generate sample invoice PDFs
python scripts/generate_sample_invoices.py

# 5. Create BigQuery dataset and tables
bq mk --dataset $PROJECT_ID:financial_audit

bq mk --table $PROJECT_ID:financial_audit.vendor_transactions \
  vendor_id:STRING,vendor_name:STRING,invoice_num:STRING,amount:FLOAT64,currency:STRING,tax_rate:FLOAT64,status:STRING,quarter:STRING,transaction_date:DATE

bq mk --table $PROJECT_ID:financial_audit.audit_results \
  execution_id:STRING,vendor_id:STRING,invoice_num:STRING,transaction_amount:FLOAT64,invoice_amount:FLOAT64,discrepancy_amount:FLOAT64,status:STRING,agent_notes:STRING,reviewed_by:STRING,timestamp:TIMESTAMP

# 6. Populate sample transaction data
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.financial_audit.vendor_transactions`
(vendor_id, vendor_name, invoice_num, amount, currency, tax_rate, status, quarter, transaction_date) VALUES
("8492", "TechCorp Solutions", "INV-8492-Q3-001", 142300.00, "USD", 0.085, "PENDING", "Q3", "2026-07-15"),
("1022", "OfficeSupplies Co", "INV-1022-Q3-014", 4500.00, "USD", 0.05, "PENDING", "Q3", "2026-07-20"),
("3301", "Global Services Ltd", "INV-3301-Q3-099", 87500.00, "USD", 0.10, "PENDING", "Q3", "2026-08-01"),
("5567", "Consulting Group Inc", "INV-5567-Q3-001", 23400.00, "USD", 0.0, "PENDING", "Q3", "2026-08-10"),
("5567", "Consulting Group Inc", "INV-5567-Q3-001", 24100.00, "USD", 0.0, "PENDING", "Q3", "2026-08-12")'

# 7. Create GCS bucket and upload invoices
gsutil mb -l us-central1 gs://$PROJECT_ID-audit-invoices
gsutil -m cp data/invoices/*.pdf gs://$PROJECT_ID-audit-invoices/Q3/

# 8. Run the audit
python main.py --mode=dev --quarter=Q3 --project-id=$PROJECT_ID
```

## Running the Agent

The agent supports three policy tiers. Try all three to see how the SDK's policy system controls agent behavior:

```bash
# Development — full permissions, good for debugging
python main.py --mode=dev --quarter=Q3 --project-id=$PROJECT_ID

# Staging — agent pauses and prompts for human approval before writes
python main.py --mode=staging --quarter=Q3 --project-id=$PROJECT_ID

# Production — deny-by-default, destructive commands silently blocked
python main.py --mode=prod --quarter=Q3 --project-id=$PROJECT_ID
```

| Flag | Policies | Use Case |
|:---|:---|:---|
| `--mode=dev` | `allow_all()` | Debugging with full permissions |
| `--mode=staging` | Human-in-the-loop for writes | Pre-production testing |
| `--mode=prod` | Deny-by-default + surgical allowlists | Production deployment |

## Observability

Install optional dependencies for production observability:
```bash
pip install google-cloud-logging opentelemetry-api opentelemetry-sdk opentelemetry-exporter-gcp-trace
```

## Evaluations

Run the eval suite to verify the agent handles all test scenarios correctly:
```bash
python eval/run_eval.py --project-id=$PROJECT_ID
```

## Cloud Run Deployment

Deploy the agent as an HTTP service on Cloud Run:
```bash
gcloud run deploy financial-audit-agent \
  --source . \
  --region us-central1 \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --timeout 300 \
  --memory 1Gi \
  --service-account audit-agent-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated
```

Invoke the deployed agent:
```bash
SERVICE_URL=$(gcloud run services describe financial-audit-agent \
  --region us-central1 --format 'value(status.url)')

curl -X POST "$SERVICE_URL/audit" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"quarter": "Q3"}'
```

## Tutorial

For the complete step-by-step tutorial explaining every design decision, see the companion article on building this system from scratch.

## License

Apache 2.0
