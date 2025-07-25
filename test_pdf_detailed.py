#!/usr/bin/env python3
"""
Test PDF generation with a real contract from the database
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
from contracts.pdf_generator import ContractPDFGenerator
import traceback

def test_pdf_generation():
    """Test the PDF generation functionality"""
    try:
        print("🔍 Looking for contracts in database...")
        contracts = Contract.objects.all()
        print(f"📊 Found {contracts.count()} contracts")
        
        if contracts.count() == 0:
            print("❌ No contracts found. Create a contract first!")
            return False
            
        # Use the first contract
        contract = contracts.first()
        print(f"✅ Using contract #{contract.id}")
        print(f"   Status: {contract.status}")
        print(f"   Total Payment: ${contract.total_payment}")
        
        # Test the PDF generator
        print("\n🔄 Generating PDF...")
        pdf_generator = ContractPDFGenerator()
        
        # First test context generation
        print("📝 Preparing contract context...")
        context = pdf_generator._get_contract_context(contract)
        print(f"   Client: {context.get('client', {}).get('username', 'N/A')}")
        print(f"   Freelancer: {context.get('freelancer', {}).get('username', 'N/A')}")
        print(f"   Job Title: {context.get('job_title', 'N/A')}")
        
        # Generate PDF
        print("🎨 Generating PDF content...")
        pdf_content = pdf_generator.generate_contract_pdf(contract)
        
        if pdf_content and len(pdf_content) > 0:
            print(f"✅ PDF generated successfully!")
            print(f"   Size: {len(pdf_content):,} bytes")
            
            # Save the PDF
            output_file = f'/Users/rejan/Documents/Epita/Action Learning /final/contract_{contract.id}_test.pdf'
            with open(output_file, 'wb') as f:
                f.write(pdf_content)
            
            print(f"💾 PDF saved to: {output_file}")
            
            # Verify the file
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ File verification: {file_size:,} bytes written to disk")
                return True
            else:
                print("❌ File was not created!")
                return False
        else:
            print("❌ PDF generation failed - no content returned")
            return False
            
    except Exception as e:
        print(f"💥 Error during PDF generation: {str(e)}")
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Contract PDF Generation...")
    print("=" * 60)
    
    success = test_pdf_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 PDF generation test PASSED!")
    else:
        print("💥 PDF generation test FAILED!")
        sys.exit(1)
