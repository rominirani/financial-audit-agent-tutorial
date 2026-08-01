from google.cloud import bigquery, storage
import json
import os

PROJECT_ID = os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")
DATASET = "insurance_claims"
BUCKET_NAME = f"{PROJECT_ID}-claims-documents"

_client = bigquery.Client(project=PROJECT_ID)

def query_pending_claims() -> str:
    """Query BigQuery for all PENDING insurance claims.

    Returns:
        JSON string with the claim records.
    """
    query = f"""
    SELECT claim_id, claimant_name, policy_number, claim_type, amount, date_filed, incident_date, status
    FROM `{PROJECT_ID}.{DATASET}.claims`
    WHERE status = 'PENDING'
    ORDER BY claim_id
    """
    rows = _client.query(query).result()
    results = []
    for row in rows:
        results.append({
            "claim_id": row.claim_id,
            "claimant_name": row.claimant_name,
            "policy_number": row.policy_number,
            "claim_type": row.claim_type,
            "amount": row.amount,
            "date_filed": str(row.date_filed),
            "incident_date": str(row.incident_date),
            "status": row.status,
        })
    return json.dumps({"total_claims": len(results), "claims": results}, indent=2)

def get_policy_details(policy_number: str) -> str:
    """Query BigQuery for coverage rules for a specific policy.

    Args:
        policy_number: The policy number.

    Returns:
        JSON string with policy details.
    """
    query = f"""
    SELECT policy_number, coverage_type, max_coverage, deductible, exclusions
    FROM `{PROJECT_ID}.{DATASET}.policies`
    WHERE policy_number = '{policy_number}'
    """
    rows = _client.query(query).result()
    results = []
    for row in rows:
        results.append({
            "policy_number": row.policy_number,
            "coverage_type": row.coverage_type,
            "max_coverage": row.max_coverage,
            "deductible": row.deductible,
            "exclusions": row.exclusions,
        })
    return json.dumps({"total_policies": len(results), "policies": results}, indent=2)

def list_claim_documents(claim_id: str) -> str:
    """List all PDF documents for a claim in Google Cloud Storage.

    Args:
        claim_id: The ID of the claim to filter by.

    Returns:
        JSON string with the list of document file paths.
    """
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    prefix = f"claims/{claim_id}/"
    blobs = bucket.list_blobs(prefix=prefix)
    documents = []
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            documents.append({
                "name": blob.name,
                "size_bytes": blob.size,
                "gs_uri": f"gs://{BUCKET_NAME}/{blob.name}",
            })
    return json.dumps({"total_documents": len(documents), "documents": documents}, indent=2)

def read_claim_document(document_path: str) -> str:
    """Read a claim document PDF from Google Cloud Storage and extract its data.

    Args:
        document_path: Path to the document within the bucket.

    Returns:
        JSON string with extracted claim data.
    """
    import re
    import tempfile
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(document_path)

    if not blob.exists():
        return json.dumps({"error": f"Document not found: gs://{BUCKET_NAME}/{document_path}"})

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        blob.download_to_filename(tmp.name)

        from PyPDF2 import PdfReader
        reader = PdfReader(tmp.name)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

    result = {
        "gs_uri": f"gs://{BUCKET_NAME}/{document_path}",
        "raw_text": text,
        "claim_id": _extract(r"CLAIM:\s*(CLM-\d+)", text),
        "claimant": _extract(r"Claimant:\s*(.+?)\n", text),
        "claim_type": _extract(r"Claim Type:\s*(.+?)\n", text),
        "provider": _extract(r"Provider:\s*(.+?)\n", text),
        "procedure_damage": _extract(r"Procedure/Damage:\s*(.+?)\n", text),
        "amount": _extract_float(r"Amount:\s*\$?([\d,.]+)", text),
        "date": _extract(r"Date:\s*(.+?)\n", text),
    }

    return json.dumps(result, indent=2)

def _extract(pattern: str, text: str) -> str | None:
    """Extract a single regex match from text."""
    import re
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None

def _extract_float(pattern: str, text: str) -> float | None:
    """Extract a float value from text via regex."""
    import re
    m = re.search(pattern, text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None

def write_adjudication_result(
    execution_id: str,
    claim_id: str,
    policy_number: str,
    claimed_amount: float,
    approved_amount: float,
    status: str,
    adjudication_notes: str,
    reviewed_by: str = "agent",
) -> str:
    """Write an adjudication result row to BigQuery.

    Args:
        execution_id: Unique ID for this adjudication run.
        claim_id: The claim ID.
        policy_number: The policy number.
        claimed_amount: Amount claimed.
        approved_amount: Amount approved.
        status: One of APPROVED, DENIED, ESCALATED, FLAGGED.
        adjudication_notes: Agent's explanation.
        reviewed_by: Who reviewed this result.

    Returns:
        Confirmation message.
    """
    from datetime import datetime, UTC

    row = {
        "execution_id": execution_id,
        "claim_id": claim_id,
        "policy_number": policy_number,
        "claimed_amount": claimed_amount,
        "approved_amount": approved_amount,
        "status": status,
        "adjudication_notes": adjudication_notes,
        "reviewed_by": reviewed_by,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    table_ref = f"{PROJECT_ID}.{DATASET}.adjudication_results"
    errors = _client.insert_rows_json(table_ref, [row])

    if errors:
        return f"ERROR writing adjudication result: {errors}"
    return f"✅ Adjudication result written for claim {claim_id} — status: {status}"

CLAIMS_TOOLS = [query_pending_claims, get_policy_details, list_claim_documents, read_claim_document, write_adjudication_result]
