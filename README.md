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

# 3. Generate sample invoice PDFs
python scripts/generate_sample_invoices.py

# 4. Provision GCP infrastructure (see tutorial for full details)
#    - Create BigQuery dataset and tables
#    - Create GCS bucket and upload invoices
#    - Create service account with least-privilege IAM
gsutil mb -l us-central1 gs://$PROJECT_ID-audit-invoices
gsutil -m cp data/invoices/*.pdf gs://$PROJECT_ID-audit-invoices/Q3/

# 5. Run the audit
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
