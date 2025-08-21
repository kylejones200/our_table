#!/usr/bin/env python3
"""
Add nutrition information to Hugo recipe markdown files using USDA FoodData Central API
Free, no API key required.
"""

import json
import os
import re
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# USDA FoodData Central API configuration
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"
USDA_SEARCH_URL = f"{USDA_API_BASE}/foods/search"
USDA_FOOD_URL = f"{USDA_API_BASE}/food"
USDA_API_KEY = os.getenv('USDA_KEY') or os.getenv('USDA_API_KEY') or os.getenv('FDC_API_KEY') or ''

def search_food_usda(food_name):
    """
    Search for a food item in USDA database
    """
    params = {
        'query': food_name,
        'dataType': ['Foundation', 'SR Legacy'],
        'pageSize': 5,
        'sortBy': 'dataType.keyword',
        'sortOrder': 'asc',
        'api_key': USDA_API_KEY
    }
    
    try:
        response = requests.get(USDA_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('foods'):
            return data['foods'][0]
        return None
    except requests.exceptions.RequestException as e:
        print(f"USDA API search failed for '{food_name}': {e}")
        return None

def get_nutrition_usda(fdc_id):
    """
    Get detailed nutrition data for a specific food ID
    """
    url = f"{USDA_FOOD_URL}/{fdc_id}"
    params = {'api_key': USDA_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"USDA API nutrition failed for ID {fdc_id}: {e}")
        return None

def extract_nutrition_values(food_data):
    """
    Extract nutrition values from USDA food data
    """
    nutrition = {
        'calories': 0,
        'protein_g': 0,
        'carbohydrates_g': 0,
        'fat_g': 0,
        'fiber_g': 0,
        'sugar_g': 0
    }
    
    if not food_data or 'foodNutrients' not in food_data:
        return nutrition
    
    # USDA nutrient ID mapping (correct IDs from API)
    nutrient_map = {
        1008: 'calories',      # Energy (kcal)
        1003: 'protein_g',     # Protein
        1005: 'carbohydrates_g', # Carbohydrate, by difference
        1004: 'fat_g',         # Total lipid (fat)
        1079: 'fiber_g',       # Fiber, total dietary
        2000: 'sugar_g'        # Sugars, total including NLEA
    }
    
    for nutrient in food_data['foodNutrients']:
        nutrient_id = nutrient.get('nutrient', {}).get('id')
        if nutrient_id in nutrient_map:
            key = nutrient_map[nutrient_id]
            value = nutrient.get('amount', 0)
            if value:
                nutrition[key] = round(float(value), 2)
    
    return nutrition

def parse_ingredient_for_search(ingredient):
    """
    Clean ingredient text for USDA search
    """
    # Remove measurements and common descriptors
    cleaned = re.sub(r'\b\d+[\d\s/]*\b', '', ingredient)
    cleaned = re.sub(r'\b(cup|cups|tablespoon|tablespoons|tbsp|teaspoon|teaspoons|tsp|pound|pounds|lb|lbs|ounce|ounces|oz|gram|grams|g|kilogram|kg)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(chopped|sliced|diced|minced|grated|shredded|cooked|raw|fresh|dried|organic|extra|virgin|unsalted|salted|ground|whole|large|medium|small|fine|room temperature|softened|melted|beaten)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def get_recipe_nutrition(ingredients_list):
    """
    Calculate total nutrition for a recipe from ingredients
    """
    total_nutrition = {
        'calories': 0,
        'protein_g': 0,
        'carbohydrates_g': 0,
        'fat_g': 0,
        'fiber_g': 0,
        'sugar_g': 0
    }
    
    found_ingredients = 0
    
    for ingredient in ingredients_list[:8]:
        if ingredient.startswith('---') and ingredient.endswith('---'):
            continue
            
        cleaned_ingredient = parse_ingredient_for_search(ingredient)
        if len(cleaned_ingredient) < 3:
            continue
            
        print(f"  🔍 Searching: {cleaned_ingredient}")
        
        # Search for the ingredient
        food_item = search_food_usda(cleaned_ingredient)
        if not food_item:
            continue
            
        # Get detailed nutrition
        nutrition_data = get_nutrition_usda(food_item['fdcId'])
        if not nutrition_data:
            continue
            
        # Extract nutrition values
        ingredient_nutrition = extract_nutrition_values(nutrition_data)
        
        # Add to totals (assuming 100g serving for estimation)
        for key in total_nutrition:
            total_nutrition[key] += ingredient_nutrition[key]
        
        found_ingredients += 1
        print(f"    ✅ Found: {food_item.get('description', 'Unknown')} - {ingredient_nutrition['calories']} cal")
        
        # Rate limiting
        time.sleep(0.5)
    
    # Round final values
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)
    
    print(f"  📊 Found nutrition data for {found_ingredients} ingredients")
    return total_nutrition if found_ingredients > 0 else None

def extract_servings_from_recipe(content):
    """
    Extract the number of servings from recipe front matter
    """
    # Look for yield field
    yield_match = re.search(r'yield:\s*"([^"]*)"', content)
    if yield_match:
        yield_text = yield_match.group(1).lower()
        # Extract numbers from yield text
        numbers = re.findall(r'\d+', yield_text)
        if numbers:
            return int(numbers[0])
    
    # Default to 4 servings if not found
    return 4

def update_recipe_with_nutrition(file_path, nutrition_data):
    """
    Update a recipe markdown file with nutrition information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract servings to calculate per-serving nutrition
    servings = extract_servings_from_recipe(content)
    
    # Calculate per-serving nutrition
    per_serving_nutrition = {}
    for key, value in nutrition_data.items():
        per_serving_nutrition[key] = round(value / servings, 1)
    
    # Remove any existing nutrition data
    content = re.sub(r'nutrition:\s*\n(?:\s+[^\n]+\n)*', '', content)
    
    # Split front matter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"⚠️  Could not parse front matter in {file_path}")
        return False
    
    front_matter = parts[1]
    body = parts[2]
    
    # Add nutrition data to front matter (per serving)
    nutrition_yaml = f"""nutrition:
  calories: {per_serving_nutrition['calories']}
  protein_g: {per_serving_nutrition['protein_g']}
  carbohydrates_g: {per_serving_nutrition['carbohydrates_g']}
  fat_g: {per_serving_nutrition['fat_g']}
  fiber_g: {per_serving_nutrition['fiber_g']}
  sugar_g: {per_serving_nutrition['sugar_g']}
  servings: {servings}"""
    
    # Insert nutrition data before the closing ---
    updated_content = f"---\n{front_matter.rstrip()}\n{nutrition_yaml}\n---{body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return per_serving_nutrition, servings

def process_recipes_with_usda_nutrition(max_recipes=5):
    """
    Process recipe files and add USDA nutrition information
    """
    recipes_dir = Path('content/recipes')
    if not recipes_dir.exists():
        print("❌ Recipes directory not found")
        return
    
    recipe_files = list(recipes_dir.glob('*.md'))
    
    if not recipe_files:
        print("❌ No recipe files found")
        return
    
    print(f"🍽️  USDA Nutrition Enhancer")
    print("=" * 50)
    print(f"📊 Processing nutrition for {min(len(recipe_files), max_recipes)} recipes...")
    print("🆓 Using USDA FoodData Central - completely FREE!")
    
    processed = 0
    for recipe_file in recipe_files[:max_recipes]:
        print(f"\n🔍 Processing: {recipe_file.name}")
        
        try:
            with open(recipe_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip recipes that already have nutrition data
            if 'nutrition:' in content and 'calories:' in content:
                print("  ✅ Already has nutrition data, skipping")
                continue
            
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
            
            # Get nutrition data from USDA
            nutrition_data = get_recipe_nutrition(ingredients_list)
            if not nutrition_data:
                print(f"  ⚠️  No nutrition data found for {recipe_file.name}")
                continue

            result = update_recipe_with_nutrition(recipe_file, nutrition_data)
            if result:
                per_serving_nutrition, servings = result
                print(f"  ✅ Added nutrition (per serving, {servings} servings): {per_serving_nutrition['calories']} cal, {per_serving_nutrition['protein_g']}g protein, {per_serving_nutrition['carbohydrates_g']}g carbs, {per_serving_nutrition['fat_g']}g fat")
                processed += 1
            else:
                print(f"  ❌ Failed to update {recipe_file}")

        except Exception as e:
            print(f"  ❌ Error processing {recipe_file.name}: {e}")
            continue

    print(f"\n✅ Completed! Processed {processed} recipes with USDA nutrition data.")
    print("\n📝 Benefits of USDA FoodData Central:")
    print("• 100% FREE - No API key required")
    print("• Complete nutrition data - calories, protein, carbs, fat, fiber, sugar")
    print("• Government-backed accuracy")
    print("• 900,000+ foods in database")

def main():
    """
    Main function
    """
    print("🍽️  USDA Nutrition Enhancer")
    print("=" * 50)
    
    if not USDA_API_KEY:
        print("❌ USDA API key not found in .env file")
        print("📝 Please add USDA_KEY=your-api-key to your .env file")
        print("🔗 Get your free key at: https://fdc.nal.usda.gov/api-guide.html")
        return
    
    print("🆓 Using USDA FoodData Central API with your API key!")
    print("📊 Government-backed nutrition data")
    
    # Process a small batch first for testing
    process_recipes_with_usda_nutrition(max_recipes=368)

if __name__ == "__main__":
    main()
