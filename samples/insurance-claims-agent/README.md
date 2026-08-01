# Insurance Claims Processing Agent

An automated multi-agent claims adjudication system built with the [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) and Google Cloud Platform. This sample demonstrates the **delegation architecture** pattern from the [Financial Audit Agent](../../) applied to insurance claims processing.

## Architecture

The Orchestrator has **zero direct data tools** — it delegates to specialist subagents via wrapper functions:

- **Orchestrator** (`gemini-3.6-flash`) — Coordinates the 4-phase workflow via delegation tools only
- **Claims Researcher** (`gemini-3.5-flash-lite`) — Queries BigQuery for pending claims and policy coverage rules (read-only)
- **Document Analyzer** (`gemini-3.5-flash-lite`) — Reads and extracts structured data from claim PDF documents in GCS (read-only)
- **Adjudication Engine** (`gemini-3.6-flash`) — Reviews accumulated data, determines claim outcomes, writes results to BigQuery (write access, policy-gated)

All agents use `location='global'`.

### Key Patterns

- **State Accumulation**: Delegation tools store full results in module-level globals; orchestrator receives truncated summaries
- **Guardrails**: Adjudication Engine delegation is blocked until research and document analysis are complete
- **Defense-in-Depth**: Write tool validates status against `VALID_STATUSES = {'APPROVED', 'DENIED', 'ESCALATED', 'FLAGGED'}`
- **Policy Tiers**: Dev (allow all), Staging (human approval before adjudication), Prod (fully autonomous)

## Prerequisites

- Python 3.11+
- A Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Vertex AI API enabled

## Quick Start

```bash
# 1. Clone and navigate to this sample
git clone https://github.com/rominirani/financial-audit-agent-tutorial.git
cd financial-audit-agent-tutorial/samples/insurance-claims-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure your project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable bigquery.googleapis.com storage.googleapis.com \
  logging.googleapis.com cloudtrace.googleapis.com aiplatform.googleapis.com

# 4. Create BigQuery dataset and tables
bq mk --dataset $PROJECT_ID:insurance_claims

bq mk --table $PROJECT_ID:insurance_claims.claims \
  claim_id:STRING,claimant_name:STRING,policy_number:STRING,claim_type:STRING,amount:FLOAT64,date_filed:DATE,incident_date:DATE,status:STRING

bq mk --table $PROJECT_ID:insurance_claims.policies \
  policy_number:STRING,coverage_type:STRING,max_coverage:FLOAT64,deductible:FLOAT64,exclusions:STRING

bq mk --table $PROJECT_ID:insurance_claims.adjudication_results \
  execution_id:STRING,claim_id:STRING,policy_number:STRING,claimed_amount:FLOAT64,approved_amount:FLOAT64,status:STRING,adjudication_notes:STRING,reviewed_by:STRING,timestamp:TIMESTAMP

# 5. Populate sample claims data
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.insurance_claims.claims`
(claim_id, claimant_name, policy_number, claim_type, amount, date_filed, incident_date, status) VALUES
("CLM-4821", "Alice Smith", "POL-AUTO-100", "Auto", 45000.00, "2026-08-01", "2026-07-28", "PENDING"),
("CLM-1133", "Bob Johnson", "POL-MED-200", "Medical", 2300.00, "2026-07-20", "2026-07-18", "PENDING"),
("CLM-7744", "Charlie Brown", "POL-PROP-300", "Property", 5000.00, "2026-08-10", "2026-08-15", "PENDING"),
("CLM-9902", "Diana Prince", "POL-MED-200", "Medical", 1500.00, "2026-07-25", "2026-07-22", "PENDING")'

# 6. Populate sample policy data
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.insurance_claims.policies`
(policy_number, coverage_type, max_coverage, deductible, exclusions) VALUES
("POL-AUTO-100", "Auto", 25000.00, 500.00, "Racing, intentional damage"),
("POL-MED-200", "Medical", 100000.00, 250.00, "Cosmetic procedures"),
("POL-PROP-300", "Property", 50000.00, 1000.00, "Flood, earthquake")'

# 7. Generate sample claim document PDFs
python scripts/generate_sample_documents.py

# 8. Create GCS bucket and upload documents
gsutil mb -l us-central1 gs://$PROJECT_ID-claims-documents
gsutil -m cp -r data/documents/* gs://$PROJECT_ID-claims-documents/claims/

# 9. Run the agent
python main.py --mode=dev --project-id=$PROJECT_ID
```

## Running the Agent

```bash
# Development — full permissions, good for debugging
python main.py --mode=dev --project-id=$PROJECT_ID

# Staging — agent pauses for Compliance Officer approval before adjudication
python main.py --mode=staging --project-id=$PROJECT_ID

# Production — fully autonomous
python main.py --mode=prod --project-id=$PROJECT_ID
```

## Evaluations

```bash
python eval/run_eval.py --project-id=$PROJECT_ID
```

## Cloud Run Deployment

```bash
# Deploy
gcloud run deploy insurance-claims-agent \
  --source . \
  --region us-central1 \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --timeout 300 \
  --memory 1Gi \
  --no-allow-unauthenticated

# Invoke
SERVICE_URL=$(gcloud run services describe insurance-claims-agent \
  --region us-central1 --format 'value(status.url)')

curl -X POST "$SERVICE_URL/process" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{}'
```
