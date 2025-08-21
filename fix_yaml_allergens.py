#!/usr/bin/env python3
"""
Fix malformed YAML allergen syntax in Hugo recipe files.
Fixes patterns like: - "eggs", 'gluten', 'nuts'"
"""

import os
import re
import glob

def fix_allergen_yaml(content):
    """Fix malformed allergen YAML syntax."""
    # Pattern to match malformed allergen lines like: - "eggs", 'gluten', 'nuts'"
    pattern = r'^(\s*)-\s*"([^"]+)",\s*\'([^\']+)\'(?:,\s*\'([^\']+)\')*"?\s*$'
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a malformed allergen line
        match = re.match(pattern, line)
        if match:
            indent = match.group(1).replace('-', ' ')  # Get indentation
            allergens = [match.group(2)]  # First allergen in quotes
            
            # Add remaining allergens
            if match.group(3):
                allergens.append(match.group(3))
            if match.group(4):
                allergens.append(match.group(4))
            
            # Look for additional allergens on the same line
            remaining = line[match.end():]
            additional_matches = re.findall(r"'([^']+)'", remaining)
            allergens.extend(additional_matches)
            
            # Create properly formatted YAML lines
            for allergen in allergens:
                fixed_lines.append(f'{indent}- "{allergen}"')
        else:
            fixed_lines.append(line)
        
        i += 1
    
    return '\n'.join(fixed_lines)

def main():
    """Fix all recipe files with malformed YAML."""
    recipe_dir = "/Users/kylejonespatricia/our_table/content/recipes"
    files_fixed = 0
    
    # Get all markdown files
    for filepath in glob.glob(os.path.join(recipe_dir, "*.md")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file contains malformed allergen syntax
            if "', '" in content or '", \'' in content:
                print(f"Fixing: {os.path.basename(filepath)}")
                fixed_content = fix_allergen_yaml(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                files_fixed += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print(f"\nFixed {files_fixed} files with malformed YAML syntax.")

if __name__ == "__main__":
    main()
