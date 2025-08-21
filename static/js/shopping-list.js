/**
 * Shopping List Generator for Hugo Recipe Site
 * Allows users to select recipes and generate smart shopping lists
 */

class ShoppingListGenerator {
    constructor() {
        this.selectedRecipes = new Set();
        this.recipes = new Map();
        this.init();
    }

    async init() {
        await this.loadRecipes();
        this.setupUI();
        this.bindEvents();
    }

    async loadRecipes() {
        // In a real implementation, this would load from your Hugo site's recipe data
        // For now, we'll create a simple interface that works with the Python backend
        console.log('Shopping list generator initialized');
    }

    setupUI() {
        // Create shopping list interface if it doesn't exist
        if (!document.getElementById('shopping-list-interface')) {
            this.createShoppingListInterface();
        }
    }

    createShoppingListInterface() {
        const interface = document.createElement('div');
        interface.id = 'shopping-list-interface';
        interface.innerHTML = `
            <div class="shopping-list-container">
                <h3>🛒 Generate Shopping List</h3>
                <div class="recipe-selection">
                    <div class="selected-recipes">
                        <h4>Selected Recipes:</h4>
                        <div id="selected-recipes-list" class="selected-list">
                            <p class="empty-state">No recipes selected</p>
                        </div>
                    </div>
                    <div class="recipe-controls">
                        <button id="add-current-recipe" class="btn btn-primary">
                            ➕ Add Current Recipe
                        </button>
                        <button id="generate-shopping-list" class="btn btn-success" disabled>
                            🛒 Generate Shopping List
                        </button>
                        <button id="clear-selection" class="btn btn-secondary">
                            🗑️ Clear All
                        </button>
                    </div>
                </div>
                <div id="shopping-list-output" class="shopping-output hidden">
                    <h4>📝 Your Shopping List:</h4>
                    <div class="list-actions">
                        <button id="copy-list" class="btn btn-outline">📋 Copy</button>
                        <button id="download-list" class="btn btn-outline">💾 Download</button>
                    </div>
                    <div id="shopping-list-content" class="list-content"></div>
                </div>
            </div>
        `;

        // Add CSS
        const style = document.createElement('style');
        style.textContent = `
            .shopping-list-container {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 1.5rem;
                margin: 2rem 0;
            }

            .shopping-list-container h3 {
                margin: 0 0 1rem 0;
                color: #495057;
            }

            .recipe-selection {
                display: grid;
                gap: 1rem;
                margin-bottom: 1.5rem;
            }

            .selected-recipes {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 1rem;
            }

            .selected-recipes h4 {
                margin: 0 0 0.5rem 0;
                font-size: 1rem;
                color: #6c757d;
            }

            .selected-list {
                min-height: 60px;
            }

            .empty-state {
                color: #6c757d;
                font-style: italic;
                margin: 0;
            }

            .recipe-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem;
                background: #e9ecef;
                border-radius: 4px;
                margin-bottom: 0.5rem;
            }

            .recipe-item:last-child {
                margin-bottom: 0;
            }

            .recipe-controls {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
            }

            .btn {
                padding: 0.5rem 1rem;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.2s;
            }

            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .btn-primary {
                background: #007bff;
                color: white;
            }

            .btn-primary:hover:not(:disabled) {
                background: #0056b3;
            }

            .btn-success {
                background: #28a745;
                color: white;
            }

            .btn-success:hover:not(:disabled) {
                background: #1e7e34;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-secondary:hover:not(:disabled) {
                background: #545b62;
            }

            .btn-outline {
                background: white;
                color: #007bff;
                border: 1px solid #007bff;
            }

            .btn-outline:hover {
                background: #007bff;
                color: white;
            }

            .btn-danger {
                background: #dc3545;
                color: white;
                padding: 0.25rem 0.5rem;
                font-size: 0.8rem;
            }

            .btn-danger:hover {
                background: #c82333;
            }

            .shopping-output {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 1rem;
            }

            .shopping-output h4 {
                margin: 0 0 1rem 0;
                color: #495057;
            }

            .list-actions {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }

            .list-content {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 1rem;
                font-family: monospace;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }

            .hidden {
                display: none;
            }

            .loading {
                opacity: 0.6;
                pointer-events: none;
            }

            @media (max-width: 768px) {
                .recipe-controls {
                    flex-direction: column;
                }

                .list-actions {
                    flex-direction: column;
                }
            }
        `;
        document.head.appendChild(style);

        // Add to page
        const recipeContent = document.querySelector('.recipe-content') || document.querySelector('main');
        if (recipeContent) {
            recipeContent.appendChild(interface);
        }
    }

