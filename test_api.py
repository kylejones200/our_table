#!/usr/bin/env python3
"""
Test the API Ninjas nutrition API directly
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_NINJAS_KEY', '')
API_BASE_URL = "https://api.api-ninjas.com/v1/nutrition"

def test_api():
    if not API_KEY:
        print("❌ No API key found")
        return
    
    headers = {'X-Api-Key': API_KEY}
    
    # Test with a simple query
    test_query = "1 cup butter and 1 cup sugar and 2 cups flour"
    
    print(f"🔍 Testing API with: {test_query}")
    
    try:
        response = requests.get(API_BASE_URL, headers=headers, params={'query': test_query})
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Parsed JSON: {data}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api()
