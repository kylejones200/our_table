#!/usr/bin/env python3
"""
Convert recipes.json to Hugo markdown files
"""

import json
import os
import re
from datetime import datetime

def slugify(text):
    """Convert text to URL-friendly slug"""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    return slug.strip('-')

def format_ingredients(ingredients_list):
    """Format ingredients for YAML front matter"""
    formatted = []
    for ingredient_group in ingredients_list:
        if ingredient_group.get('section'):
            # Add section header as a comment-style entry
            formatted.append(f"--- {ingredient_group['section']} ---")
        for item in ingredient_group.get('items', []):
            formatted.append(item)
    return formatted

def format_directions(directions_list):
    """Format directions for YAML front matter"""
    return directions_list

def write_yaml_value(key, value, indent=0):
    """Write a YAML key-value pair with proper formatting"""
    spaces = "  " * indent
    if isinstance(value, str):
        # Escape quotes and handle multiline strings
        if '\n' in value or '"' in value:
            return f'{spaces}{key}: |\n{spaces}  {value.replace(chr(10), chr(10) + spaces + "  ")}'
        else:
            return f'{spaces}{key}: "{value}"'
    elif isinstance(value, list):
        if not value:
            return f'{spaces}{key}: []'
        result = [f'{spaces}{key}:']
        for item in value:
            if isinstance(item, str):
                # Escape quotes in YAML strings
                escaped_item = item.replace('"', '\\"')
                result.append(f'{spaces}  - "{escaped_item}"')
            else:
                result.append(f'{spaces}  - {item}')
        return '\n'.join(result)
    elif isinstance(value, (int, float, bool)):
        return f'{spaces}{key}: {value}'
    else:
        return f'{spaces}{key}: "{str(value)}"'

def clean_title(title):
    """Clean up recipe titles"""
    # Remove common prefixes that aren't part of the actual recipe name
    if title.startswith("Yield:"):
        # This seems to be malformed data, skip or handle differently
        return None
    return title.strip()

def extract_servings(recipe):
    """Extract serving information"""
    servings = recipe.get('servings', '')
    servings_min = recipe.get('servings_min')
    servings_max = recipe.get('servings_max')
    
    if servings_min and servings_max:
        if servings_min == servings_max:
            return f"{servings_min} servings"
        else:
            return f"{servings_min}-{servings_max} servings"
    elif servings:
        return servings
    else:
        return "4 servings"

def convert_recipes_to_hugo():
    """Convert recipes.json to Hugo markdown files"""
    
    # Load recipes JSON
    with open('recipes.json', 'r') as f:
        recipes = json.load(f)
    
    # Create recipes directory if it doesn't exist
    recipes_dir = 'content/recipes'
    os.makedirs(recipes_dir, exist_ok=True)
    
    successful_conversions = 0
    skipped_recipes = []
    
    for recipe in recipes:
        # Clean and validate title
        title = clean_title(recipe.get('title', ''))
        if not title:
            skipped_recipes.append(f"Recipe with no valid title: {recipe}")
            continue
            
        # Create filename slug
        filename_slug = slugify(title)
        if not filename_slug:
            skipped_recipes.append(f"Could not create slug for: {title}")
            continue
            
        filepath = os.path.join(recipes_dir, f"{filename_slug}.md")
        
        # Prepare front matter data
        front_matter = {
            'title': title,
            'date': datetime.now().isoformat(),
            'type': 'recipe',
            'description': recipe.get('subtitle', ''),
            'yield': extract_servings(recipe),
            'categories': recipe.get('categories', []),
            'source': recipe.get('source', ''),
        }
        
        # Add ingredients and directions
        if recipe.get('ingredients'):
            front_matter['ingredients'] = format_ingredients(recipe['ingredients'])
        
        if recipe.get('directions'):
            front_matter['steps'] = format_directions(recipe['directions'])
        
        # Add notes if present
        if recipe.get('notes'):
            notes_text = '\n'.join(recipe['notes']) if isinstance(recipe['notes'], list) else str(recipe['notes'])
            front_matter['notes'] = notes_text
        
        # Create markdown content
        content_lines = ['---']
        
        # Write YAML front matter manually
        for key, value in front_matter.items():
            content_lines.append(write_yaml_value(key, value))
        
        content_lines.append('---')
        content_lines.append('')
        
        # Add any additional content (description or notes as body text)
        if recipe.get('subtitle'):
            content_lines.append(recipe['subtitle'])
            content_lines.append('')
        
        # Add Hugo shortcodes for recipe display
        content_lines.append('{{< recipe-meta >}}')
        content_lines.append('')
        content_lines.append('{{< ingredients >}}')
        content_lines.append('')
        content_lines.append('{{< steps >}}')
        content_lines.append('')
        content_lines.append('{{< nutrition >}}')
        content_lines.append('')
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        successful_conversions += 1
        print(f"✓ Created: {filepath}")
    
    print(f"\nConversion complete!")
    print(f"Successfully converted: {successful_conversions} recipes")
    if skipped_recipes:
        print(f"Skipped: {len(skipped_recipes)} recipes")
        for skipped in skipped_recipes[:5]:  # Show first 5 skipped
            print(f"  - {skipped}")
        if len(skipped_recipes) > 5:
            print(f"  ... and {len(skipped_recipes) - 5} more")

if __name__ == "__main__":
    convert_recipes_to_hugo()
