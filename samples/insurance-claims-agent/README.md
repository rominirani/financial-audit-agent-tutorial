# Insurance Claims Processing Agent (Delegation Architecture)

This project is an automated AI agent for processing insurance claims. It demonstrates the **Delegation Architecture** pattern, utilizing Google Antigravity and Vertex AI to orchestrate multiple specialized subagents.

## Architecture

This sample leverages the **Delegation Architecture** pattern:
- **Orchestrator Agent**: A high-level planner (using `gemini-3.6-flash`) with ZERO direct data tools. It delegates work to specialized subagents.
- **Claims Researcher**: A specialized subagent (using `gemini-3.5-flash-lite`) that handles querying BigQuery for claims and policies.
- **Document Analyzer**: A specialized subagent (using `gemini-3.5-flash-lite`) that lists and reads PDF documents from Google Cloud Storage.
- **Adjudication Engine**: A specialized subagent (using `gemini-3.6-flash`) that reviews all gathered context and executes the final write to BigQuery.

All agents run using `location='global'`.

### Key Concepts Demonstrated:
1. **Model Tiering**: Using `gemini-3.6-flash` for complex reasoning (orchestrator, adjudicator) and `gemini-3.5-flash-lite` for simpler data retrieval and extraction tasks.
2. **State Accumulation**: Delegation tools accumulate state in a central module (`tools/delegation_tools.py`) rather than passing massive context payloads back and forth between tools.
3. **Guardrails**: The Adjudication Engine will refuse to run if the research and analysis phases haven't been completed.
4. **Environment Policies**: Demonstrates dev/staging/prod policy sets, with staging utilizing a rich `compliance_officer_approval_handler` interactive prompt.

## Prerequisites

- Python 3.10+
- Google Cloud Project with Billing Enabled
- Google Cloud SDK (`gcloud`) installed and authenticated

## Quick Start Setup

1. **Set your Project ID:**
   ```bash
   export PROJECT_ID="your-gcp-project-id"
   gcloud config set project $PROJECT_ID
   ```

2. **Run the setup script:**
   This script creates the BigQuery dataset, tables, GCS bucket, and uploads sample PDFs.
   ```bash
   pip install -r requirements.txt
   python scripts/generate_sample_documents.py
   ```

3. **Run the Agent CLI:**

   **Dev Mode** (Fully autonomous):
   ```bash
   python main.py --mode=dev --project-id=$PROJECT_ID
   ```

   **Staging Mode** (Requires Compliance Officer interactive approval before adjudication):
   ```bash
   python main.py --mode=staging --project-id=$PROJECT_ID
   ```

   **Prod Mode** (Fully autonomous):
   ```bash
   python main.py --mode=prod --project-id=$PROJECT_ID
   ```

4. **Run the Server:**
   ```bash
   export PROJECT_ID=$PROJECT_ID
   python server.py
   ```
   Then send a request:
   ```bash
   curl -X POST http://localhost:8080/process -H "Content-Type: application/json" -d '{}'
   ```

5. **Run the Evals:**
   ```bash
   python eval/run_eval.py --project-id=$PROJECT_ID
   ```
