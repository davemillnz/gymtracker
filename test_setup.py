#!/usr/bin/env python3
"""
Test script to verify the StrongLift Tracker setup.
"""

import sys
import importlib

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing package imports...")
    
    packages = [
        'flask',
        'flask_cors', 
        'pandas',
        'matplotlib',
        'io',
        'base64',
        'datetime',
        'json'
    ]
    
    failed = []
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package}: {e}")
            failed.append(package)
    
    if failed:
        print(f"\nFailed to import: {', '.join(failed)}")
        print("Please install missing packages with: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All packages imported successfully!")
        return True

def test_flask_app():
    """Test if the Flask app can be created."""
    print("\nTesting Flask app creation...")
    
    try:
        from app import app
        print("✓ Flask app created successfully")
        
        # Test routes
        routes = ['/', '/api/exercises', '/api/analyze', '/api/weekly-summary']
        for route in routes:
            with app.test_client() as client:
                if route == '/':
                    response = client.get(route)
                else:
                    response = client.post(route)
                
                if response.status_code in [200, 400, 405]:  # 405 = method not allowed
                    print(f"✓ Route {route} accessible")
                else:
                    print(f"⚠ Route {route} returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Flask app: {e}")
        return False

def main():
    print("StrongLift Tracker Setup Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    if not imports_ok:
        sys.exit(1)
    
    flask_ok = test_flask_app()
    if not flask_ok:
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("✓ Setup test completed successfully!")
    print("\nTo run the application:")
    print("1. Local: python3 app.py")
    print("2. Docker: docker-compose up --build")
    print("3. Script: ./run.sh")
    print("\nThen open http://localhost:8080 in your browser")

if __name__ == "__main__":
    main()
