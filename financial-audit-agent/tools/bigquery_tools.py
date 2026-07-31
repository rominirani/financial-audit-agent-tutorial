from google.cloud import bigquery, storage
import json

PROJECT_ID = "YOUR_PROJECT_ID"  # Replace with your GCP project ID
DATASET = "financial_audit"

_client = bigquery.Client(project=PROJECT_ID)


def query_vendor_transactions(quarter: str = "Q3") -> str:
    """Query BigQuery for all PENDING vendor transactions in a given quarter.

    Args:
        quarter: The fiscal quarter to query (e.g. "Q3").

    Returns:
        JSON string with the transaction records.
    """
    query = f"""
    SELECT vendor_id, vendor_name, invoice_num, amount, currency, tax_rate, status, quarter, transaction_date
    FROM `{PROJECT_ID}.{DATASET}.vendor_transactions`
    WHERE status = 'PENDING' AND quarter = '{quarter}'
    ORDER BY vendor_id, invoice_num
    """
    rows = _client.query(query).result()
    results = []
    for row in rows:
        results.append({
            "vendor_id": row.vendor_id,
            "vendor_name": row.vendor_name,
            "invoice_num": row.invoice_num,
            "amount": row.amount,
            "currency": row.currency,
            "tax_rate": row.tax_rate,
            "status": row.status,
            "quarter": row.quarter,
            "transaction_date": str(row.transaction_date),
        })
    return json.dumps({"total_transactions": len(results), "transactions": results}, indent=2)


def list_invoices_in_gcs(bucket_name: str, prefix: str = "Q3/") -> str:
    """List all invoice PDF files in a Google Cloud Storage bucket.

    Args:
        bucket_name: The GCS bucket name (e.g. "my-project-audit-invoices").
        prefix: Path prefix to filter by (e.g. "Q3/" for Q3 invoices).

    Returns:
        JSON string with the list of invoice file paths.
    """
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    invoices = []
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            invoices.append({
                "name": blob.name,
                "size_bytes": blob.size,
                "gs_uri": f"gs://{bucket_name}/{blob.name}",
            })
    return json.dumps({"total_invoices": len(invoices), "invoices": invoices}, indent=2)


def read_invoice_from_gcs(bucket_name: str, invoice_path: str) -> str:
    """Read an invoice PDF from Google Cloud Storage and extract its structured data.

    Downloads the PDF, parses its text content, and returns structured fields
    including vendor ID, invoice number, amounts, tax rate, and currency.

    Args:
        bucket_name: The GCS bucket name (e.g. "my-project-audit-invoices").
        invoice_path: Path to the invoice within the bucket (e.g. "Q3/INV-8492-Q3-001.pdf").

    Returns:
        JSON string with extracted invoice data (vendor_id, invoice_num,
        base_amount, tax_rate, tax_amount, total_amount, currency).
    """
    import re
    import tempfile
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(invoice_path)

    if not blob.exists():
        return json.dumps({"error": f"Invoice not found: gs://{bucket_name}/{invoice_path}"})

    # Download PDF to temp file and extract text
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        blob.download_to_filename(tmp.name)

        # Extract text using PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(tmp.name)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

    # Parse structured fields from the extracted text
    result = {
        "gs_uri": f"gs://{bucket_name}/{invoice_path}",
        "raw_text": text,
        "vendor_id": _extract(r"ID:\s*(\d+)", text),
        "vendor_name": _extract(r"Vendor:\s*(.+?)\s*\(", text),
        "invoice_num": _extract(r"INVOICE:\s*(INV-[\w-]+)", text),
        "base_amount": _extract_float(r"Base Amount:\s*([\d,.]+)", text),
        "tax_rate": _extract_float(r"Tax Rate:\s*([\d.]+)%", text),
        "tax_amount": _extract_float(r"Tax Amount:\s*([\d,.]+)", text),
        "total_amount": _extract_float(r"TOTAL:\s*([\d,.]+)", text),
        "currency": _extract(r"TOTAL:\s*[\d,.]+\s+(\w{3})", text),
    }
    # Convert tax_rate from percentage to decimal if found
    if result["tax_rate"] is not None:
        result["tax_rate"] = round(result["tax_rate"] / 100, 4)

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


def write_audit_result(
    execution_id: str,
    vendor_id: str,
    invoice_num: str,
    transaction_amount: float,
    invoice_amount: float,
    discrepancy_amount: float,
    status: str,
    agent_notes: str,
    reviewed_by: str = "agent",
) -> str:
    """Write a single audit result row to BigQuery.

    Args:
        execution_id: Unique ID for this audit run.
        vendor_id: The vendor's ID.
        invoice_num: The invoice number.
        transaction_amount: Amount from the transaction record.
        invoice_amount: Amount from the invoice.
        discrepancy_amount: The difference (transaction - invoice).
        status: One of MATCHED, DISCREPANCY, UNMATCHED, ESCALATED.
        agent_notes: Agent's explanation of the finding.
        reviewed_by: Who reviewed this result.

    Returns:
        Confirmation message.
    """
    from datetime import datetime, UTC

    row = {
        "execution_id": execution_id,
        "vendor_id": vendor_id,
        "invoice_num": invoice_num,
        "transaction_amount": transaction_amount,
        "invoice_amount": invoice_amount,
        "discrepancy_amount": discrepancy_amount,
        "status": status,
        "agent_notes": agent_notes,
        "reviewed_by": reviewed_by,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    table_ref = f"{PROJECT_ID}.{DATASET}.audit_results"
    errors = _client.insert_rows_json(table_ref, [row])

    if errors:
        return f"ERROR writing audit result: {errors}"
    return f"✅ Audit result written for vendor {vendor_id} / {invoice_num} — status: {status}"


# Export all tools as a list for the SDK
AUDIT_TOOLS = [query_vendor_transactions, list_invoices_in_gcs, read_invoice_from_gcs, write_audit_result]
