#!/usr/bin/env python3
"""
Fix allergen YAML indentation issues in Hugo recipe files.
"""

import os
import glob

def fix_allergen_indentation(content):
    """Fix allergen lines that start with '- "' instead of '  - "'."""
    lines = content.split('\n')
    fixed_lines = []
    in_allergens = False
    
    for line in lines:
        # Check if we're entering allergens section
        if line.strip() == 'allergens:':
            in_allergens = True
            fixed_lines.append(line)
            continue
        
        # Check if we're leaving allergens section
        if in_allergens and line.strip() and not line.startswith(' ') and ':' in line:
            in_allergens = False
        
        # Fix allergen lines with wrong indentation
        if in_allergens and line.startswith('- "') and not line.startswith('  - "'):
            fixed_lines.append('  ' + line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    """Fix all recipe files with allergen indentation issues."""
    recipe_dir = "/Users/kylejonespatricia/our_table/content/recipes"
    files_fixed = 0
    
    # Get all markdown files
    for filepath in glob.glob(os.path.join(recipe_dir, "*.md")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has allergen indentation issues
            if '\n- "' in content:
                print(f"Fixing: {os.path.basename(filepath)}")
                fixed_content = fix_allergen_indentation(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                files_fixed += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print(f"\nFixed {files_fixed} files with allergen indentation issues.")

if __name__ == "__main__":
    main()
