#!/usr/bin/env python3
"""
Comprehensive fix for all YAML syntax errors in Hugo recipe files.
"""

import os
import re
import glob

def fix_yaml_errors(content):
    """Fix all YAML syntax errors in recipe front matter."""
    lines = content.split('\n')
    fixed_lines = []
    in_front_matter = False
    front_matter_ended = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Track front matter boundaries
        if line.strip() == '---':
            if not in_front_matter:
                in_front_matter = True
                fixed_lines.append(line)
                i += 1
                continue
            elif in_front_matter:
                front_matter_ended = True
                in_front_matter = False
                fixed_lines.append(line)
                i += 1
                continue
        
        # Only process within front matter
        if in_front_matter and not front_matter_ended:
            # Fix ingredients section with malformed content
            if line.strip() == 'ingredients:':
                fixed_lines.append(line)
                i += 1
                
                # Collect all valid ingredients
                ingredients = []
                while i < len(lines):
                    next_line = lines[i]
                    
                    # Stop if we hit another YAML key (not starting with - or space)
                    if ':' in next_line and not next_line.strip().startswith('-') and not next_line.strip().startswith('"'):
                        break
                    
                    # Extract valid ingredients
                    if next_line.strip().startswith('- "') and next_line.strip().endswith('"'):
                        ingredient = next_line.strip()[3:-1]  # Remove '- "' and '"'
                        if ingredient and not ingredient.startswith('---') and len(ingredient) > 1:
                            ingredients.append(ingredient)
                    elif next_line.strip() == '- "' or next_line.strip().startswith('- "') and not next_line.strip().endswith('"'):
                        # Skip malformed ingredient lines
                        pass
                    else:
                        # Not an ingredient line, break
                        break
                    
                    i += 1
                
                # Add properly formatted ingredients or empty array
                if ingredients:
                    for ingredient in ingredients:
                        fixed_lines.append(f'  - "{ingredient}"')
                else:
                    fixed_lines.append('  []')
                
                continue
            
            # Fix allergens section
            elif line.strip() == 'allergens:':
                fixed_lines.append(line)
                i += 1
                
                # Collect all valid allergens
                allergens = []
                while i < len(lines):
                    next_line = lines[i]
                    
                    # Stop if we hit another YAML key
                    if ':' in next_line and not next_line.strip().startswith('-'):
                        break
                    
                    # Extract valid allergens
                    if next_line.strip().startswith('- "') and next_line.strip().endswith('"'):
                        allergen = next_line.strip()[3:-1]  # Remove '- "' and '"'
                        if allergen and not allergen.startswith('---') and len(allergen) < 20:
                            allergens.append(allergen)
                    elif next_line.strip().startswith('- "') and not next_line.strip().endswith('"'):
                        # Skip malformed allergen lines
                        pass
                    else:
                        # Not an allergen line, break
                        break
                    
                    i += 1
                
                # Add properly formatted allergens
                for allergen in allergens:
                    fixed_lines.append(f'  - "{allergen}"')
                
                continue
        
        # Keep all other lines as-is
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def main():
    """Fix all recipe files with YAML syntax errors."""
    recipe_dir = "/Users/kylejonespatricia/our_table/content/recipes"
    files_fixed = 0
    
    # Get all markdown files
    for filepath in glob.glob(os.path.join(recipe_dir, "*.md")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply comprehensive fixes
            fixed_content = fix_yaml_errors(content)
            
            # Only write if content changed
            if fixed_content != content:
                print(f"Fixing: {os.path.basename(filepath)}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                files_fixed += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print(f"\nFixed {files_fixed} files with YAML syntax errors.")

if __name__ == "__main__":
    main()
