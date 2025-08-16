#!/usr/bin/env python3
"""
Simple test script to verify the Flask backend works correctly.
"""

import requests
import json

def test_backend():
    base_url = "http://localhost:8080"
    
    print("Testing StrongLift Tracker Backend...")
    print("=" * 40)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Server is running (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Please start the Flask app first.")
        return False
    
    # Test 2: Check API endpoints exist
    endpoints = ["/api/exercises", "/api/analyze", "/api/weekly-summary"]
    for endpoint in endpoints:
        try:
            response = requests.post(f"{base_url}{endpoint}")
            # Should get 400 (no file) but endpoint exists
            if response.status_code in [400, 405]:
                print(f"✓ Endpoint {endpoint} exists")
            else:
                print(f"⚠ Endpoint {endpoint} returned unexpected status: {response.status_code}")
        except Exception as e:
            print(f"✗ Error testing {endpoint}: {e}")
    
    print("\nBackend tests completed!")
    print("\nTo test with real data:")
    print("1. Start the Flask app: python app.py")
    print("2. Open http://localhost:8080 in your browser")
    print("3. Upload a CSV file from the Strong app")
    
    return True

if __name__ == "__main__":
    test_backend()
