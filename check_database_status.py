#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from projects.models import Project, ProjectProposal
from contracts.models import Contract
from users.models import CustomUser

print("📊 DATABASE STATUS CHECK")
print("=" * 40)

# Check users
clients = CustomUser.objects.filter(user_type='client')
freelancers = CustomUser.objects.filter(user_type='freelancer')
print(f"👥 Users: {clients.count()} clients, {freelancers.count()} freelancers")

# Check projects
projects = Project.objects.all()
print(f"📋 Projects: {projects.count()}")
for i, project in enumerate(projects[:3], 1):
    print(f"  {i}. {project.title} (Client: {project.client.username})")

# Check proposals
proposals = ProjectProposal.objects.all()
accepted_proposals = proposals.filter(status='accepted')
print(f"📝 Proposals: {proposals.count()} total, {accepted_proposals.count()} accepted")

for proposal in accepted_proposals[:3]:
    print(f"  ✅ Proposal {proposal.id}: {proposal.project.title} by {proposal.freelancer.username}")

# Check contracts
contracts = Contract.objects.all()
print(f"📄 Contracts: {contracts.count()}")

if contracts.exists():
    for contract in contracts[:3]:
        print(f"  📋 Contract {contract.id}: {contract.project_proposal.project.title}")

print(f"\n🎯 READY TO CREATE CONTRACTS:")
if accepted_proposals.exists():
    proposal = accepted_proposals.first()
    print(f"✅ Use proposal ID {proposal.id} for contract creation")
    print(f"   Project: {proposal.project.title}")
    print(f"   Client: {proposal.project.client.username}")
    print(f"   Freelancer: {proposal.freelancer.username}")
else:
    print("❌ No accepted proposals available")
    print("   Need to accept a proposal first")
