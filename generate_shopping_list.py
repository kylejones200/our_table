#!/usr/bin/env python3
"""
Smart Shopping List Generator for Hugo Recipes
Combines ingredients intelligently and handles quantity aggregation
"""

import json
import os
import re
import sys
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import argparse

class IngredientParser:
    """Parse and normalize recipe ingredients"""
    
    # Common measurement units and their conversions to base units
    UNIT_CONVERSIONS = {
        # Volume - convert to cups
        'cup': 1.0, 'cups': 1.0, 'c': 1.0,
        'tablespoon': 1/16, 'tablespoons': 1/16, 'tbsp': 1/16, 'tbs': 1/16,
        'teaspoon': 1/48, 'teaspoons': 1/48, 'tsp': 1/48,
        'fluid ounce': 1/8, 'fluid ounces': 1/8, 'fl oz': 1/8, 'oz': 1/8,
        'pint': 2.0, 'pints': 2.0, 'pt': 2.0,
        'quart': 4.0, 'quarts': 4.0, 'qt': 4.0,
        'gallon': 16.0, 'gallons': 16.0, 'gal': 16.0,
        'liter': 4.227, 'liters': 4.227, 'l': 4.227,
        'milliliter': 0.004227, 'milliliters': 0.004227, 'ml': 0.004227,
        
        # Weight - convert to ounces
        'pound': 16.0, 'pounds': 16.0, 'lb': 16.0, 'lbs': 16.0,
        'ounce': 1.0, 'ounces': 1.0,
        'gram': 0.035274, 'grams': 0.035274, 'g': 0.035274,
        'kilogram': 35.274, 'kilograms': 35.274, 'kg': 35.274,
        
        # Count units
        'piece': 1.0, 'pieces': 1.0,
        'item': 1.0, 'items': 1.0,
        'clove': 1.0, 'cloves': 1.0,
        'head': 1.0, 'heads': 1.0,
        'bunch': 1.0, 'bunches': 1.0,
        'package': 1.0, 'packages': 1.0, 'pkg': 1.0,
        'can': 1.0, 'cans': 1.0,
        'jar': 1.0, 'jars': 1.0,
        'bottle': 1.0, 'bottles': 1.0,
        'stick': 1.0, 'sticks': 1.0,
        'slice': 1.0, 'slices': 1.0,
        'sheet': 1.0, 'sheets': 1.0,
    }
    
    # Words to ignore when normalizing ingredient names
    IGNORE_WORDS = {
        'fresh', 'dried', 'frozen', 'canned', 'chopped', 'diced', 'sliced',
        'minced', 'crushed', 'ground', 'whole', 'half', 'quartered',
        'peeled', 'seeded', 'stemmed', 'trimmed', 'cleaned', 'washed',
        'cooked', 'uncooked', 'raw', 'roasted', 'toasted', 'melted',
        'softened', 'room temperature', 'cold', 'warm', 'hot',
        'large', 'medium', 'small', 'extra', 'jumbo', 'baby',
        'organic', 'free-range', 'grass-fed', 'wild-caught',
        'unsalted', 'salted', 'sweet', 'sour', 'bitter',
        'optional', 'for', 'garnish', 'serving', 'taste',
        'plus', 'more', 'additional', 'extra', 'as', 'needed'
    }

    def parse_ingredient(self, ingredient_text):
        """
        Parse an ingredient string into quantity, unit, and name
        Returns: (quantity, unit, normalized_name, original_text)
        """
        original = ingredient_text.strip()
        text = original.lower()
        
        # Skip instructions that aren't ingredients
        skip_patterns = [
            r'heat.*oil', r'fry.*until', r'remove.*drain', r'serve.*immediately',
            r'whip.*into', r'fold.*in', r'flatten.*tbsp', r'place.*tsp',
            r'form.*ball', r'pinch.*closed'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, text):
                return (None, None, None, original)
        
        # Handle special cases
        if any(word in text for word in ['salt', 'pepper', 'to taste']):
            if 'salt' in text and 'pepper' in text:
                return (1.0, 'pinch', 'salt and pepper', original)
            elif 'salt' in text:
                return (1.0, 'pinch', 'salt', original)
            elif 'pepper' in text:
                return (1.0, 'pinch', 'pepper', original)
        
        # Extract quantity (numbers and fractions)
        quantity_pattern = r'^(\d+(?:\s+\d+/\d+|\.\d+|/\d+)?|\d+/\d+)'
        quantity_match = re.match(quantity_pattern, text)
        
        if quantity_match:
            quantity_str = quantity_match.group(1)
            quantity = self._parse_quantity(quantity_str)
            remaining_text = text[len(quantity_str):].strip()
        else:
            quantity = 1.0
            remaining_text = text
        
        # Extract unit
        unit = None
        for unit_name in sorted(self.UNIT_CONVERSIONS.keys(), key=len, reverse=True):
            if remaining_text.startswith(unit_name + ' ') or remaining_text == unit_name:
                unit = unit_name
                remaining_text = remaining_text[len(unit_name):].strip()
                break
        
        # Clean up the ingredient name
        ingredient_name = self._normalize_ingredient_name(remaining_text)
        
        # Skip if no meaningful ingredient name
        if not ingredient_name or len(ingredient_name) < 2:
            return (None, None, None, original)
        
        return (quantity, unit, ingredient_name, original)
    
    def _parse_quantity(self, quantity_str):
        """Parse quantity string with fractions"""
        try:
            # Handle mixed numbers like "1 1/2"
            if ' ' in quantity_str:
                parts = quantity_str.split()
                whole = float(parts[0])
                fraction = Fraction(parts[1])
                return whole + float(fraction)
            # Handle fractions like "1/2"
            elif '/' in quantity_str:
                return float(Fraction(quantity_str))
            # Handle decimals
            else:
                return float(quantity_str)
        except:
            return 1.0
    
    def _normalize_ingredient_name(self, name):
        """Normalize ingredient name for smart combining"""
        # Remove parenthetical descriptions
        name = re.sub(r'\([^)]*\)', '', name)
        
        # Split into words and filter
        words = name.split()
        filtered_words = []
        
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word.lower() not in self.IGNORE_WORDS:
                filtered_words.append(clean_word.lower())
        
        # Handle special ingredient mappings
        normalized = ' '.join(filtered_words)
        
        # Common ingredient normalizations
        normalizations = {
            'all purpose flour': 'flour',
            'bread flour': 'flour',
            'whole wheat flour': 'flour',
            'granulated sugar': 'sugar',
            'white sugar': 'sugar',
            'brown sugar': 'brown sugar',
            'powdered sugar': 'powdered sugar',
            'confectioners sugar': 'powdered sugar',
            'olive oil': 'olive oil',
            'vegetable oil': 'vegetable oil',
            'canola oil': 'vegetable oil',
            'unsalted butter': 'butter',
            'salted butter': 'butter',
            'heavy cream': 'heavy cream',
            'whipping cream': 'heavy cream',
            'milk': 'milk',
            'whole milk': 'milk',
            '2% milk': 'milk',
            'chicken breast': 'chicken breast',
            'chicken thighs': 'chicken thighs',
            'ground beef': 'ground beef',
            'yellow onion': 'onion',
            'white onion': 'onion',
            'red onion': 'red onion',
            'garlic': 'garlic',
            'roma tomatoes': 'tomatoes',
            'cherry tomatoes': 'cherry tomatoes',
        }
        
        return normalizations.get(normalized, normalized)