    bindEvents() {
        // Add current recipe button
        document.getElementById('add-current-recipe')?.addEventListener('click', () => {
            this.addCurrentRecipe();
        });

        // Generate shopping list button
        document.getElementById('generate-shopping-list')?.addEventListener('click', () => {
            this.generateShoppingList();
        });

        // Clear selection button
        document.getElementById('clear-selection')?.addEventListener('click', () => {
            this.clearSelection();
        });

        // Copy list button
        document.getElementById('copy-list')?.addEventListener('click', () => {
            this.copyShoppingList();
        });

        // Download list button
        document.getElementById('download-list')?.addEventListener('click', () => {
            this.downloadShoppingList();
        });
    }

    addCurrentRecipe() {
        // Get current recipe title from page
        const titleElement = document.querySelector('h1') || document.querySelector('.recipe-title');
        if (!titleElement) {
            alert('Could not find recipe title on this page');
            return;
        }

        const title = titleElement.textContent.trim();
        const slug = this.titleToSlug(title);

        if (this.selectedRecipes.has(slug)) {
            alert('Recipe already added to shopping list');
            return;
        }

        this.selectedRecipes.add(slug);
        this.recipes.set(slug, { title, slug });
        this.updateSelectedRecipesList();
        this.updateGenerateButton();
    }

    titleToSlug(title) {
        return title.toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim('-');
    }

    removeRecipe(slug) {
        this.selectedRecipes.delete(slug);
        this.recipes.delete(slug);
        this.updateSelectedRecipesList();
        this.updateGenerateButton();
    }

    updateSelectedRecipesList() {
        const listElement = document.getElementById('selected-recipes-list');
        if (!listElement) return;

        if (this.selectedRecipes.size === 0) {
            listElement.innerHTML = '<p class="empty-state">No recipes selected</p>';
            return;
        }

        const items = Array.from(this.selectedRecipes).map(slug => {
            const recipe = this.recipes.get(slug);
            return `
                <div class="recipe-item">
                    <span>${recipe.title}</span>
                    <button class="btn btn-danger" onclick="shoppingListGen.removeRecipe('${slug}')">
                        ✕
                    </button>
                </div>
            `;
        }).join('');

        listElement.innerHTML = items;
    }

    updateGenerateButton() {
        const button = document.getElementById('generate-shopping-list');
        if (button) {
            button.disabled = this.selectedRecipes.size === 0;
        }
    }

    clearSelection() {
        this.selectedRecipes.clear();
        this.recipes.clear();
        this.updateSelectedRecipesList();
        this.updateGenerateButton();
        this.hideShoppingList();
    }

    async generateShoppingList() {
        if (this.selectedRecipes.size === 0) return;

        const container = document.querySelector('.shopping-list-container');
        const outputElement = document.getElementById('shopping-list-output');
        const contentElement = document.getElementById('shopping-list-content');

        // Show loading state
        container.classList.add('loading');
        
        try {
            // Create command for Python script
            const recipeList = Array.from(this.selectedRecipes).join(' ');
            const command = `python3 generate_shopping_list.py ${recipeList}`;
            
            // Since we can't run Python directly from the browser,
            // we'll create a downloadable script or show instructions
            const instructions = this.createInstructions(recipeList);
            
            contentElement.textContent = instructions;
            outputElement.classList.remove('hidden');
            
        } catch (error) {
            alert('Error generating shopping list: ' + error.message);
        } finally {
            container.classList.remove('loading');
        }
    }

    createInstructions(recipeList) {
        return `To generate your smart shopping list, run this command in your terminal:

cd /Users/kylejonespatricia/our_table
python3 generate_shopping_list.py ${recipeList}

This will create a smart shopping list that:
• Combines duplicate ingredients (e.g., won't list salt 3 times)
• Converts measurements to common units
• Groups items by store category (Produce, Dairy, etc.)
• Saves the list to a text file

Selected recipes: ${Array.from(this.recipes.values()).map(r => r.title).join(', ')}

Alternatively, copy the recipe names above and use them with the shopping list generator.`;
    }

    copyShoppingList() {
        const content = document.getElementById('shopping-list-content');
        if (content) {
            navigator.clipboard.writeText(content.textContent).then(() => {
                alert('Shopping list copied to clipboard!');
            }).catch(() => {
                alert('Could not copy to clipboard');
            });
        }
    }

    downloadShoppingList() {
        const content = document.getElementById('shopping-list-content');
        if (content) {
            const blob = new Blob([content.textContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `shopping-list-${Date.now()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }

    hideShoppingList() {
        const outputElement = document.getElementById('shopping-list-output');
        if (outputElement) {
            outputElement.classList.add('hidden');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.shoppingListGen = new ShoppingListGenerator();
});

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.shoppingListGen = new ShoppingListGenerator();
    });
} else {
    window.shoppingListGen = new ShoppingListGenerator();
}
