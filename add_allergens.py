#!/usr/bin/env python3
"""
Add allergen information to Hugo recipe markdown files
Uses rule-based detection on ingredients
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Common allergen patterns
ALLERGEN_PATTERNS = {
    'gluten': [
        r'\bwheat\b', r'\bflour\b', r'\bbread\b', r'\bpasta\b', r'\bnoodles\b',
        r'\bbarley\b', r'\brye\b', r'\boats\b', r'\boat\b', r'\bsoy sauce\b',
        r'\bbeer\b', r'\bmalt\b', r'\bseitan\b', r'\bbiscuit\b', r'\bcookie\b',
        r'\bcake\b', r'\bcracker\b', r'\bpie crust\b', r'\btortilla\b'
    ],
    'dairy': [
        r'\bmilk\b', r'\bcheese\b', r'\bbutter\b', r'\bcream\b', r'\byogurt\b',
        r'\bsour cream\b', r'\bcream cheese\b', r'\bparmesan\b', r'\bcheddar\b',
        r'\bmozzarella\b', r'\bricotta\b', r'\bwhey\b', r'\bcasein\b',
        r'\blactose\b', r'\bice cream\b', r'\bhalf and half\b'
    ],
    'eggs': [
        r'\begg\b', r'\beggs\b', r'\begg white\b', r'\begg yolk\b', r'\bmayonnaise\b',
        r'\bmayo\b', r'\bmeringue\b', r'\bcustard\b', r'\bhollandaise\b'
    ],
    'nuts': [
        r'\balmond\b', r'\bwalnut\b', r'\bpecan\b', r'\bpeanut\b', r'\bcashew\b',
        r'\bpistachio\b', r'\bhazelnut\b', r'\bmacadamia\b', r'\bbrazil nut\b',
        r'\bpine nut\b', r'\bnut\b', r'\bnuts\b', r'\bpeanut butter\b',
        r'\balmond butter\b', r'\bnutella\b', r'\bmarzipan\b'
    ],
    'soy': [
        r'\bsoy\b', r'\btofu\b', r'\bsoy sauce\b', r'\bmiso\b', r'\btempeh\b',
        r'\bedamame\b', r'\bsoybean\b', r'\bsoy milk\b', r'\bsoy protein\b'
    ],
    'shellfish': [
        r'\bshrimp\b', r'\bcrab\b', r'\blobster\b', r'\bscallop\b', r'\bclam\b',
        r'\bmussel\b', r'\boyster\b', r'\bcrawfish\b', r'\bprawn\b'
    ],
    'fish': [
        r'\bsalmon\b', r'\btuna\b', r'\bcod\b', r'\bhalibut\b', r'\bmahi\b',
        r'\btilapia\b', r'\banchovies\b', r'\bsardines\b', r'\bfish\b',
        r'\bseabass\b', r'\btrout\b', r'\bmackerel\b'
    ],
    'sesame': [
        r'\bsesame\b', r'\btahini\b', r'\bsesame oil\b', r'\bsesame seeds\b'
    ]
}

def detect_allergens_in_ingredients(ingredients_list):
    """
    Detect allergens in a list of ingredients using pattern matching
    """
    detected_allergens = set()
    
    # Combine all ingredients into one text for analysis
    ingredients_text = ' '.join(ingredients_list).lower()
    
    for allergen, patterns in ALLERGEN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, ingredients_text, re.IGNORECASE):
                detected_allergens.add(allergen)
                break  # Found this allergen, move to next
    
    return sorted(list(detected_allergens))

def extract_ingredients_from_recipe(content):
    """
    Extract ingredients list from recipe markdown content
    """
    # Look for ingredients section in YAML front matter
    ingredients_match = re.search(r'ingredients:\s*\n((?:\s*-\s*"[^"]*"\s*\n)*)', content, re.MULTILINE)
    if ingredients_match:
        ingredients_text = ingredients_match.group(1)
        ingredients_list = re.findall(r'-\s*"([^"]*)"', ingredients_text)
        return ingredients_list
    return []

def update_recipe_with_allergens(file_path, allergens):
    """
    Update a recipe markdown file with allergen information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any existing allergen data
    content = re.sub(r'allergens:\s*\[.*?\]\s*\n', '', content)
    
    # Split front matter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"⚠️  Could not parse front matter in {file_path}")
        return False
    
    front_matter = parts[1]
    body = parts[2]
    
    # Add allergen data to front matter
    if allergens:
        allergens_yaml = f"allergens: {allergens}\n"
    else:
        allergens_yaml = "allergens: []\n"
    
    # Insert allergen data before the closing ---
    updated_content = f"---\n{front_matter.rstrip()}\n{allergens_yaml}---{body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return True

def process_recipes_with_allergens(max_recipes=10):
    """
    Process recipe files and add allergen information
    """
    recipes_dir = Path('content/recipes')
    if not recipes_dir.exists():
        print("❌ Recipes directory not found")
        return
    
    recipe_files = list(recipes_dir.glob('*.md'))[:max_recipes]
    processed = 0
    
    print(f"🔍 Processing allergens for {len(recipe_files)} recipes...")
    print("🥜 Detecting: gluten, dairy, eggs, nuts, soy, shellfish, fish, sesame")
    print()
    
    for recipe_file in recipe_files:
        try:
            print(f"🔍 Processing: {recipe_file.name}")
            
            with open(recipe_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract ingredients
            ingredients_list = extract_ingredients_from_recipe(content)
            if not ingredients_list:
                print("  ⚠️  No ingredients found, skipping")
                continue
            
            # Detect allergens
            allergens = detect_allergens_in_ingredients(ingredients_list)
            
            # Update recipe file
            if update_recipe_with_allergens(recipe_file, allergens):
                if allergens:
                    allergen_str = ', '.join(allergens)
                    print(f"  ✅ Added allergens: {allergen_str}")
                else:
                    print(f"  ✅ No allergens detected")
                processed += 1
            else:
                print(f"  ❌ Failed to update {recipe_file}")
                
        except Exception as e:
            print(f"  ❌ Error processing {recipe_file.name}: {e}")
            continue
    
    print(f"\n✅ Completed! Processed {processed} recipes with allergen detection.")
    print("\n📝 Detected allergens:")
    print("• Gluten (wheat, flour, bread, pasta, oats, etc.)")
    print("• Dairy (milk, cheese, butter, cream, yogurt, etc.)")
    print("• Eggs (eggs, mayonnaise, custard, etc.)")
    print("• Nuts (almonds, walnuts, peanuts, cashews, etc.)")
    print("• Soy (soy sauce, tofu, miso, tempeh, etc.)")
    print("• Shellfish (shrimp, crab, lobster, scallops, etc.)")
    print("• Fish (salmon, tuna, cod, anchovies, etc.)")
    print("• Sesame (sesame seeds, tahini, sesame oil, etc.)")

def main():
    """
    Main function
    """
    print("🥜 Recipe Allergen Detector")
    print("=" * 50)
    print("🔍 Rule-based allergen detection")
    print("🆓 No API required - completely free!")
    
    # Process all recipes with allergen detection
    process_recipes_with_allergens(max_recipes=368)

if __name__ == "__main__":
    main()
