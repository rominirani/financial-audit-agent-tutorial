import os
from reportlab.pdfgen import canvas

def create_document(emp_id, doc_type, emp_name, issue_date, expiry_date, cert_name, authority, output_dir):
    emp_dir = os.path.join(output_dir, emp_id)
    os.makedirs(emp_dir, exist_ok=True)
    filename = f"{doc_type.replace(' ', '_')}.pdf"
    c = canvas.Canvas(os.path.join(emp_dir, filename))
    c.drawString(100, 750, f"DOCUMENT TYPE: {doc_type}")
    c.drawString(100, 730, f"Employee Name: {emp_name}")
    c.drawString(100, 710, f"Issue Date: {issue_date}")
    if expiry_date:
        c.drawString(100, 690, f"Expiry Date: {expiry_date}")
    if cert_name:
        c.drawString(100, 670, f"Certification: {cert_name}")
    if authority:
        c.drawString(100, 650, f"Issuing Authority: {authority}")
    c.save()

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'documents')

    # EMP-2847 (Engineering): Missing security clearance
    create_document('EMP-2847', 'ID', 'Jane Smith', '2020-01-01', '2030-01-01', '', '', output_dir)
    create_document('EMP-2847', 'Tax Form', 'Jane Smith', '2023-01-01', '', '', '', output_dir)
    
    # EMP-1155 (Healthcare): Expired HIPAA cert
    create_document('EMP-1155', 'ID', 'Michael Johnson', '2019-05-05', '2029-05-05', '', '', output_dir)
    create_document('EMP-1155', 'HIPAA Certification', 'Michael Johnson', '2020-01-01', '2025-12-31', 'HIPAA Pro', 'HealthBoard', output_dir)
    
    # EMP-4490 (Finance): Clean
    create_document('EMP-4490', 'ID', 'Alice Williams', '2021-02-02', '2031-02-02', '', '', output_dir)
    create_document('EMP-4490', 'SOX Certification', 'Alice Williams', '2023-01-01', '2027-12-31', 'SOX Compliance', 'FinAuthority', output_dir)
    
    # EMP-3321 (Engineering): Name mismatch
    create_document('EMP-3321', 'ID', 'Robert James Chen-Wu', '2018-03-03', '2028-03-03', '', '', output_dir)
    create_document('EMP-3321', 'Security Clearance', 'Robert James Chen-Wu', '2023-01-01', '2028-01-01', 'Top Secret', 'DoD', output_dir)

    print(f"✅ Generated sample documents in {os.path.abspath(output_dir)}")
