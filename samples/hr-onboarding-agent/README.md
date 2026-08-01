# HR Onboarding Compliance Agent

An automated multi-agent onboarding compliance system built with the [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) and Google Cloud Platform. This sample demonstrates the **delegation architecture** pattern from the [Financial Audit Agent](../../) applied to HR onboarding document verification.

## Architecture

The Orchestrator has **zero direct data tools** — it delegates to specialist subagents via wrapper functions:

- **Orchestrator** (`gemini-3.6-flash`) — Coordinates the 4-phase workflow via delegation tools only
- **HR Researcher** (`gemini-3.5-flash-lite`) — Queries BigQuery for pending new hires and department-specific document requirements (read-only)
- **Document Verifier** (`gemini-3.5-flash-lite`) — Reads and extracts structured data from onboarding PDF documents in GCS (read-only)
- **Compliance Checker** (`gemini-3.6-flash`) — Cross-references documents against requirements, writes compliance results to BigQuery (write access, policy-gated)

All agents use `location='global'`.

### Key Patterns

- **State Accumulation**: Delegation tools store full results in module-level globals; orchestrator receives truncated summaries
- **Guardrails**: Compliance Checker delegation is blocked until all expected documents have been verified
- **Defense-in-Depth**: Write tool validates status against `VALID_STATUSES = {'COMPLIANT', 'NON_COMPLIANT', 'ESCALATED', 'PENDING_REVIEW'}`
- **Policy Tiers**: Dev (allow all), Staging (HR Manager approval before compliance writes), Prod (fully autonomous)

## Prerequisites

- Python 3.11+
- A Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Vertex AI API enabled

## Quick Start

```bash
# 1. Clone and navigate to this sample
git clone https://github.com/rominirani/financial-audit-agent-tutorial.git
cd financial-audit-agent-tutorial/samples/hr-onboarding-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure your project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable bigquery.googleapis.com storage.googleapis.com \
  logging.googleapis.com cloudtrace.googleapis.com aiplatform.googleapis.com

# 4. Create BigQuery dataset and tables
bq mk --dataset $PROJECT_ID:hr_onboarding

bq mk --table $PROJECT_ID:hr_onboarding.new_hires \
  emp_id:STRING,name:STRING,role:STRING,department:STRING,start_date:DATE,status:STRING

bq mk --table $PROJECT_ID:hr_onboarding.department_requirements \
  department:STRING,doc_type:STRING,description:STRING,mandatory:BOOLEAN

bq mk --table $PROJECT_ID:hr_onboarding.compliance_results \
  execution_id:STRING,emp_id:STRING,department:STRING,status:STRING,missing_documents:STRING,expired_documents:STRING,compliance_notes:STRING,reviewed_by:STRING,timestamp:TIMESTAMP

# 5. Populate sample new hires data
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.hr_onboarding.new_hires`
(emp_id, name, role, department, start_date, status) VALUES
("EMP-2847", "Jane Smith", "Software Engineer", "Engineering", "2026-09-01", "PENDING"),
("EMP-1155", "Michael Johnson", "Nurse Practitioner", "Healthcare", "2026-09-15", "PENDING"),
("EMP-4490", "Alice Williams", "Financial Analyst", "Finance", "2026-09-10", "PENDING"),
("EMP-3321", "Robert Chen", "Security Engineer", "Engineering", "2026-09-20", "PENDING")'

# 6. Populate department requirements
bq query --use_legacy_sql=false \
'INSERT INTO `'$PROJECT_ID'.hr_onboarding.department_requirements`
(department, doc_type, description, mandatory) VALUES
("Engineering", "ID", "Government-issued photo ID", true),
("Engineering", "Tax Form", "W-4 or equivalent tax form", true),
("Engineering", "Security Clearance", "Active security clearance certificate", true),
("Healthcare", "ID", "Government-issued photo ID", true),
("Healthcare", "HIPAA Certification", "Current HIPAA compliance certification", true),
("Finance", "ID", "Government-issued photo ID", true),
("Finance", "SOX Certification", "SOX compliance certification", true)'

# 7. Generate sample onboarding document PDFs
python scripts/generate_sample_documents.py

# 8. Create GCS bucket and upload documents
gsutil mb -l us-central1 gs://$PROJECT_ID-onboarding-documents
gsutil -m cp -r data/documents/* gs://$PROJECT_ID-onboarding-documents/

# 9. Run the agent
python main.py --mode=dev --project-id=$PROJECT_ID
```

## Running the Agent

```bash
# Development — full permissions, good for debugging
python main.py --mode=dev --project-id=$PROJECT_ID

# Staging — agent pauses for HR Manager approval before compliance writes
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
gcloud run deploy hr-onboarding-agent \
  --source . \
  --region us-central1 \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --timeout 300 \
  --memory 1Gi \
  --no-allow-unauthenticated

# Invoke
SERVICE_URL=$(gcloud run services describe hr-onboarding-agent \
  --region us-central1 --format 'value(status.url)')

curl -X POST "$SERVICE_URL/verify" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{}'
```
