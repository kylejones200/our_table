#!/usr/bin/env python3
"""
Add nutrition information to Hugo recipe markdown files using Open Food Facts API
Completely free, no API key required!
"""

import json
import os
import re
import requests
import time
from pathlib import Path

# Open Food Facts API configuration
OPENFOOD_API_BASE = "https://world.openfoodfacts.org/api/v2"
OPENFOOD_SEARCH_URL = f"{OPENFOOD_API_BASE}/search"

def search_food_openfood(food_name):
    """
    Search for a food item in Open Food Facts database
    """
    params = {
        'search_terms': food_name,
        'search_simple': 1,
        'action': 'process',
        'json': 1,
        'page_size': 5,
        'fields': 'product_name,nutriments,brands'
    }
    
    headers = {
        'User-Agent': 'RecipeNutritionBot/1.0 (https://github.com/your-repo)'
    }
    
    try:
        response = requests.get(OPENFOOD_SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get('products'):
            # Find best match with nutrition data
            for product in data['products']:
                if product.get('nutriments') and product['nutriments'].get('energy-kcal_100g'):
                    return product
        return None
    except requests.exceptions.RequestException as e:
        print(f"Open Food Facts API search failed for '{food_name}': {e}")
        return None

def extract_nutrition_openfood(product):
    """
    Extract nutrition values from Open Food Facts product data
    """
    nutrition = {
        'calories': 0,
        'protein_g': 0,
        'carbohydrates_g': 0,
        'fat_g': 0,
        'fiber_g': 0,
        'sugar_g': 0
    }
    
    if not product or 'nutriments' not in product:
        return nutrition
    
    nutriments = product['nutriments']
    
    # Map Open Food Facts nutrient keys to our format
    nutrient_map = {
        'energy-kcal_100g': 'calories',
        'proteins_100g': 'protein_g',
        'carbohydrates_100g': 'carbohydrates_g',
        'fat_100g': 'fat_g',
        'fiber_100g': 'fiber_g',
        'sugars_100g': 'sugar_g'
    }
    
    for off_key, our_key in nutrient_map.items():
        if off_key in nutriments and nutriments[off_key]:
            try:
                nutrition[our_key] = round(float(nutriments[off_key]), 2)
            except (ValueError, TypeError):
                continue
    
    return nutrition

def estimate_nutrition_simple(ingredient):
    """
    Simple nutrition estimation for common ingredients when API fails
    """
    # Basic nutrition estimates per 100g for common ingredients
    estimates = {
        'butter': {'calories': 717, 'protein_g': 0.9, 'carbohydrates_g': 0.1, 'fat_g': 81, 'fiber_g': 0, 'sugar_g': 0.1},
        'sugar': {'calories': 387, 'protein_g': 0, 'carbohydrates_g': 100, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 100},
        'flour': {'calories': 364, 'protein_g': 10, 'carbohydrates_g': 76, 'fat_g': 1, 'fiber_g': 3, 'sugar_g': 0.3},
        'eggs': {'calories': 155, 'protein_g': 13, 'carbohydrates_g': 1.1, 'fat_g': 11, 'fiber_g': 0, 'sugar_g': 1.1},
        'milk': {'calories': 42, 'protein_g': 3.4, 'carbohydrates_g': 5, 'fat_g': 1, 'fiber_g': 0, 'sugar_g': 5},
        'cheese': {'calories': 113, 'protein_g': 7, 'carbohydrates_g': 1, 'fat_g': 9, 'fiber_g': 0, 'sugar_g': 1},
        'chicken': {'calories': 239, 'protein_g': 27, 'carbohydrates_g': 0, 'fat_g': 14, 'fiber_g': 0, 'sugar_g': 0},
        'beef': {'calories': 250, 'protein_g': 26, 'carbohydrates_g': 0, 'fat_g': 15, 'fiber_g': 0, 'sugar_g': 0},
        'oil': {'calories': 884, 'protein_g': 0, 'carbohydrates_g': 0, 'fat_g': 100, 'fiber_g': 0, 'sugar_g': 0},
        'onion': {'calories': 40, 'protein_g': 1.1, 'carbohydrates_g': 9.3, 'fat_g': 0.1, 'fiber_g': 1.7, 'sugar_g': 4.2},
        'garlic': {'calories': 149, 'protein_g': 6.4, 'carbohydrates_g': 33, 'fat_g': 0.5, 'fiber_g': 2.1, 'sugar_g': 1},
        'tomato': {'calories': 18, 'protein_g': 0.9, 'carbohydrates_g': 3.9, 'fat_g': 0.2, 'fiber_g': 1.2, 'sugar_g': 2.6}
    }
    
    ingredient_lower = ingredient.lower()
    for key, values in estimates.items():
        if key in ingredient_lower:
            return values
    
    return None

def parse_ingredient_for_search(ingredient):
    """
    Clean ingredient text for search
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
        
        # Try Open Food Facts API first
        product = search_food_openfood(cleaned_ingredient)
        ingredient_nutrition = None
        
        if product:
            ingredient_nutrition = extract_nutrition_openfood(product)
            print(f"    ✅ Found in Open Food Facts: {product.get('product_name', 'Unknown')} - {ingredient_nutrition['calories']} cal")
        else:
            # Fallback to simple estimation
            ingredient_nutrition = estimate_nutrition_simple(cleaned_ingredient)
            if ingredient_nutrition:
                print(f"    📊 Using estimate for: {cleaned_ingredient} - {ingredient_nutrition['calories']} cal")
        
        if ingredient_nutrition and ingredient_nutrition['calories'] > 0:
            # Add to totals (scaled down since we're estimating)
            scale_factor = 0.3  # Assume smaller portions
            for key in total_nutrition:
                total_nutrition[key] += ingredient_nutrition[key] * scale_factor
            found_ingredients += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    # Round final values
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)
    
    print(f"  📊 Found nutrition data for {found_ingredients} ingredients")
    return total_nutrition if found_ingredients > 0 else None

def update_recipe_with_nutrition(file_path, nutrition_data):
    """
    Update a recipe markdown file with nutrition information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any existing nutrition data
    content = re.sub(r'nutrition:\s*\n(?:\s+[^\n]+\n)*', '', content)
    
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
  carbohydrates_g: {nutrition_data['carbohydrates_g']}
  fat_g: {nutrition_data['fat_g']}
  fiber_g: {nutrition_data['fiber_g']}
  sugar_g: {nutrition_data['sugar_g']}"""
    
    # Insert nutrition data before the closing ---
    updated_content = f"---\n{front_matter.rstrip()}\n{nutrition_yaml}\n---{body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return True

def process_recipes_with_nutrition(max_recipes=5):
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
    
    print(f"🍽️  Open Food Facts Nutrition Enhancer")
    print("=" * 50)
    print(f"📊 Processing nutrition for {min(len(recipe_files), max_recipes)} recipes...")
    print("🆓 Using Open Food Facts API + Smart Estimates - completely FREE!")
    
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
            
            # Get nutrition data
            nutrition_data = get_recipe_nutrition(ingredients_list)
            if not nutrition_data:
                print("  ❌ Could not get nutrition data")
                continue
            
            # Update recipe file
            if update_recipe_with_nutrition(recipe_file, nutrition_data):
                print(f"  ✅ Added nutrition: {nutrition_data['calories']} cal, {nutrition_data['protein_g']}g protein, {nutrition_data['carbohydrates_g']}g carbs, {nutrition_data['fat_g']}g fat")
                processed += 1
            else:
                print("  ❌ Failed to update recipe file")
            
        except Exception as e:
            print(f"  ❌ Error processing {recipe_file.name}: {e}")
            continue
    
    print(f"\n✅ Completed! Processed {processed} recipes with nutrition data.")
    print("\n📝 Benefits of this approach:")
    print("• 100% FREE - No API key required")
    print("• Complete nutrition data - calories, protein, carbs, fat, fiber, sugar")
    print("• Open Food Facts API + smart fallback estimates")
    print("• Works for common ingredients")

def main():
    """
    Main function
    """
    print("🍽️  Open Food Facts Nutrition Enhancer")
    print("=" * 50)
    print("🆓 Using Open Food Facts API + Smart Estimates - completely FREE!")
    print("📊 No API key required")
    
    # Process a small batch first for testing
    process_recipes_with_nutrition(max_recipes=3)

if __name__ == "__main__":
    main()
