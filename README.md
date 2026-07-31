# Financial Audit Agent Team

An autonomous multi-agent financial reconciliation system built with the [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) and Google Cloud Platform.

## Overview

This project implements a team of specialized AI agents that reconcile vendor transactions (from BigQuery) against invoice PDFs (from Cloud Storage), flag discrepancies, and escalate findings above $1,000 for human review.

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

# 2. Configure your project
#    Open tools/bigquery_tools.py and replace YOUR_PROJECT_ID with your GCP project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 3. Generate sample invoice PDFs
python scripts/generate_sample_invoices.py

# 4. Create BigQuery dataset and tables
bq mk --dataset $PROJECT_ID:financial_audit

bq mk --table $PROJECT_ID:financial_audit.vendor_transactions \
  vendor_id:STRING,vendor_name:STRING,invoice_num:STRING,amount:FLOAT64,currency:STRING,tax_rate:FLOAT64,status:STRING,quarter:STRING,transaction_date:DATE

bq mk --table $PROJECT_ID:financial_audit.audit_results \
  execution_id:STRING,vendor_id:STRING,invoice_num:STRING,transaction_amount:FLOAT64,invoice_amount:FLOAT64,discrepancy_amount:FLOAT64,status:STRING,agent_notes:STRING,reviewed_by:STRING,timestamp:TIMESTAMP

# 5. Populate sample transaction data
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.financial_audit.vendor_transactions`
(vendor_id, vendor_name, invoice_num, amount, currency, tax_rate, status, quarter, transaction_date) VALUES
("8492", "TechCorp Solutions", "INV-8492-Q3-001", 142300.00, "USD", 0.085, "PENDING", "Q3", "2026-07-15"),
("1022", "OfficeSupplies Co", "INV-1022-Q3-014", 4500.00, "USD", 0.05, "PENDING", "Q3", "2026-07-20"),
("3301", "Global Services Ltd", "INV-3301-Q3-099", 87500.00, "USD", 0.10, "PENDING", "Q3", "2026-08-01"),
("5567", "Consulting Group Inc", "INV-5567-Q3-001", 23400.00, "USD", 0.0, "PENDING", "Q3", "2026-08-10"),
("5567", "Consulting Group Inc", "INV-5567-Q3-001", 24100.00, "USD", 0.0, "PENDING", "Q3", "2026-08-12")'

# 6. Create GCS bucket and upload invoices
gsutil mb -l us-central1 gs://$PROJECT_ID-audit-invoices
gsutil -m cp data/invoices/*.pdf gs://$PROJECT_ID-audit-invoices/Q3/

# 7. Run the audit
python main.py --mode=dev --quarter=Q3 --project-id=$PROJECT_ID
```

## Policy Tiers

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

## Tutorial

For the complete step-by-step tutorial, see the companion article on building this system from scratch.

## License

Apache 2.0
