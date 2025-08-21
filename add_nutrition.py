#!/usr/bin/env python3
"""
Add nutrition information to Hugo recipe markdown files using API Ninjas
"""

import json
import os
import re
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Ninjas configuration
API_BASE_URL = "https://api.api-ninjas.com/v1/nutrition"
API_KEY = os.getenv('API_NINJAS_KEY', '')  # Load from .env file

def get_nutrition_data(ingredients_text, api_key):
    """
    Get nutrition data from API Ninjas for given ingredients
    """
    if not api_key:
        print("⚠️  API key not set. Please get your free API key from https://api-ninjas.com/")
        return None
    
    headers = {
        'X-Api-Key': api_key
    }
    
    params = {
        'query': ingredients_text
    }
    
    try:
        response = requests.get(API_BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def parse_ingredients_for_nutrition(ingredients_list):
    """
    Convert ingredients list to a text format suitable for nutrition API
    """
    # Extract just the ingredient names, removing measurements and instructions
    ingredient_texts = []
    
    for ingredient in ingredients_list:
        if ingredient.startswith('---') and ingredient.endswith('---'):
            # Skip section headers
            continue
        
        # Keep the original ingredient with measurements for better API recognition
        # Just clean up obvious non-food words
        cleaned = ingredient.strip()
        
        # Remove preparation instructions but keep measurements and main ingredients
        cleaned = re.sub(r'\b(chopped|sliced|diced|minced|grated|shredded|cooked|raw|fresh|dried|organic|extra|virgin|unsalted|salted|ground|whole|large|medium|small|fine|room temperature|softened|melted|beaten)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if cleaned and len(cleaned) > 3:  # Only include meaningful ingredients
            ingredient_texts.append(cleaned)
    
    # Limit to first 8 ingredients and create a more natural query
    main_ingredients = ingredient_texts[:8]
    return ' and '.join(main_ingredients)

def calculate_total_nutrition(nutrition_data):
    """
    Calculate total nutrition from API response
    """
    if not nutrition_data:
        return None
    
    totals = {
        'carbohydrates_total_g': 0,
        'fat_total_g': 0,
        'fiber_g': 0,
        'sugar_g': 0,
        'sodium_mg': 0
    }
    
    for item in nutrition_data:
        for key in totals.keys():
            if key in item and item[key] is not None:
                try:
                    # Convert to float to handle string numbers
                    value = float(item[key])
                    totals[key] += value
                except (ValueError, TypeError):
                    # Skip invalid values
                    continue
    
    # Round to reasonable precision
    for key in totals:
        if key.endswith('_mg'):
            totals[key] = round(totals[key], 1)
        else:
            totals[key] = round(totals[key], 2)
    
    return totals

def update_recipe_with_nutrition(file_path, nutrition_data):
    """
    Update a recipe markdown file with nutrition information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split front matter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"⚠️  Could not parse front matter in {file_path}")
        return False
    
    front_matter = parts[1]
    body = parts[2]
    
    # Add nutrition data to front matter
    nutrition_yaml = f"""nutrition:
  calories: {nutrition_data['calories']}
  protein_g: {nutrition_data['protein_g']}
  carbohydrates_g: {nutrition_data['carbohydrates_total_g']}
  fat_g: {nutrition_data['fat_total_g']}
  fiber_g: {nutrition_data['fiber_g']}
  sugar_g: {nutrition_data['sugar_g']}
  sodium_mg: {nutrition_data['sodium_mg']}"""
    
    # Insert nutrition data before the closing ---
    updated_content = f"---\n{front_matter.rstrip()}\n{nutrition_yaml}\n---{body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return True

def process_recipes_with_nutrition(api_key, max_recipes=10):
    """
    Process recipe files and add nutrition information
    """
    recipes_dir = Path('content/recipes')
    if not recipes_dir.exists():
        print("❌ Recipes directory not found")
        return
    
    recipe_files = list(recipes_dir.glob('*.md'))
    
    if not recipe_files:
        print("❌ No recipe files found")
        return
    
    print(f"📊 Processing nutrition for {min(len(recipe_files), max_recipes)} recipes...")
    
    processed = 0
    for recipe_file in recipe_files[:max_recipes]:
        print(f"\n🔍 Processing: {recipe_file.name}")
        
        try:
            with open(recipe_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract ingredients from front matter
            if 'ingredients:' not in content:
                print("  ⚠️  No ingredients found, skipping")
                continue
            
            # Parse ingredients
            ingredients_match = re.search(r'ingredients:\s*\n((?:\s*-\s*"[^"]*"\s*\n)*)', content)
            if not ingredients_match:
                print("  ⚠️  Could not parse ingredients, skipping")
                continue
            
            ingredients_text = ingredients_match.group(1)
            ingredients_list = re.findall(r'-\s*"([^"]*)"', ingredients_text)
            
            if not ingredients_list:
                print("  ⚠️  No ingredients found, skipping")
                continue
            
            # Prepare ingredients for API
            nutrition_query = parse_ingredients_for_nutrition(ingredients_list)
            print(f"  🔍 Analyzing: {nutrition_query[:100]}...")
            
            # Get nutrition data
            nutrition_response = get_nutrition_data(nutrition_query, api_key)
            if not nutrition_response:
                print("  ❌ Failed to get nutrition data")
                continue
            
            # Calculate totals
            nutrition_totals = calculate_total_nutrition(nutrition_response)
            if not nutrition_totals:
                print("  ❌ Failed to calculate nutrition totals")
                continue
            
            # Update recipe file
            if update_recipe_with_nutrition(recipe_file, nutrition_totals):
                print(f"  ✅ Added nutrition data: {nutrition_totals['calories']} cal, {nutrition_totals['protein_g']}g protein")
                processed += 1
            else:
                print("  ❌ Failed to update recipe file")
            
            # Rate limiting - be nice to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error processing {recipe_file.name}: {e}")
            continue
    
    print(f"\n✅ Completed! Processed {processed} recipes with nutrition data.")
    print("\n📝 Next steps:")
    print("1. Update your Hugo layouts to display nutrition information")
    print("2. Test the site to ensure nutrition data displays correctly")

def main():
    """
    Main function
    """
    print("🍽️  Recipe Nutrition Enhancer")
    print("=" * 50)
    
    # Check for API key
    api_key = API_KEY or os.getenv('API_NINJAS_KEY')
    
    if not api_key:
        print("\n🔑 API Key Setup Required:")
        print("1. Go to https://api-ninjas.com/ and sign up for a free account")
        print("2. Get your API key from the dashboard")
        print("3. Either:")
        print("   - Set API_KEY variable in this script, or")
        print("   - Set API_NINJAS_KEY environment variable")
        print("\nExample: export API_NINJAS_KEY='your-api-key-here'")
        return
    
    # Process a small batch first for testing
    process_recipes_with_nutrition(api_key, max_recipes=5)

if __name__ == "__main__":
    main()