class ShoppingListGenerator:
    """Generate smart shopping lists from selected recipes"""
    
    def __init__(self):
        self.parser = IngredientParser()
        self.recipes = {}
        self.load_recipes()
    
    def load_recipes(self):
        """Load all recipes from Hugo markdown files"""
        recipes_dir = Path('content/recipes')
        if not recipes_dir.exists():
            print("❌ Recipes directory not found")
            return
        
        for recipe_file in recipes_dir.glob('*.md'):
            try:
                with open(recipe_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract front matter
                parts = content.split('---', 2)
                if len(parts) < 3:
                    continue
                
                front_matter = parts[1]
                
                # Extract title
                title_match = re.search(r'title:\s*["\']([^"\']*)["\']', front_matter)
                title = title_match.group(1) if title_match else recipe_file.stem
                
                # Extract ingredients
                ingredients_match = re.search(r'ingredients:\s*\n((?:\s*-\s*"[^"]*"\s*\n)*)', front_matter, re.MULTILINE)
                ingredients = []
                if ingredients_match:
                    ingredients_text = ingredients_match.group(1)
                    ingredients = re.findall(r'-\s*"([^"]*)"', ingredients_text)
                
                # Extract yield/servings
                yield_match = re.search(r'yield:\s*["\']([^"\']*)["\']', front_matter)
                servings = 1
                if yield_match:
                    yield_text = yield_match.group(1)
                    servings_match = re.search(r'(\d+)', yield_text)
                    if servings_match:
                        servings = int(servings_match.group(1))
                
                self.recipes[recipe_file.stem] = {
                    'title': title,
                    'ingredients': ingredients,
                    'servings': servings,
                    'file': recipe_file.stem
                }
                
            except Exception as e:
                print(f"⚠️  Error loading {recipe_file}: {e}")
                continue
        
        print(f"📚 Loaded {len(self.recipes)} recipes")
    
    def generate_shopping_list(self, recipe_names, servings_multiplier=None):
        """
        Generate a smart shopping list from selected recipes
        servings_multiplier: dict of recipe_name -> multiplier
        """
        if not recipe_names:
            print("❌ No recipes selected")
            return
        
        # Aggregate ingredients
        ingredient_totals = defaultdict(lambda: {'quantity': 0, 'unit': None, 'items': []})
        
        for recipe_name in recipe_names:
            if recipe_name not in self.recipes:
                print(f"⚠️  Recipe '{recipe_name}' not found")
                continue
            
            recipe = self.recipes[recipe_name]
            multiplier = 1.0
            
            if servings_multiplier and recipe_name in servings_multiplier:
                multiplier = servings_multiplier[recipe_name]
            
            print(f"📝 Processing: {recipe['title']} (×{multiplier})")
            
            for ingredient_text in recipe['ingredients']:
                quantity, unit, normalized_name, original = self.parser.parse_ingredient(ingredient_text)
                
                if not normalized_name or quantity is None:
                    continue
                
                # Apply multiplier
                adjusted_quantity = quantity * multiplier
                
                # Combine with existing ingredients
                if normalized_name in ingredient_totals:
                    existing = ingredient_totals[normalized_name]
                    
                    # Try to combine quantities if units are compatible
                    if self._can_combine_units(existing['unit'], unit):
                        # Convert to common unit
                        existing_base = self._convert_to_base_unit(existing['quantity'], existing['unit'])
                        new_base = self._convert_to_base_unit(adjusted_quantity, unit)
                        
                        if existing_base is not None and new_base is not None:
                            combined_base = existing_base + new_base
                            existing['quantity'] = combined_base
                            existing['unit'] = self._get_best_display_unit(combined_base, existing['unit'], unit)
                        else:
                            # Can't combine, add as separate item
                            existing['items'].append(f"{self._format_quantity(adjusted_quantity)} {unit or ''} {normalized_name}".strip())
                    else:
                        # Different unit types, add as separate item
                        existing['items'].append(f"{self._format_quantity(adjusted_quantity)} {unit or ''} {normalized_name}".strip())
                else:
                    ingredient_totals[normalized_name] = {
                        'quantity': adjusted_quantity,
                        'unit': unit,
                        'items': []
                    }
        
        # Generate formatted shopping list
        self._print_shopping_list(ingredient_totals, recipe_names)
        
        # Save to file
        self._save_shopping_list(ingredient_totals, recipe_names)
    
    def _can_combine_units(self, unit1, unit2):
        """Check if two units can be combined"""
        if not unit1 or not unit2:
            return unit1 == unit2
        
        # Get unit categories
        volume_units = {'cup', 'cups', 'c', 'tablespoon', 'tablespoons', 'tbsp', 'tbs', 
                       'teaspoon', 'teaspoons', 'tsp', 'fluid ounce', 'fluid ounces', 'fl oz', 'oz',
                       'pint', 'pints', 'pt', 'quart', 'quarts', 'qt', 'gallon', 'gallons', 'gal',
                       'liter', 'liters', 'l', 'milliliter', 'milliliters', 'ml'}
        
        weight_units = {'pound', 'pounds', 'lb', 'lbs', 'ounce', 'ounces', 
                       'gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg'}
        
        count_units = {'piece', 'pieces', 'item', 'items', 'clove', 'cloves', 'head', 'heads',
                      'bunch', 'bunches', 'package', 'packages', 'pkg', 'can', 'cans',
                      'jar', 'jars', 'bottle', 'bottles', 'stick', 'sticks', 'slice', 'slices'}
        
        unit1_lower = unit1.lower()
        unit2_lower = unit2.lower()
        
        return ((unit1_lower in volume_units and unit2_lower in volume_units) or
                (unit1_lower in weight_units and unit2_lower in weight_units) or
                (unit1_lower in count_units and unit2_lower in count_units))
    
    def _convert_to_base_unit(self, quantity, unit):
        """Convert quantity to base unit"""
        if not unit:
            return quantity
        
        unit_lower = unit.lower()
        if unit_lower in self.parser.UNIT_CONVERSIONS:
            return quantity * self.parser.UNIT_CONVERSIONS[unit_lower]
        
        return quantity
    
    def _get_best_display_unit(self, base_quantity, unit1, unit2):
        """Choose the best unit for display"""
        if not unit1 and not unit2:
            return None
        
        # Prefer the more common/readable unit
        preferred_units = ['cup', 'tablespoon', 'teaspoon', 'pound', 'ounce', 'piece', 'clove']
        
        for preferred in preferred_units:
            if unit1 and preferred in unit1.lower():
                return unit1
            if unit2 and preferred in unit2.lower():
                return unit2
        
        return unit1 or unit2
    
    def _format_quantity(self, quantity):
        """Format quantity for display"""
        if quantity == int(quantity):
            return str(int(quantity))
        
        # Try to convert to fraction for common values
        frac = Fraction(quantity).limit_denominator(16)
        if abs(float(frac) - quantity) < 0.01:
            if frac.numerator > frac.denominator:
                whole = frac.numerator // frac.denominator
                remainder = frac.numerator % frac.denominator
                if remainder == 0:
                    return str(whole)
                else:
                    return f"{whole} {remainder}/{frac.denominator}"
            else:
                return str(frac)
        
        return f"{quantity:.2f}".rstrip('0').rstrip('.')
    
    def _print_shopping_list(self, ingredient_totals, recipe_names):
        """Print formatted shopping list"""
        print("\n" + "="*60)
        print("🛒 SMART SHOPPING LIST")
        print("="*60)
        print(f"📝 Recipes: {', '.join(recipe_names)}")
        print(f"📊 Total ingredients: {len(ingredient_totals)}")
        print()
        
        # Group by category
        categories = {
            'Produce': ['onion', 'garlic', 'tomatoes', 'lettuce', 'carrots', 'celery', 'peppers', 'herbs'],
            'Meat & Seafood': ['chicken', 'beef', 'pork', 'fish', 'shrimp', 'salmon'],
            'Dairy': ['milk', 'butter', 'cheese', 'cream', 'yogurt', 'eggs'],
            'Pantry': ['flour', 'sugar', 'oil', 'vinegar', 'spices', 'salt', 'pepper'],
            'Canned/Packaged': ['beans', 'tomato sauce', 'broth', 'pasta', 'rice']
        }
        
        categorized = defaultdict(list)
        uncategorized = []
        
        for ingredient_name, data in sorted(ingredient_totals.items()):
            categorized_item = False
            
            for category, keywords in categories.items():
                if any(keyword in ingredient_name.lower() for keyword in keywords):
                    if data['items']:
                        # Has multiple items
                        for item in data['items']:
                            categorized[category].append(f"  • {item}")
                    else:
                        # Single combined item
                        formatted = f"  • {self._format_quantity(data['quantity'])}"
                        if data['unit']:
                            formatted += f" {data['unit']}"
                        formatted += f" {ingredient_name}"
                        categorized[category].append(formatted)
                    categorized_item = True
                    break
            
            if not categorized_item:
                if data['items']:
                    for item in data['items']:
                        uncategorized.append(f"  • {item}")
                else:
                    formatted = f"  • {self._format_quantity(data['quantity'])}"
                    if data['unit']:
                        formatted += f" {data['unit']}"
                    formatted += f" {ingredient_name}"
                    uncategorized.append(formatted)
        
        # Print categorized items
        for category in ['Produce', 'Meat & Seafood', 'Dairy', 'Pantry', 'Canned/Packaged']:
            if categorized[category]:
                print(f"🏷️  {category.upper()}")
                for item in sorted(categorized[category]):
                    print(item)
                print()
        
        # Print uncategorized items
        if uncategorized:
            print("🏷️  OTHER")
            for item in sorted(uncategorized):
                print(item)
            print()
        
        print("="*60)
    
    def _save_shopping_list(self, ingredient_totals, recipe_names):
        """Save shopping list to file"""
        filename = f"shopping_list_{'_'.join(recipe_names[:3])}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("SMART SHOPPING LIST\n")
            f.write("="*50 + "\n")
            f.write(f"Recipes: {', '.join(recipe_names)}\n")
            f.write(f"Generated: {os.popen('date').read().strip()}\n\n")
            
            for ingredient_name, data in sorted(ingredient_totals.items()):
                if data['items']:
                    for item in data['items']:
                        f.write(f"• {item}\n")
                else:
                    formatted = f"• {self._format_quantity(data['quantity'])}"
                    if data['unit']:
                        formatted += f" {data['unit']}"
                    formatted += f" {ingredient_name}\n"
                    f.write(formatted)
        
        print(f"💾 Shopping list saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Generate smart shopping lists from Hugo recipes')
    parser.add_argument('recipes', nargs='+', help='Recipe names (file names without .md)')
    parser.add_argument('--servings', '-s', help='Servings multiplier (format: recipe1:2,recipe2:1.5)')
    
    args = parser.parse_args()
    
    # Parse servings multiplier
    servings_multiplier = {}
    if args.servings:
        for item in args.servings.split(','):
            if ':' in item:
                recipe, multiplier = item.split(':')
                servings_multiplier[recipe.strip()] = float(multiplier)
    
    # Generate shopping list
    generator = ShoppingListGenerator()
    generator.generate_shopping_list(args.recipes, servings_multiplier)

if __name__ == "__main__":
    main()
