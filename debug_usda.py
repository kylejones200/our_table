#!/usr/bin/env python3
"""
Debug USDA API responses to see the actual data structure
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

USDA_API_KEY = os.getenv('USDA_KEY') or os.getenv('USDA_API_KEY') or os.getenv('FDC_API_KEY') or ''
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"
USDA_SEARCH_URL = f"{USDA_API_BASE}/foods/search"
USDA_FOOD_URL = f"{USDA_API_BASE}/food"

def debug_food_search():
    # Search for butter
    params = {
        'query': 'butter',
        'dataType': ['Foundation', 'SR Legacy'],
        'pageSize': 1,
        'api_key': USDA_API_KEY
    }
    
    response = requests.get(USDA_SEARCH_URL, params=params)
    data = response.json()
    
    if data.get('foods'):
        food = data['foods'][0]
        print(f"Found food: {food.get('description')}")
        print(f"FDC ID: {food.get('fdcId')}")
        
        # Get detailed nutrition
        food_url = f"{USDA_FOOD_URL}/{food['fdcId']}"
        food_response = requests.get(food_url, params={'api_key': USDA_API_KEY})
        food_data = food_response.json()
        
        print("\nNutrition data structure:")
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients'][:10]:  # Show first 10
                print(f"ID: {nutrient.get('nutrient', {}).get('id')} - "
                      f"Name: {nutrient.get('nutrient', {}).get('name')} - "
                      f"Amount: {nutrient.get('amount')} "
                      f"{nutrient.get('nutrient', {}).get('unitName', '')}")
        else:
            print("No foodNutrients found")
            print("Available keys:", list(food_data.keys()))

if __name__ == "__main__":
    debug_food_search()
