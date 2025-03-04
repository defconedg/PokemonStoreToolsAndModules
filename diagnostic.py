"""
Diagnostic tool to check setup and configuration
"""
import os
import sys
import requests
import json
import subprocess
from dotenv import load_dotenv

def check_python_version():
    print(f"Python Version: {sys.version}")
    if sys.version_info < (3, 6):
        print("⚠️ WARNING: Python 3.6 or higher is recommended")
    else:
        print("✅ Python version is good")
    print()

def check_dependencies():
    print("Checking required packages...")
    required = [
        "flask", "requests", "python-dotenv", "flask-cors", "beautifulsoup4"
    ]
    
    all_installed = True
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\nSome packages are missing. Install them with:")
        print("pip install -r requirements.txt")
    
    print()

def check_env_variables():
    print("Checking environment variables...")
    load_dotenv()
    
    poke_api_key = os.getenv('POKE_API_KEY')
    if poke_api_key:
        print("✅ POKE_API_KEY is set")
    else:
        print("❌ POKE_API_KEY is not set - this is required")
        
    pricecharting_api_key = os.getenv('PRICECHARTING_API_KEY')
    if pricecharting_api_key:
        print("✅ PRICECHARTING_API_KEY is set")
    else:
        print("⚠️ PRICECHARTING_API_KEY is not set - optional but recommended")
    
    print()
    
def check_api_access():
    print("Testing API access...")
    poke_api_key = os.getenv('POKE_API_KEY')
    
    if not poke_api_key:
        print("❌ Cannot test API access: No POKE_API_KEY found")
        return
        
    try:
        response = requests.get(
            'https://api.pokemontcg.io/v2/sets',
            headers={'X-Api-Key': poke_api_key}
        )
        
        if response.status_code == 200:
            print("✅ Successfully connected to Pokemon TCG API")
            data = response.json()
            print(f"  Found {len(data.get('data', []))} sets")
        else:
            print(f"❌ Failed to connect to Pokemon TCG API: Status {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing API access: {str(e)}")
    
    print()

def check_flask_app():
    print("Checking Flask app...")
    if not os.path.exists("app.py"):
        print("❌ app.py not found in current directory")
        return
        
    if not os.path.exists("templates/index.html"):
        print("❌ templates/index.html not found - Flask may not serve the frontend correctly")
    else:
        print("✅ templates/index.html found")
    
    # Check if app.py contains the right imports
    with open("app.py", "r") as f:
        content = f.read()
        if "from flask import" not in content:
            print("❌ app.py doesn't seem to be a Flask application")
        else:
            print("✅ app.py appears to be a valid Flask application")
    
    print()

def check_network():
    print("Checking network connectivity...")
    try:
        response = requests.get("https://api.pokemontcg.io")
        print(f"✅ Can reach pokemontcg.io: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach pokemontcg.io: {str(e)}")
    
    try:
        response = requests.get("https://www.pricecharting.com")
        print(f"✅ Can reach pricecharting.com: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach pricecharting.com: {str(e)}")
    
    print()

if __name__ == "__main__":
    print("=========================================")
    print("Pokemon Store Tools Diagnostic Check")
    print("=========================================")
    print()
    
    check_python_version()
    check_dependencies()
    check_env_variables()
    check_api_access()
    check_flask_app()
    check_network()
    
    print("Diagnostic complete!")
    print()
    print("If you're having trouble:")
    print("1. Make sure the Flask server is running (python app.py)")
    print("2. Ensure your API keys are correctly set in .env")
    print("3. Access the web interface at: http://127.0.0.1:5000")
    print("4. Check your browser console for any JavaScript errors")
    print()
    
    input("Press Enter to exit...")
