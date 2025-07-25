#!/usr/bin/env python
"""
Test script for the Rating API endpoints
Run this script to test the new rating system API
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from projects.models import Project
from reviews.models import Rating

def test_rating_api():
    """Test the rating API endpoints"""
    client = Client()
    User = get_user_model()
    
    print("🔍 Testing Rating API Endpoints")
    print("=" * 50)
    
    # Test 1: Check if endpoints are accessible (should require auth)
    print("\n1. Testing endpoint accessibility:")
    
    endpoints = [
        '/api/reviews/',
        '/api/reviews/ratings/',
        '/api/reviews/ratings/summary/',
        '/api/reviews/ratings/pending/',
        '/api/reviews/ratings/received/',
        '/api/reviews/ratings/given/',
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        status_icon = "✅" if response.status_code == 401 else "❌"
        print(f"  {status_icon} {endpoint} -> {response.status_code} (expects 401 - auth required)")
    
    # Test 2: Check models and relationships
    print("\n2. Testing model structure:")
    
    # Check if Rating model is properly configured
    try:
        rating_fields = [field.name for field in Rating._meta.fields]
        expected_fields = [
            'id', 'project', 'freelancer', 'client', 'rated_by', 'rated_user',
            'rating', 'review', 'communication_rating', 'quality_rating',
            'timeliness_rating', 'payment_rating', 'clarity_rating',
            'would_recommend', 'created_at', 'updated_at'
        ]
        
        missing_fields = set(expected_fields) - set(rating_fields)
        if not missing_fields:
            print("  ✅ Rating model has all required fields")
        else:
            print(f"  ❌ Rating model missing fields: {missing_fields}")
            
        print(f"  📋 Available fields: {', '.join(rating_fields)}")
        
    except Exception as e:
        print(f"  ❌ Error checking Rating model: {e}")
    
    # Test 3: Check database tables
    print("\n3. Testing database structure:")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%review%';")
            tables = cursor.fetchall()
            print(f"  📊 Rating/Review tables: {[table[0] for table in tables]}")
            
            # Check Rating table structure
            cursor.execute("PRAGMA table_info(reviews_rating);")
            rating_columns = cursor.fetchall()
            if rating_columns:
                print("  ✅ Rating table exists with columns:")
                for col in rating_columns[:5]:  # Show first 5 columns
                    print(f"    - {col[1]} ({col[2]})")
                if len(rating_columns) > 5:
                    print(f"    ... and {len(rating_columns) - 5} more columns")
            else:
                print("  ❌ Rating table not found")
                
    except Exception as e:
        print(f"  ❌ Error checking database: {e}")
    
    # Test 4: Check API URL routing
    print("\n4. Testing URL routing:")
    
    try:
        from django.urls import reverse
        from reviews.urls import urlpatterns
        
        print(f"  📍 Found {len(urlpatterns)} URL patterns in reviews app")
        
        # Test a few key URLs
        test_urls = [
            ('rating-list-create', '✅ Rating list/create endpoint'),
            ('rating-summary', '✅ Rating summary endpoint'),
            ('pending-ratings', '✅ Pending ratings endpoint'),
        ]
        
        for url_name, description in test_urls:
            try:
                url = reverse(url_name)
                print(f"    {description}: {url}")
            except:
                print(f"    ❌ {description}: URL not found")
                
    except Exception as e:
        print(f"  ❌ Error checking URLs: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Rating API Test Complete!")
    print("\nNext Steps:")
    print("1. Create test users and projects")
    print("2. Test rating submission with authentication")
    print("3. Test rating retrieval and filtering")
    print("4. Test rating summary calculations")
    
    return True

if __name__ == '__main__':
    test_rating_api()
