#!/usr/bin/env python3
"""
Test script for contract PDF generation
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

def test_pdf_generation():
    """Test the PDF generation functionality"""
    try:
        # Get the first contract for testing
        contract = Contract.objects.first()
        if not contract:
            print("❌ No contracts found in database. Please create a contract first.")
            return False
            
        print(f"✅ Found contract #{contract.id}")
        
        # Test PDF generation
        pdf_generator = ContractPDFGenerator()
        pdf_content = pdf_generator.generate_contract_pdf(contract)
        
        if pdf_content:
            print(f"✅ PDF generated successfully! Size: {len(pdf_content)} bytes")
            
            # Save test PDF file
            test_file = f'/Users/rejan/Documents/Epita/Action Learning /final/test_contract_{contract.id}.pdf'
            with open(test_file, 'wb') as f:
                f.write(pdf_content)
            print(f"✅ Test PDF saved to: {test_file}")
            return True
        else:
            print("❌ PDF generation failed - no content returned")
            return False
            
    except Exception as e:
        print(f"❌ Error during PDF generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Testing Contract PDF Generation...")
    success = test_pdf_generation()
    
    if success:
        print("\n🎉 Contract PDF generation test completed successfully!")
    else:
        print("\n💥 Contract PDF generation test failed!")
        sys.exit(1)
