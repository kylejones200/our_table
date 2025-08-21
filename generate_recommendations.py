#!/usr/bin/env python3
"""
Recipe Recommendation Engine for Hugo Recipe Website
Generates "If you liked this recipe, you might also like..." recommendations
"""

import os
import re
import json
import glob
from collections import defaultdict, Counter
from pathlib import Path
import yaml

class RecipeRecommendationEngine:
    def __init__(self, recipes_dir):
        self.recipes_dir = Path(recipes_dir)
        self.recipes = {}
        self.ingredient_index = defaultdict(set)
        self.category_index = defaultdict(set)
        self.cooking_method_index = defaultdict(set)
        self.allergen_index = defaultdict(set)
        
    def load_recipes(self):
        """Load all recipe files and extract metadata"""
        print("🔍 Loading recipes...")
        
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
                            'ingredients': recipe_data.get('ingredients') or [],
                            'categories': recipe_data.get('categories') or [],
                            'allergens': recipe_data.get('allergens') or [],
                            'steps': recipe_data.get('steps') or [],
                            'file': recipe_file.name
                        }
                        
                        # Build indexes
                        self._index_recipe(recipe_slug, recipe_data)
                        
            except Exception as e:
                print(f"  ⚠️  Error loading {recipe_file.name}: {e}")
                continue
        
        print(f"✅ Loaded {len(self.recipes)} recipes")
    
    def _index_recipe(self, recipe_slug, recipe_data):
        """Index recipe by ingredients, categories, cooking methods, allergens"""
        # Index ingredients
        ingredients = recipe_data.get('ingredients', [])
        for ingredient in ingredients:
            # Extract key ingredients (remove quantities and common words)
            key_ingredients = self._extract_key_ingredients(ingredient)
            for key_ingredient in key_ingredients:
                self.ingredient_index[key_ingredient].add(recipe_slug)
        
        # Index categories
        categories = recipe_data.get('categories', [])
        for category in categories:
            self.category_index[category.lower()].add(recipe_slug)
        
        # Index allergens
        allergens = recipe_data.get('allergens', [])
        for allergen in allergens:
            self.allergen_index[allergen.lower()].add(recipe_slug)
        
        # Index cooking methods from steps
        steps = recipe_data.get('steps', [])
        cooking_methods = self._extract_cooking_methods(steps)
        for method in cooking_methods:
            self.cooking_method_index[method].add(recipe_slug)
    
    def _extract_key_ingredients(self, ingredient_text):
        """Extract key ingredients from ingredient text"""
        # Common words to ignore
        ignore_words = {
            'cup', 'cups', 'tbsp', 'tsp', 'teaspoon', 'tablespoon', 'pound', 'pounds',
            'lb', 'lbs', 'oz', 'ounce', 'ounces', 'inch', 'inches', 'large', 'small',
            'medium', 'fresh', 'dried', 'chopped', 'diced', 'sliced', 'minced',
            'finely', 'coarsely', 'roughly', 'thinly', 'thickly', 'and', 'or', 'to',
            'taste', 'optional', 'plus', 'extra', 'additional', 'more', 'less',
            'about', 'approximately', 'room', 'temperature', 'cold', 'warm', 'hot'
        }
        
        # Clean and extract key words
        clean_text = re.sub(r'[\d/\-\(\)]+', ' ', ingredient_text.lower())
        words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text)
        key_ingredients = [word for word in words if word not in ignore_words]
        
        return key_ingredients[:3]  # Take top 3 key ingredients
    
    def _extract_cooking_methods(self, steps):
        """Extract cooking methods from recipe steps"""
        cooking_methods = set()
        method_keywords = {
            'bake': 'baking', 'baking': 'baking', 'baked': 'baking',
            'grill': 'grilling', 'grilling': 'grilling', 'grilled': 'grilling',
            'fry': 'frying', 'frying': 'frying', 'fried': 'frying',
            'sauté': 'sauteing', 'saute': 'sauteing', 'sautéing': 'sauteing',
            'roast': 'roasting', 'roasting': 'roasting', 'roasted': 'roasting',
            'boil': 'boiling', 'boiling': 'boiling', 'boiled': 'boiling',
            'steam': 'steaming', 'steaming': 'steaming', 'steamed': 'steaming',
            'broil': 'broiling', 'broiling': 'broiling', 'broiled': 'broiling',
            'simmer': 'simmering', 'simmering': 'simmering',
            'mix': 'mixing', 'mixing': 'mixing', 'stir': 'mixing',
            'blend': 'blending', 'blending': 'blending',
            'marinate': 'marinating', 'marinating': 'marinating'
        }
        
        for step in steps:
            step_text = step.lower()
            for keyword, method in method_keywords.items():
                if keyword in step_text:
                    cooking_methods.add(method)
        
        return cooking_methods
    
    def calculate_similarity(self, recipe1_slug, recipe2_slug):
        """Calculate similarity score between two recipes"""
        if recipe1_slug == recipe2_slug:
            return 0
        
        recipe1 = self.recipes.get(recipe1_slug)
        recipe2 = self.recipes.get(recipe2_slug)
        
        if not recipe1 or not recipe2:
            return 0
        
        score = 0
        
        # Ingredient similarity (40% weight)
        ingredients1 = set(self._extract_all_key_ingredients(recipe1['ingredients']))
        ingredients2 = set(self._extract_all_key_ingredients(recipe2['ingredients']))
        
        if ingredients1 and ingredients2:
            ingredient_similarity = len(ingredients1 & ingredients2) / len(ingredients1 | ingredients2)
            score += ingredient_similarity * 0.4
        
        # Category similarity (25% weight)
        categories1 = set(cat.lower() for cat in recipe1['categories'])
        categories2 = set(cat.lower() for cat in recipe2['categories'])
        
        if categories1 and categories2:
            category_similarity = len(categories1 & categories2) / len(categories1 | categories2)
            score += category_similarity * 0.25
        
        # Cooking method similarity (20% weight)
        methods1 = self._extract_cooking_methods(recipe1['steps'])
        methods2 = self._extract_cooking_methods(recipe2['steps'])
        
        if methods1 and methods2:
            method_similarity = len(methods1 & methods2) / len(methods1 | methods2)
            score += method_similarity * 0.2
        
        # Calculate allergen compatibility (fewer shared allergens = better)
        allergens1 = set(allergen.lower() for allergen in (recipe1['allergens'] or []) if allergen)
        allergens2 = set(allergen.lower() for allergen in (recipe2['allergens'] or []) if allergen)
        
        if allergens1 or allergens2:
            allergen_similarity = len(allergens1 & allergens2) / max(len(allergens1 | allergens2), 1)
            score += allergen_similarity * 0.15
        
        return score
    
    def _extract_all_key_ingredients(self, ingredients):
        """Extract all key ingredients from ingredient list"""
        all_ingredients = []
        for ingredient in ingredients:
            all_ingredients.extend(self._extract_key_ingredients(ingredient))
        return all_ingredients
    
    def get_recommendations(self, recipe_slug, num_recommendations=5):
        """Get recipe recommendations for a given recipe"""
        if recipe_slug not in self.recipes:
            return []
        
        similarities = []
        
        for other_slug in self.recipes:
            if other_slug != recipe_slug:
                similarity = self.calculate_similarity(recipe_slug, other_slug)
                if similarity > 0.1:  # Minimum similarity threshold
                    similarities.append((other_slug, similarity))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        recommendations = []
        for slug, score in similarities[:num_recommendations]:
            recipe = self.recipes[slug]
            recommendations.append({
                'slug': slug,
                'title': recipe['title'],
                'score': round(score, 3),
                'categories': recipe['categories'],
                'file': recipe['file']
            })
        
        return recommendations
    
    def generate_all_recommendations(self):
        """Generate recommendations for all recipes"""
        print("🤖 Generating recipe recommendations...")
        
        all_recommendations = {}
        
        for recipe_slug in self.recipes:
            recommendations = self.get_recommendations(recipe_slug)
            if recommendations:
                all_recommendations[recipe_slug] = recommendations
                print(f"  ✅ {recipe_slug}: {len(recommendations)} recommendations")
        
        return all_recommendations
    
    def save_recommendations_json(self, output_file):
        """Save recommendations to JSON file for Hugo to use"""
        recommendations = self.generate_all_recommendations()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved recommendations to {output_file}")
        return recommendations

def main():
    """Generate recipe recommendations"""
    recipes_dir = "/Users/kylejonespatricia/our_table/content/recipes"
    output_file = "/Users/kylejonespatricia/our_table/data/recommendations.json"
    
    print("🍽️  Recipe Recommendation Engine")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize recommendation engine
    engine = RecipeRecommendationEngine(recipes_dir)
    engine.load_recipes()
    
    # Generate and save recommendations
    recommendations = engine.save_recommendations_json(output_file)
    
    print(f"\n📊 Generated recommendations for {len(recommendations)} recipes")
    print("🔗 Recommendations saved to data/recommendations.json")
    print("\n💡 Features:")
    print("• Ingredient-based similarity matching")
    print("• Category and cooking method analysis")
    print("• Allergen compatibility scoring")
    print("• Smart ingredient extraction (ignores quantities)")

if __name__ == "__main__":
    main()
