#!/usr/bin/env python3
"""
Bulk Prep Feature for Hugo Recipe Website
Groups recipes by shared ingredients and cooking methods for efficient meal prep
"""

import os
import re
import json
import glob
from collections import defaultdict, Counter
from pathlib import Path
import yaml

class BulkPrepPlanner:
    def __init__(self, recipes_dir):
        self.recipes_dir = Path(recipes_dir)
        self.recipes = {}
        self.ingredient_groups = defaultdict(list)
        self.cooking_method_groups = defaultdict(list)
        self.equipment_groups = defaultdict(list)
        
    def load_recipes(self):
        """Load all recipe files and extract metadata"""
        print("🔍 Loading recipes for bulk prep analysis...")
        
        for recipe_file in self.recipes_dir.glob("*.md"):
            try:
                with open(recipe_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse front matter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        front_matter = parts[1]
                        recipe_data = yaml.safe_load(front_matter) or {}
                        
                        recipe_slug = recipe_file.stem
                        self.recipes[recipe_slug] = {
                            'title': recipe_data.get('title', recipe_slug),
                            'ingredients': recipe_data.get('ingredients', []),
                            'categories': recipe_data.get('categories', []),
                            'steps': recipe_data.get('steps', []),
                            'yield': recipe_data.get('yield', ''),
                            'file': recipe_file.name
                        }
                        
                        # Analyze for bulk prep opportunities
                        self._analyze_for_bulk_prep(recipe_slug, recipe_data)
                        
            except Exception as e:
                print(f"  ⚠️  Error loading {recipe_file.name}: {e}")
                continue
        
        print(f"✅ Loaded {len(self.recipes)} recipes")
    
    def _analyze_for_bulk_prep(self, recipe_slug, recipe_data):
        """Analyze recipe for bulk prep opportunities"""
        ingredients = recipe_data.get('ingredients', [])
        steps = recipe_data.get('steps', [])
        
        # Group by major ingredients
        major_ingredients = self._extract_major_ingredients(ingredients)
        for ingredient in major_ingredients:
            self.ingredient_groups[ingredient].append(recipe_slug)
        
        # Group by cooking methods
        cooking_methods = self._extract_cooking_methods(steps)
        for method in cooking_methods:
            self.cooking_method_groups[method].append(recipe_slug)
        
        # Group by equipment needed
        equipment = self._extract_equipment(steps)
        for equip in equipment:
            self.equipment_groups[equip].append(recipe_slug)
    
    def _extract_major_ingredients(self, ingredients):
        """Extract major ingredients that are good for bulk prep"""
        major_ingredient_keywords = {
            # Proteins
            'chicken': ['chicken', 'poultry'],
            'beef': ['beef', 'steak', 'ground beef', 'brisket'],
            'pork': ['pork', 'bacon', 'ham', 'sausage'],
            'fish': ['salmon', 'fish', 'tuna', 'cod'],
            'turkey': ['turkey'],
            'lamb': ['lamb'],
            
            # Vegetables that benefit from bulk prep
            'onions': ['onion', 'onions'],
            'carrots': ['carrot', 'carrots'],
            'potatoes': ['potato', 'potatoes'],
            'bell_peppers': ['bell pepper', 'peppers'],
            'mushrooms': ['mushroom', 'mushrooms'],
            'garlic': ['garlic'],
            'tomatoes': ['tomato', 'tomatoes'],
            
            # Grains and starches
            'rice': ['rice', 'basmati', 'jasmine'],
            'pasta': ['pasta', 'noodles', 'spaghetti', 'linguine'],
            'beans': ['beans', 'chickpeas', 'lentils'],
            'quinoa': ['quinoa'],
            
            # Dairy
            'cheese': ['cheese', 'cheddar', 'parmesan', 'mozzarella'],
            'cream': ['cream', 'heavy cream', 'sour cream'],
            
            # Pantry items for bulk cooking
            'broth': ['broth', 'stock', 'chicken broth'],
            'wine': ['wine', 'white wine', 'red wine']
        }
        
        found_ingredients = set()
        
        for ingredient_text in ingredients:
            ingredient_lower = ingredient_text.lower()
            for major_ingredient, keywords in major_ingredient_keywords.items():
                if any(keyword in ingredient_lower for keyword in keywords):
                    found_ingredients.add(major_ingredient)
        
        return found_ingredients
    
    def _extract_cooking_methods(self, steps):
        """Extract cooking methods from recipe steps"""
        cooking_methods = set()
        method_keywords = {
            'oven_baking': ['bake', 'baking', 'baked', 'oven', 'roast', 'roasting'],
            'grilling': ['grill', 'grilling', 'grilled', 'barbecue', 'bbq'],
            'stovetop': ['sauté', 'saute', 'fry', 'frying', 'simmer', 'boil'],
            'slow_cooking': ['slow cook', 'crockpot', 'slow cooker', 'braise'],
            'pressure_cooking': ['pressure cook', 'instant pot'],
            'marinating': ['marinate', 'marinating', 'marinade'],
            'prep_intensive': ['chop', 'dice', 'slice', 'mince', 'julienne']
        }
        
        all_steps_text = ' '.join(steps).lower()
        
        for method, keywords in method_keywords.items():
            if any(keyword in all_steps_text for keyword in keywords):
                cooking_methods.add(method)
        
        return cooking_methods
    
    def _extract_equipment(self, steps):
        """Extract cooking equipment from recipe steps"""
        equipment = set()
        equipment_keywords = {
            'grill': ['grill', 'grilling', 'barbecue'],
            'oven': ['oven', 'bake', 'roast', 'broil'],
            'slow_cooker': ['slow cooker', 'crockpot'],
            'pressure_cooker': ['pressure cooker', 'instant pot'],
            'food_processor': ['food processor', 'processor'],
            'blender': ['blender', 'blend'],
            'stand_mixer': ['mixer', 'mixing bowl', 'whip'],
            'dutch_oven': ['dutch oven', 'large pot'],
            'cast_iron': ['cast iron', 'skillet']
        }
        
        all_steps_text = ' '.join(steps).lower()
        
        for equip, keywords in equipment_keywords.items():
            if any(keyword in all_steps_text for keyword in keywords):
                equipment.add(equip)
        
        return equipment
    
    def generate_bulk_prep_groups(self):
        """Generate bulk prep groups based on shared ingredients and methods"""
        print("🥘 Generating bulk prep groups...")
        
        bulk_prep_groups = {
            'by_ingredient': {},
            'by_cooking_method': {},
            'by_equipment': {},
            'meal_prep_combos': []
        }
        
        # Group by major ingredients (minimum 3 recipes to be useful)
        for ingredient, recipe_slugs in self.ingredient_groups.items():
            if len(recipe_slugs) >= 3:
                recipes = []
                for slug in recipe_slugs:
                    if slug in self.recipes:
                        recipes.append({
                            'slug': slug,
                            'title': self.recipes[slug]['title'],
                            'categories': self.recipes[slug]['categories'],
                            'file': self.recipes[slug]['file']
                        })
                
                bulk_prep_groups['by_ingredient'][ingredient] = {
                    'name': ingredient.replace('_', ' ').title(),
                    'description': f"Recipes featuring {ingredient.replace('_', ' ')} - prep this ingredient in bulk!",
                    'recipes': recipes,
                    'prep_tips': self._get_prep_tips(ingredient)
                }
        
        # Group by cooking methods
        for method, recipe_slugs in self.cooking_method_groups.items():
            if len(recipe_slugs) >= 3:
                recipes = []
                for slug in recipe_slugs:
                    if slug in self.recipes:
                        recipes.append({
                            'slug': slug,
                            'title': self.recipes[slug]['title'],
                            'categories': self.recipes[slug]['categories'],
                            'file': self.recipes[slug]['file']
                        })
                
                bulk_prep_groups['by_cooking_method'][method] = {
                    'name': method.replace('_', ' ').title(),
                    'description': f"Recipes using {method.replace('_', ' ')} - cook multiple dishes together!",
                    'recipes': recipes,
                    'efficiency_tips': self._get_cooking_tips(method)
                }
        
        # Group by equipment
        for equipment, recipe_slugs in self.equipment_groups.items():
            if len(recipe_slugs) >= 3:
                recipes = []
                for slug in recipe_slugs:
                    if slug in self.recipes:
                        recipes.append({
                            'slug': slug,
                            'title': self.recipes[slug]['title'],
                            'categories': self.recipes[slug]['categories'],
                            'file': self.recipes[slug]['file']
                        })
                
                bulk_prep_groups['by_equipment'][equipment] = {
                    'name': equipment.replace('_', ' ').title(),
                    'description': f"Recipes using {equipment.replace('_', ' ')} - maximize equipment usage!",
                    'recipes': recipes
                }
        
        # Generate smart meal prep combinations
        bulk_prep_groups['meal_prep_combos'] = self._generate_meal_prep_combos()
        
        return bulk_prep_groups
    
    def _get_prep_tips(self, ingredient):
        """Get prep tips for specific ingredients"""
        prep_tips = {
            'chicken': [
                "Buy whole chickens or family packs and portion into meal-sized amounts",
                "Marinate multiple batches at once for different flavor profiles",
                "Cook extra chicken breast for salads and sandwiches throughout the week"
            ],
            'beef': [
                "Buy larger cuts and portion for multiple meals",
                "Brown ground beef in large batches and freeze portions",
                "Marinate steaks together for consistent flavor"
            ],
            'onions': [
                "Dice large quantities and freeze in portions",
                "Caramelize onions in bulk - they freeze beautifully",
                "Pre-slice onions for the week and store in airtight containers"
            ],
            'potatoes': [
                "Wash and prep multiple pounds at once",
                "Par-boil potatoes for faster cooking later",
                "Bake extra potatoes for quick meals throughout the week"
            ],
            'rice': [
                "Cook large batches and portion into meal-sized containers",
                "Rice freezes well and reheats perfectly",
                "Make different varieties at once for meal variety"
            ]
        }
        
        return prep_tips.get(ingredient, [
            f"Buy {ingredient.replace('_', ' ')} in larger quantities for better value",
            f"Prep {ingredient.replace('_', ' ')} in advance to save time during cooking",
            f"Store prepped {ingredient.replace('_', ' ')} properly to maintain freshness"
        ])
    
    def _get_cooking_tips(self, method):
        """Get efficiency tips for cooking methods"""
        cooking_tips = {
            'oven_baking': [
                "Use multiple racks to cook several dishes simultaneously",
                "Group recipes with similar temperatures together",
                "Start with dishes that take longest, add others as needed"
            ],
            'grilling': [
                "Fire up the grill once and cook multiple proteins",
                "Grill vegetables alongside main dishes",
                "Use different heat zones for various cooking needs"
            ],
            'stovetop': [
                "Use multiple burners for different components",
                "Start with dishes that take longest to cook",
                "Prep all ingredients before starting to cook"
            ],
            'slow_cooking': [
                "Use multiple slow cookers for different dishes",
                "Prep ingredients the night before",
                "Double recipes and freeze half for later"
            ]
        }
        
        return cooking_tips.get(method, [
            f"Plan {method.replace('_', ' ')} sessions to maximize efficiency",
            f"Group similar {method.replace('_', ' ')} recipes together",
            f"Prep all ingredients before starting {method.replace('_', ' ')}"
        ])
    
    def _generate_meal_prep_combos(self):
        """Generate smart meal prep combinations"""
        combos = []
        
        # Find recipes that share multiple characteristics
        for ingredient, recipes in self.ingredient_groups.items():
            if len(recipes) >= 2:
                # Find recipes with this ingredient that also share cooking methods
                for method, method_recipes in self.cooking_method_groups.items():
                    shared_recipes = list(set(recipes) & set(method_recipes))
                    if len(shared_recipes) >= 2:
                        combo_recipes = []
                        for slug in shared_recipes[:4]:  # Limit to 4 recipes per combo
                            if slug in self.recipes:
                                combo_recipes.append({
                                    'slug': slug,
                                    'title': self.recipes[slug]['title'],
                                    'categories': self.recipes[slug]['categories'],
                                    'file': self.recipes[slug]['file']
                                })
                        
                        if len(combo_recipes) >= 2:
                            combos.append({
                                'name': f"{ingredient.replace('_', ' ').title()} + {method.replace('_', ' ').title()}",
                                'description': f"Recipes featuring {ingredient.replace('_', ' ')} using {method.replace('_', ' ')} - perfect for efficient meal prep!",
                                'recipes': combo_recipes,
                                'efficiency_score': len(combo_recipes) * 2  # Higher score for more recipes
                            })
        
        # Sort by efficiency score
        combos.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        return combos[:10]  # Return top 10 combinations
    
    def save_bulk_prep_data(self, output_file):
        """Save bulk prep data to JSON file for Hugo to use"""
        bulk_prep_data = self.generate_bulk_prep_groups()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bulk_prep_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved bulk prep data to {output_file}")
        return bulk_prep_data

def main():
    """Generate bulk prep planning data"""
    recipes_dir = "/Users/kylejonespatricia/our_table/content/recipes"
    output_file = "/Users/kylejonespatricia/our_table/data/bulk_prep.json"
    
    print("🥘 Bulk Prep Planner")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize bulk prep planner
    planner = BulkPrepPlanner(recipes_dir)
    planner.load_recipes()
    
    # Generate and save bulk prep data
    bulk_prep_data = planner.save_bulk_prep_data(output_file)
    
    print(f"\n📊 Generated bulk prep groups:")
    print(f"  • {len(bulk_prep_data['by_ingredient'])} ingredient-based groups")
    print(f"  • {len(bulk_prep_data['by_cooking_method'])} cooking method groups")
    print(f"  • {len(bulk_prep_data['by_equipment'])} equipment-based groups")
    print(f"  • {len(bulk_prep_data['meal_prep_combos'])} smart meal prep combinations")
    
    print("\n💡 Features:")
    print("• Groups recipes by shared major ingredients")
    print("• Organizes by cooking methods for efficiency")
    print("• Equipment-based groupings for maximum utilization")
    print("• Smart combinations for optimal meal prep sessions")
    print("• Prep tips and efficiency suggestions")

if __name__ == "__main__":
    main()
