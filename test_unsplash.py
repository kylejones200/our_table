#!/usr/bin/env python3
"""
Test Unsplash API connection
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Check all possible environment variables
access_key = os.getenv('UNSPLASH_ACCESS_KEY')
app_id = os.getenv('UNSPLASH_APPLICATION_ID')
secret = os.getenv('UNSPLASH_SECRET_KEY')

# Strip quotes if present
if access_key:
    access_key = access_key.strip('"\'')
if app_id:
    app_id = app_id.strip('"\'')
if secret:
    secret = secret.strip('"\'')

print("🔍 Environment Variables:")
print(f"UNSPLASH_ACCESS_KEY: {'✅ Found' if access_key else '❌ Missing'}")
print(f"UNSPLASH_APPLICATION_ID: {'✅ Found' if app_id else '❌ Missing'}")
print(f"UNSPLASH_SECRET_KEY: {'✅ Found' if secret else '❌ Missing'}")
print()

# Test with Application ID (this is usually the correct one for public API)
if app_id:
    print("🧪 Testing API with Application ID...")
    headers = {
        'Authorization': f'Client-ID {app_id}',
        'User-Agent': 'RecipeImageBot/1.0'
    }
    
    try:
        response = requests.get('https://api.unsplash.com/search/photos?query=food&per_page=1', headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API connection successful with Application ID!")
            if data.get('results'):
                photo = data['results'][0]
                print(f"Found photo: {photo.get('alt_description', 'No description')}")
        else:
            print(f"❌ API connection failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test with Access Key as backup
if access_key and access_key != app_id:
    print("\n🧪 Testing API with Access Key...")
    headers = {
        'Authorization': f'Client-ID {access_key}',
        'User-Agent': 'RecipeImageBot/1.0'
    }
    
    try:
        response = requests.get('https://api.unsplash.com/search/photos?query=food&per_page=1', headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API connection successful with Access Key!")
        else:
            print(f"❌ API connection failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
