"""Generate sample invoice PDFs with planted discrepancies for testing.

This script uses reportlab to create realistic invoice PDFs. The text layout
matches the regex patterns in read_invoice_from_gcs(), so the agent can
extract vendor_id, amounts, tax_rate, and currency.

Usage:
    python scripts/generate_sample_invoices.py
    gsutil -m cp data/invoices/*.pdf gs://$PROJECT_ID-audit-invoices/Q3/
"""
import os
from reportlab.pdfgen import canvas

def create_invoice(vendor_id, vendor_name, inv_num, amount, currency, tax_rate, output_dir):
    """Generate a single invoice PDF with structured text fields."""
    os.makedirs(output_dir, exist_ok=True)
    c = canvas.Canvas(os.path.join(output_dir, f"{inv_num}.pdf"))
    c.drawString(100, 750, f"INVOICE: {inv_num}")
    c.drawString(100, 730, f"Vendor: {vendor_name} (ID: {vendor_id})")

    base_amount = amount / (1 + tax_rate)
    tax_amount = amount - base_amount

    c.drawString(100, 690, f"Base Amount: {base_amount:.2f} {currency}")
    c.drawString(100, 670, f"Tax Rate: {tax_rate * 100}%")
    c.drawString(100, 650, f"Tax Amount: {tax_amount:.2f} {currency}")
    c.drawString(100, 610, f"TOTAL: {amount:.2f} {currency}")
    c.save()

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'invoices')

    # Normal — matches ERP exactly
    create_invoice('1022', 'OfficeSupplies Co', 'INV-1022-Q3-014', 4500.00, 'USD', 0.05, output_dir)
    # Planted discrepancy 1: Tax calculation error (invoice shows 6.25% instead of 8.5%)
    create_invoice('8492', 'TechCorp', 'INV-8492-Q3-001', 138750.00, 'USD', 0.0625, output_dir)
    # Planted discrepancy 2: Currency mismatch (invoice in EUR, ERP in USD)
    create_invoice('3301', 'Global Services', 'INV-3301-Q3-099', 87500.00, 'EUR', 0.10, output_dir)
    # Planted discrepancy 3: Duplicate invoice (only one PDF, two ERP records)
    create_invoice('5567', 'Consulting Group', 'INV-5567-Q3-001', 23400.00, 'USD', 0.0, output_dir)

    print(f"✅ Generated 4 sample invoice PDFs in {os.path.abspath(output_dir)}")
