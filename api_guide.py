#!/usr/bin/env python3
"""
Comprehensive API Guide for Contract Creation and Dispute Management
"""
import os
import django
import sys
import requests
import json

# Add the parent directory to Python path
sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from users.models import CustomUser
from disputes.models import Dispute
from contracts.models import Contract
from projects.models import Project, ProjectProposal

BASE_URL = "http://localhost:8000"


def show_contract_creation_guide():
    """Complete guide for creating contracts"""
    print("📋 CONTRACT CREATION API GUIDE")
    print("=" * 60)
    
    print("\n🔗 API Endpoint:")
    print("POST /api/contracts/")
    
    print("\n📝 Required Steps:")
    print("1. Have an accepted proposal (proposal.status = 'accepted')")
    print("2. Be the client who owns the project")
    print("3. Send POST request with proposal ID")
    
    print("\n🏗️ Request Format:")
    contract_request = {
        "proposal": 1,  # ID of accepted proposal
        "start_date": "2025-07-25",
        "end_date": "2025-08-25",
        "total_payment": "1500.00",
        "deliverables": "Complete website development with responsive design",
        "milestones": "Week 1: Design mockups, Week 2: Frontend, Week 3: Backend, Week 4: Testing"
    }
    print(json.dumps(contract_request, indent=2))
    
    print("\n🔐 Authentication:")
    print("Headers: {")
    print("  'Authorization': 'Bearer <your_jwt_token>',")
    print("  'Content-Type': 'application/json'")
    print("}")
    
    print("\n✅ Success Response (201):")
    success_response = {
        "id": 1,
        "project_proposal": 1,
        "project_id": "1",
        "project_title": "E-commerce Website Development",
        "client": {
            "id": 1,
            "username": "client_user",
            "email": "client@example.com",
            "user_type": "client"
        },
        "freelancer": {
            "id": 2,
            "username": "freelancer_user",
            "email": "freelancer@example.com",
            "user_type": "freelancer"
        },
        "start_date": "2025-07-25",
        "end_date": "2025-08-25",
        "status": "active",
        "total_payment": "1500.00",
        "deliverables": "Complete website development with responsive design",
        "milestones": "Week 1: Design mockups, Week 2: Frontend, Week 3: Backend, Week 4: Testing",
        "created_at": "2025-07-25T10:00:00Z",
        "signed_by_client": False,
        "signed_by_freelancer": False
    }
    print(json.dumps(success_response, indent=2))
    
    print("\n❌ Common Errors:")
    print("• 400: 'proposal field is required' - Missing proposal ID")
    print("• 404: 'Proposal not found' - Invalid proposal ID")
    print("• 403: 'Only the project owner can create contracts' - Not the client")
    print("• 400: 'Only accepted proposals can be converted to contracts' - Proposal not accepted")
    print("• 400: 'Contract already exists for this proposal' - Duplicate contract")


def show_dispute_creation_guide():
    """Complete guide for creating disputes"""
    print("\n\n🚨 DISPUTE CREATION API GUIDE")
    print("=" * 60)
    
    print("\n🔗 API Endpoint:")
    print("POST /api/disputes/")
    
    print("\n👤 Access Control:")
    print("• Only FREELANCERS can create disputes")
    print("• Must be authenticated with JWT token")
    
    print("\n🏗️ Request Format:")
    dispute_request = {
        "title": "Payment Issue - Project Not Paid",
        "description": "The client has not released payment despite project completion and approval. Payment was due 7 days ago according to the contract terms.",
        "type": "payment",  # payment, quality, communication, deadline, scope, other
        "priority": "high",  # low, medium, high, urgent
        "project_id": 1,  # Either project_id OR contract_id (or both)
        "contract_id": 1   # Optional - for contract-specific disputes
    }
    print(json.dumps(dispute_request, indent=2))
    
    print("\n📋 Dispute Types:")
    for type_code, type_name in [
        ('payment', 'Payment Issue'),
        ('quality', 'Quality Issue'),
        ('communication', 'Communication Issue'),
        ('deadline', 'Deadline Issue'),
        ('scope', 'Scope Creep'),
        ('other', 'Other')
    ]:
        print(f"  • '{type_code}': {type_name}")
    
    print("\n⚡ Priority Levels:")
    for priority_code, priority_name in [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]:
        print(f"  • '{priority_code}': {priority_name}")
    
    print("\n🔐 Authentication:")
    print("Headers: {")
    print("  'Authorization': 'Bearer <freelancer_jwt_token>',")
    print("  'Content-Type': 'application/json'")
    print("}")
    
    print("\n✅ Success Response (201):")
    success_response = {
        "id": 1,
        "title": "Payment Issue - Project Not Paid",
        "description": "The client has not released payment despite project completion...",
        "type": "payment",
        "priority": "high",
        "status": "open",
        "project": 1,
        "contract": 1,
        "created_by": {
            "id": 2,
            "username": "freelancer_user",
            "email": "freelancer@example.com"
        },
        "created_at": "2025-07-25T10:00:00Z",
        "updated_at": "2025-07-25T10:00:00Z",
        "resolution": ""
    }
    print(json.dumps(success_response, indent=2))


