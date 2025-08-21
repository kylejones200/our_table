#!/usr/bin/env python3
"""
Add recipe images to Hugo recipe markdown files using Unsplash API
Free tier: 50 requests/hour
"""

import os
import re
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Unsplash API configuration
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY') or os.getenv('UNSPLASH_APPLICATION_ID')
if UNSPLASH_ACCESS_KEY:
    UNSPLASH_ACCESS_KEY = UNSPLASH_ACCESS_KEY.strip('"\'')  # Remove quotes if present
UNSPLASH_API_BASE = "https://api.unsplash.com"

def search_recipe_image(recipe_title, categories=None):
    """
    Search for a recipe image on Unsplash
    """
    if not UNSPLASH_ACCESS_KEY:
        print("❌ UNSPLASH_ACCESS_KEY not found in .env file")
        return None
    
    # Create search query from recipe title and categories
    search_terms = []
    
    # Clean up recipe title for search
    clean_title = re.sub(r'[^\w\s-]', '', recipe_title.lower())
    search_terms.append(clean_title)
    
    # Add food-related keywords
    search_terms.append("food")
    
    # Add category if available
    if categories:
        if isinstance(categories, list) and categories:
            search_terms.append(categories[0])
        elif isinstance(categories, str):
            search_terms.append(categories)
    
    query = " ".join(search_terms[:3])  # Limit to 3 terms
    
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}',
        'User-Agent': 'RecipeImageBot/1.0'
    }
    
    params = {
        'query': query,
        'per_page': 3,
        'orientation': 'landscape',
        'content_filter': 'high'
    }
    
    try:
        response = requests.get(f"{UNSPLASH_API_BASE}/search/photos", 
                              headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            # Return the best match
            photo = data['results'][0]
            return {
                'url': photo['urls']['regular'],
                'thumb_url': photo['urls']['small'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'photo_url': photo['links']['html'],
                'alt_text': photo.get('alt_description', recipe_title)
            }
        
        return None
        
    except requests.RequestException as e:
        print(f"❌ Error searching Unsplash: {e}")
        return None

def get_food_emoji_fallback(categories):
    """
    Get a food emoji based on recipe categories as fallback
    """
    emoji_map = {
        'dessert': '🍰',
        'cake': '🎂', 
        'cookie': '🍪',
        'bread': '🍞',
        'pasta': '🍝',
        'pizza': '🍕',
        'soup': '🍲',
        'salad': '🥗',
        'meat': '🥩',
        'chicken': '🍗',
        'fish': '🐟',
        'seafood': '🦐',
        'vegetable': '🥕',
        'fruit': '🍎',
        'breakfast': '🥞',
        'lunch': '🥪',
        'dinner': '🍽️',
        'snack': '🍿',
        'beverage': '🥤',
        'cocktail': '🍹'
    }
    
    if categories:
        if isinstance(categories, list):
            for category in categories:
                if category.lower() in emoji_map:
                    return emoji_map[category.lower()]
        elif isinstance(categories, str) and categories.lower() in emoji_map:
            return emoji_map[categories.lower()]
    
    return '🍽️'  # Default food emoji

def extract_recipe_metadata(content):
    """
    Extract title and categories from recipe markdown content
    """
    # Extract title
    title_match = re.search(r'title:\s*["\']([^"\']*)["\']', content)
    title = title_match.group(1) if title_match else "Recipe"
    
    # Extract categories
    categories_match = re.search(r'categories:\s*\n((?:\s*-\s*["\'][^"\']*["\']\s*\n)*)', content, re.MULTILINE)
    categories = []
    if categories_match:
        categories_text = categories_match.group(1)
        categories = re.findall(r'-\s*["\']([^"\']*)["\']', categories_text)
    
    return title, categories

def update_recipe_with_image(file_path, image_data=None, emoji_fallback=None):
    """
    Update a recipe markdown file with image information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any existing image data
    content = re.sub(r'image:\s*["\'][^"\']*["\']\s*\n', '', content)
    content = re.sub(r'image_credit:\s*["\'][^"\']*["\']\s*\n', '', content)
    content = re.sub(r'image_emoji:\s*["\'][^"\']*["\']\s*\n', '', content)
    
    # Split front matter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"⚠️  Could not parse front matter in {file_path}")
        return False
    
    front_matter = parts[1]
    body = parts[2]
    
    # Add image data to front matter
    image_yaml = ""
    if image_data:
        image_yaml = f'image: "{image_data["url"]}"\n'
        image_yaml += f'image_credit: "Photo by {image_data["photographer"]} on Unsplash"\n'
    elif emoji_fallback:
        image_yaml = f'image_emoji: "{emoji_fallback}"\n'
    
    # Insert image data before the closing ---
    updated_content = f"---\n{front_matter.rstrip()}\n{image_yaml}---{body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return True

def validate_recipe_file(content):
    """
    Validate that a recipe file has proper structure and ingredients
    """
    # Check if file has ingredients section
    if 'ingredients:' not in content.lower():
        return False, "No ingredients section found"
    
    # Check if file already has an image
    if 'image:' in content or 'image_emoji:' in content:
        return False, "Already has image"
    
    # Check for basic recipe structure
    if '---' not in content:
        return False, "No front matter found"
    
    # Extract ingredients to validate they exist and are not empty
    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False, "Malformed front matter"
        
        front_matter = parts[1].lower()
        
        # Look for ingredients section in front matter
        if 'ingredients:' in front_matter:
            # Find ingredients section
            lines = front_matter.split('\n')
            in_ingredients = False
            ingredient_count = 0
            
            for line in lines:
                line = line.strip()
                if line.startswith('ingredients:'):
                    in_ingredients = True
                    continue
                elif in_ingredients:
                    if line.startswith('-') or line.startswith('*'):
                        ingredient_count += 1
                    elif line and not line.startswith(' ') and ':' in line:
                        # Hit next section
                        break
            
            if ingredient_count == 0:
                return False, "No ingredients listed"
        
        return True, "Valid recipe"
        
    except Exception as e:
        return False, f"Error parsing: {e}"

def process_recipes_with_images(max_recipes=10, use_api=True):
    """
    Process recipe files and add image information
    """
    recipes_dir = Path('content/recipes')
    if not recipes_dir.exists():
        print("❌ Recipes directory not found")
        return
    
    recipe_files = list(recipes_dir.glob('*.md'))
    processed = 0
    api_calls = 0
    skipped = 0
    
    print(f"🖼️  Processing images for up to {max_recipes} recipes...")
    if use_api and UNSPLASH_ACCESS_KEY:
        print("📸 Using Unsplash API (50 requests/hour limit)")
    else:
        print("🎭 Using emoji fallbacks (no API required)")
    print()
    
    for recipe_file in recipe_files:
        if processed >= max_recipes:
            break
            
        try:
            print(f"🖼️  Processing: {recipe_file.name}")
            
            with open(recipe_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validate recipe file first
            is_valid, reason = validate_recipe_file(content)
            if not is_valid:
                print(f"  ⏭️  Skipping: {reason}")
                skipped += 1
                continue
            
            # Extract recipe metadata
            title, categories = extract_recipe_metadata(content)
            
            image_data = None
            emoji_fallback = None
            
            # Try Unsplash API first (if enabled and under rate limit)
            if use_api and UNSPLASH_ACCESS_KEY and api_calls < 45:  # Leave buffer for rate limit
                image_data = search_recipe_image(title, categories)
                api_calls += 1
                time.sleep(1.2)  # Rate limiting: 50/hour = ~1.2s between calls
                
                if image_data:
                    print(f"  📸 Found image by {image_data['photographer']}")
                else:
                    print(f"  🎭 No image found, using emoji fallback")
                    emoji_fallback = get_food_emoji_fallback(categories)
            else:
                # Use emoji fallback
                emoji_fallback = get_food_emoji_fallback(categories)
                print(f"  🎭 Using emoji: {emoji_fallback}")
            
            # Update recipe file
            if update_recipe_with_image(recipe_file, image_data, emoji_fallback):
                processed += 1
            else:
                print(f"  ❌ Failed to update {recipe_file}")
                
        except Exception as e:
            print(f"  ❌ Error processing {recipe_file.name}: {e}")
            continue
    
    print(f"\n✅ Completed! Processed {processed} recipes with images.")
    print(f"⏭️  Skipped {skipped} recipes (already have images or invalid)")
    print(f"📊 API calls used: {api_calls}/50 (hourly limit)")
    
    if not UNSPLASH_ACCESS_KEY:
        print("\n💡 To use Unsplash images:")
        print("1. Get free API key: https://unsplash.com/developers")
        print("2. Add to .env file: UNSPLASH_ACCESS_KEY=your_key_here")
        print("3. Run script again")

def main():
    """
    Main function
    """
    print("🖼️  Recipe Image Processor")
    print("=" * 50)
    print("📸 Unsplash API + 🎭 Emoji fallbacks")
    
    # Check if API key is available
    use_api = bool(UNSPLASH_ACCESS_KEY)
    
    # Process all recipes (respecting API limits)
    process_recipes_with_images(max_recipes=45, use_api=use_api)  # Stay under 50/hour limit

if __name__ == "__main__":
    main()
