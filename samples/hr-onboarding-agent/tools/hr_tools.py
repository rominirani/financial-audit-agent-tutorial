from google.cloud import bigquery, storage
import json
import os
import re
import tempfile
from PyPDF2 import PdfReader
from datetime import datetime, UTC

PROJECT_ID = os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")
DATASET = "hr_onboarding"
BUCKET_NAME = f"{PROJECT_ID}-onboarding-documents"

_client = bigquery.Client(project=PROJECT_ID)

def query_pending_hires() -> str:
    query = f"""
    SELECT emp_id, name, role, department, start_date, status
    FROM `{PROJECT_ID}.{DATASET}.new_hires`
    WHERE status = 'PENDING'
    ORDER BY emp_id
    """
    rows = _client.query(query).result()
    results = []
    for row in rows:
        results.append({
            "emp_id": row.emp_id,
            "name": row.name,
            "role": row.role,
            "department": row.department,
            "start_date": str(row.start_date),
            "status": row.status,
        })
    return json.dumps({"total_hires": len(results), "hires": results}, indent=2)

def get_department_requirements(department: str) -> str:
    query = f"""
    SELECT department, doc_type, description, mandatory
    FROM `{PROJECT_ID}.{DATASET}.department_requirements`
    WHERE department = '{department}'
    """
    rows = _client.query(query).result()
    results = []
    for row in rows:
        results.append({
            "doc_type": row.doc_type,
            "description": row.description,
            "mandatory": row.mandatory,
        })
    return json.dumps({"department": department, "requirements": results}, indent=2)

def list_employee_documents(emp_id: str) -> str:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=f"{emp_id}/")
    documents = []
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            documents.append({
                "name": blob.name,
                "size_bytes": blob.size,
                "gs_uri": f"gs://{BUCKET_NAME}/{blob.name}",
            })
    return json.dumps({"emp_id": emp_id, "total_documents": len(documents), "documents": documents}, indent=2)

def read_employee_document(document_path: str) -> str:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(document_path)
    if not blob.exists():
        return json.dumps({"error": f"Document not found: gs://{BUCKET_NAME}/{document_path}"})
    
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        blob.download_to_filename(tmp.name)
        reader = PdfReader(tmp.name)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    
    result = {
        "gs_uri": f"gs://{BUCKET_NAME}/{document_path}",
        "raw_text": text,
        "doc_type": _extract(r"DOCUMENT TYPE:\s*(.+)", text),
        "employee_name": _extract(r"Employee Name:\s*(.+)", text),
        "issue_date": _extract(r"Issue Date:\s*([\d-]+)", text),
        "expiry_date": _extract(r"Expiry Date:\s*([\d-]+)", text),
        "certification_name": _extract(r"Certification:\s*(.+)", text),
        "issuing_authority": _extract(r"Issuing Authority:\s*(.+)", text),
    }
    return json.dumps(result, indent=2)

def _extract(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None

def write_compliance_result(
    execution_id: str,
    emp_id: str,
    department: str,
    status: str,
    missing_documents: str,
    expired_documents: str,
    compliance_notes: str,
    reviewed_by: str = "agent"
) -> str:
    row = {
        "execution_id": execution_id,
        "emp_id": emp_id,
        "department": department,
        "status": status,
        "missing_documents": missing_documents,
        "expired_documents": expired_documents,
        "compliance_notes": compliance_notes,
        "reviewed_by": reviewed_by,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    table_ref = f"{PROJECT_ID}.{DATASET}.compliance_results"
    errors = _client.insert_rows_json(table_ref, [row])
    if errors:
        return f"ERROR writing compliance result: {errors}"
    return f"✅ Compliance result written for employee {emp_id} — status: {status}"

HR_TOOLS = [query_pending_hires, get_department_requirements, list_employee_documents, read_employee_document, write_compliance_result]