def show_api_testing_examples():
    """Show practical API testing examples"""
    print("\n\n🧪 PRACTICAL API TESTING EXAMPLES")
    print("=" * 60)
    
    print("\n1. 📋 List Contracts (GET /api/contracts/)")
    print("curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/contracts/")
    
    print("\n2. 🆕 Create Contract (POST /api/contracts/)")
    print("""curl -X POST http://localhost:8000/api/contracts/ \\
  -H 'Authorization: Bearer <client_token>' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "proposal": 1,
    "start_date": "2025-07-25",
    "end_date": "2025-08-25",
    "total_payment": "1500.00",
    "deliverables": "Website development",
    "milestones": "Weekly deliverables"
  }'""")
    
    print("\n3. 🚨 Create Dispute (POST /api/disputes/)")
    print("""curl -X POST http://localhost:8000/api/disputes/ \\
  -H 'Authorization: Bearer <freelancer_token>' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "title": "Payment overdue",
    "description": "Client has not paid for completed work",
    "type": "payment",
    "priority": "high",
    "project_id": 1,
    "contract_id": 1
  }'""")
    
    print("\n4. 📋 List Disputes with Filters (GET /api/disputes/)")
    print("curl -H 'Authorization: Bearer <freelancer_token>' 'http://localhost:8000/api/disputes/?priority=high&type=payment'")


def test_current_database_state():
    """Test current state of database"""
    print("\n\n💾 CURRENT DATABASE STATE")
    print("=" * 60)
    
    try:
        # Check users
        clients = CustomUser.objects.filter(user_type='client').count()
        freelancers = CustomUser.objects.filter(user_type='freelancer').count()
        print(f"👥 Users: {clients} clients, {freelancers} freelancers")
        
        # Check projects and proposals
        projects = Project.objects.count()
        proposals = ProjectProposal.objects.count()
        accepted_proposals = ProjectProposal.objects.filter(status='accepted').count()
        print(f"📋 Projects: {projects} total, {proposals} proposals ({accepted_proposals} accepted)")
        
        # Check contracts
        contracts = Contract.objects.count()
        active_contracts = Contract.objects.filter(status='active').count()
        print(f"📄 Contracts: {contracts} total ({active_contracts} active)")
        
        # Check disputes
        disputes = Dispute.objects.count()
        open_disputes = Dispute.objects.filter(status='open').count()
        print(f"🚨 Disputes: {disputes} total ({open_disputes} open)")
        
        print("\n📈 Ready for Testing:")
        if accepted_proposals > 0:
            print("✅ Accepted proposals available for contract creation")
        else:
            print("❌ No accepted proposals - cannot create contracts")
            
        if freelancers > 0:
            print("✅ Freelancers available for dispute creation")
        else:
            print("❌ No freelancers - cannot create disputes")
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")


if __name__ == "__main__":
    print("🚀 FREELANCEHUB API GUIDE")
    print("=" * 80)
    
    # Show guides
    show_contract_creation_guide()
    show_dispute_creation_guide()
    show_api_testing_examples()
    
    # Test current state
    test_current_database_state()
    
    print("\n" + "=" * 80)
    print("📚 Complete API documentation generated!")
    print("🎯 Use this guide to create contracts and disputes via API")
