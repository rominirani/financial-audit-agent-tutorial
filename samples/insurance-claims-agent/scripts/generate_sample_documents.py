import os
from reportlab.pdfgen import canvas

def create_document(claim_id, claimant, claim_type, provider, procedure, amount, date, output_dir):
    """Generate a single claim document PDF with structured text fields."""
    os.makedirs(output_dir, exist_ok=True)
    c = canvas.Canvas(os.path.join(output_dir, f"{claim_id}.pdf"))
    
    # Matches regex in read_claim_document
    # "CLAIM:\s*(CLM-\d+)"
    # "Claimant:\s*(.+?)\n"
    # "Claim Type:\s*(.+?)\n"
    # "Provider:\s*(.+?)\n"
    # "Procedure/Damage:\s*(.+?)\n"
    # "Amount:\s*\$?([\d,.]+)"
    # "Date:\s*(.+?)\n"
    
    textobject = c.beginText()
    textobject.setTextOrigin(100, 750)
    lines = [
        f"CLAIM: {claim_id}",
        f"Claimant: {claimant}",
        f"Claim Type: {claim_type}",
        f"Provider: {provider}",
        f"Procedure/Damage: {procedure}",
        f"Amount: ${amount:.2f}",
        f"Date: {date}",
    ]
    for line in lines:
        textobject.textLine(line)
    c.drawText(textobject)
    c.save()

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'documents')

    # CLM-4821 (Auto): Amount $45,000 but policy max $25,000
    create_document('CLM-4821', 'Alice Smith', 'Auto', 'City Repair Shop', 'Total Loss Replacement', 45000.00, '2026-08-01', output_dir)
    # CLM-1133 (Medical): Clean — $2,300 matches receipts
    create_document('CLM-1133', 'Bob Johnson', 'Medical', 'General Hospital', 'Appendectomy', 2300.00, '2026-07-20', output_dir)
    # CLM-7744 (Property): Date mismatch — claim filed 2026-08-10, incident 2026-08-15
    create_document('CLM-7744', 'Charlie Brown', 'Property', 'Home Fixers', 'Roof Repair', 5000.00, '2026-08-15', output_dir)
    # CLM-9902 (Medical): Duplicate — same procedure, same provider, same amount
    create_document('CLM-9902', 'Diana Prince', 'Medical', 'City Clinic', 'MRI Scan', 1500.00, '2026-07-25', output_dir)

    print(f"✅ Generated 4 sample claim document PDFs in {os.path.abspath(output_dir)}")
