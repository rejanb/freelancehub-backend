#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()

# Create a test client
client = Client()

# Get the client user (rejanc@gmail.com)
user = User.objects.get(email='rejanc@gmail.com')
print(f"Testing with user: {user.email}")

# Log in the user
client.force_login(user)

# Test the API endpoints
print("\n=== Testing API Endpoints ===")

# Test 1: Get all contracts
print("\n1. All contracts:")
response = client.get('/api/contracts/contracts/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Results: {len(data.get('results', []))}")
    for contract in data.get('results', []):
        print(f"  Contract {contract['id']}: {contract['status']}")

# Test 2: Filter by status=active
print("\n2. Active contracts:")
response = client.get('/api/contracts/contracts/?status=active')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Results: {len(data.get('results', []))}")
    for contract in data.get('results', []):
        print(f"  Contract {contract['id']}: {contract['status']}")

# Test 3: Filter by status=completed
print("\n3. Completed contracts:")
response = client.get('/api/contracts/contracts/?status=completed')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Results: {len(data.get('results', []))}")
    for contract in data.get('results', []):
        print(f"  Contract {contract['id']}: {contract['status']}")

# Test 4: Filter by status=cancelled
print("\n4. Cancelled contracts:")
response = client.get('/api/contracts/contracts/?status=cancelled')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Results: {len(data.get('results', []))}")
    for contract in data.get('results', []):
        print(f"  Contract {contract['id']}: {contract['status']}")

print("\n=== Test Complete ===")
