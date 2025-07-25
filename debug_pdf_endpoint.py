#!/usr/bin/env python3
"""
Simple test to debug PDF endpoint
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from contracts.models import Contract

def test_pdf_endpoint():
    """Test the PDF endpoint directly"""
    try:
        # Get a contract
        contract = Contract.objects.first()
        if not contract:
            print("❌ No contract found")
            return False
            
        print(f"✅ Found contract #{contract.id}")
        
        # Test the view directly
        from contracts.views import ContractViewSet
        from contracts.pdf_generator_reportlab import ContractPDFGenerator
        
        # Test PDF generation directly
        pdf_generator = ContractPDFGenerator()
        response = pdf_generator.create_pdf_response(contract)
        
        print(f"✅ Direct PDF generation: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type')}")
        print(f"   Content-Length: {response.get('Content-Length')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing PDF endpoint directly...")
    success = test_pdf_endpoint()
    
    if success:
        print("✅ Direct test passed!")
    else:
        print("❌ Direct test failed!")
