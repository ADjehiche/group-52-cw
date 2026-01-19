#!/usr/bin/env python3
"""
Test script for the Q&A API endpoints.
This script demonstrates all three endpoints with proper authentication and permissions.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def main():
    # For demonstration purposes, you'll need to:
    # 1. Create a user account via Django admin or signup page
    # 2. Create an item (auction) via the POST /api/items/ endpoint
    # 3. Run this script with proper authentication cookies
    
    print("Q&A API Test Script")
    print("=" * 50)
    
    # Test 1: GET questions for an item (public - no auth required)
    print("\n1. Testing GET /api/items/1/questions/ (public)")
    response = requests.get(f"{BASE_URL}/api/items/1/questions/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: POST a question (requires authentication)
    print("\n2. Testing POST /api/items/1/questions/ (auth required)")
    print("   Note: This will fail with 401 if not authenticated")
    
    question_data = {
        "question_text": "What is the condition of this item?"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/items/1/questions/",
        json=question_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: POST an answer (requires item owner authentication)
    print("\n3. Testing POST /api/questions/1/answer/ (owner only)")
    print("   Note: This will fail with 401/403 if not authenticated as owner")
    
    answer_data = {
        "answer_text": "The item is in excellent condition, barely used!"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/1/answer/",
        json=answer_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("\nTo fully test with authentication, use the Django shell or")
    print("authenticate via the web interface and capture session cookies.")

if __name__ == "__main__":
    main()
