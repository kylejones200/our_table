#!/usr/bin/env python3
"""
Comprehensive fix for all YAML syntax errors in Hugo recipe files.
"""

import os
import re
import glob

def fix_yaml_content(content):
    """Fix various YAML syntax issues in recipe files."""
    lines = content.split('\n')
    fixed_lines = []
    in_front_matter = False
    front_matter_end = False
    
    for i, line in enumerate(lines):
        # Track front matter boundaries
        if line.strip() == '---':
            if not in_front_matter:
                in_front_matter = True
            elif in_front_matter and not front_matter_end:
                front_matter_end = True
                in_front_matter = False
        
        # Only process lines within front matter
        if in_front_matter and not front_matter_end:
            # Fix allergens section with malformed syntax
            if line.strip().startswith('allergens:'):
                fixed_lines.append(line)
                # Look ahead for malformed allergen lines
                j = i + 1
                while j < len(lines) and (lines[j].startswith('  -') or lines[j].startswith('-')):
                    allergen_line = lines[j]
                    
                    # Fix lines like: - "dairy"
                    # Fix lines like: - "eggs", 'gluten'
                    # Fix lines like: - "eggs", 'gluten', 'nuts'"
                    if '", \'' in allergen_line or '\', \'' in allergen_line:
                        # Extract all allergens from the malformed line
                        allergens = []
                        # Find quoted strings
                        quoted_items = re.findall(r'"([^"]+)"|\'([^\']+)\'', allergen_line)
                        for item in quoted_items:
                            allergen = item[0] if item[0] else item[1]
                            if allergen:
                                allergens.append(allergen)
                        
                        # Add properly formatted lines
                        for allergen in allergens:
                            fixed_lines.append(f'  - "{allergen}"')
                        
                        # Skip the original malformed line
                        i = j
                        j += 1
                    else:
                        # Line is properly formatted, keep it
                        fixed_lines.append(allergen_line)
                        j += 1
                
                # Skip to where we left off
                continue
            
            # Fix standalone malformed allergen lines not caught above
            elif re.match(r'^-\s*"[^"]+",\s*\'[^\']+\'', line.strip()):
                # Extract allergens and format properly
                allergens = []
                quoted_items = re.findall(r'"([^"]+)"|\'([^\']+)\'', line)
                for item in quoted_items:
                    allergen = item[0] if item[0] else item[1]
                    if allergen:
                        allergens.append(allergen)
                
                for allergen in allergens:
                    fixed_lines.append(f'  - "{allergen}"')
                continue
        
        # Keep all other lines as-is
        fixed_lines.append(line)
    
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
            
            # Check if file has potential YAML issues
            if ('", \'' in content or '\', \'' in content or 
                re.search(r'^-\s*"[^"]+",\s*\'[^\']+\'', content, re.MULTILINE)):
                
                print(f"Fixing: {os.path.basename(filepath)}")
                fixed_content = fix_yaml_content(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                files_fixed += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print(f"\nFixed {files_fixed} files with YAML syntax errors.")

if __name__ == "__main__":
    main()
