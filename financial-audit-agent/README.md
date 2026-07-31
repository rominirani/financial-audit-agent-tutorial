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
# 1. Set up virtual environment
python -m venv .venv && source .venv/bin/activate
pip install google-antigravity google-cloud-bigquery google-cloud-storage reportlab PyPDF2

# 2. Configure your project
export PROJECT_ID="your-gcp-project-id"
# Edit tools/bigquery_tools.py and set PROJECT_ID

# 3. Provision GCP infrastructure (see tutorial for details)
# Create BigQuery dataset, tables, GCS bucket, and service account

# 4. Generate and upload sample invoices
python scripts/generate_sample_invoices.py
gsutil -m cp data/invoices/*.pdf gs://$PROJECT_ID-audit-invoices/Q3/

# 5. Run the audit
python main.py --mode=dev --quarter=Q3 --project-id=$PROJECT_ID
```

## Deployment Modes

| Mode | Policies | Use Case |
|:---|:---|:---|
| `--mode=dev` | `allow_all()` | Local debugging |
| `--mode=staging` | Human-in-the-loop for writes | Pre-production testing |
| `--mode=prod` | Deny-by-default + surgical allowlists | Production deployment |

## Observability

Install optional dependencies for production observability:
```bash
pip install google-cloud-logging opentelemetry-api opentelemetry-sdk opentelemetry-exporter-gcp-trace
```

## Tutorial

For the complete step-by-step tutorial, see the [companion article](../tutorial_financial_audit_agent.md).

## License

Apache 2.0
