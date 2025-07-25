#!/usr/bin/env python3
"""
Test ReportLab PDF generation
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from contracts.models import Contract
from contracts.pdf_generator_reportlab import ContractPDFGenerator
import traceback

def test_reportlab_pdf():
    """Test the ReportLab PDF generation"""
    try:
        print("🔍 Looking for contracts...")
        contracts = Contract.objects.all()
        print(f"📊 Found {contracts.count()} contracts")
        
        if contracts.count() == 0:
            print("❌ No contracts found!")
            return False
            
        contract = contracts.first()
        print(f"✅ Using contract #{contract.id}")
        
        # Test PDF generation
        print("🎨 Generating PDF with ReportLab...")
        pdf_generator = ContractPDFGenerator()
        pdf_content = pdf_generator.generate_contract_pdf(contract)
        
        if pdf_content and len(pdf_content) > 0:
            print(f"✅ PDF generated! Size: {len(pdf_content):,} bytes")
            
            # Save the PDF
            output_file = f'/Users/rejan/Documents/Epita/Action Learning /final/contract_reportlab_{contract.id}.pdf'
            with open(output_file, 'wb') as f:
                f.write(pdf_content)
            
            print(f"💾 PDF saved to: {output_file}")
            
            # Test the HTTP response creation
            print("🌐 Testing HTTP response...")
            response = pdf_generator.create_pdf_response(contract)
            print(f"✅ HTTP response created: {response.status_code}")
            print(f"   Content-Type: {response.get('Content-Type')}")
            print(f"   Content-Length: {response.get('Content-Length')}")
            
            return True
        else:
            print("❌ PDF generation failed")
            return False
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing ReportLab PDF Generation...")
    print("=" * 60)
    
    success = test_reportlab_pdf()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ReportLab PDF test PASSED!")
    else:
        print("💥 ReportLab PDF test FAILED!")
        sys.exit(1)
