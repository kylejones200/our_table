class ShoppingListGenerator {
    constructor() {
        this.selectedRecipes = new Set();
        this.recipes = [];
        this.init();
    }

    async init() {
        await this.loadRecipes();
        this.setupEventListeners();
        this.renderRecipes();
    }

    async loadRecipes() {
        // Use hardcoded recipes with real data from our site
        this.recipes = this.getKnownRecipes();
    }

    getKnownRecipes() {
        return [
            {
                title: "Salsa",
                url: "/recipes/salsa/",
                yield: "4 servings",
                categories: ["appetizer", "condiment"],
                ingredients: [
                    "2 (1 lb) cans whole tomatoes, drained",
                    "4-5 jalapenos",
                    "3-4 Tbsp fresh cilantro",
                    "1 small garlic clove, minced",
                    "Pinch of oregano",
                    "Salt to taste",
                    "2 green onions"
                ]
            },
            {
                title: "Breaded Pork Chops",
                url: "/recipes/breaded-pork-chops/",
                yield: "6 servings",
                categories: ["pork", "entree"],
                ingredients: [
                    "6 pork chops, 1/2 inch thick",
                    "1 cup fine dry bread crumbs",
                    "1 1/2 tsp rosemary leaves, crushed",
                    "1 egg",
                    "2 Tbsp seasoned vegetable oil",
                    "2 Tbsp water",
                    "Margarine for drizzling"
                ]
            },
            {
                title: "Pappy's Potato Soup",
                url: "/recipes/pappys-potato-soup/",
                yield: "4 servings",
                categories: ["soup"],
                ingredients: [
                    "2 Tbsp butter, divided",
                    "1 medium onion, finely chopped",
                    "6 large potatoes, peeled and diced",
                    "1 cup water (approximately)",
                    "1 cup milk",
                    "Salt and pepper to taste"
                ]
            },
            {
                title: "Spinach Salad",
                url: "/recipes/spinach-salad/",
                yield: "8 servings",
                categories: ["salad"],
                ingredients: [
                    "1 lb. fresh spinach",
                    "1 head red leaf lettuce",
                    "1/2 head iceberg lettuce",
                    "1/2 lb. bacon, fried and crumbled",
                    "4-6 mushrooms, sliced",
                    "1/4 cup sugar",
                    "1/4 cup salad oil",
                    "1/4 cup raspberry wine vinegar",
                    "1/2 tsp salt",
                    "1/2 tsp dry mustard",
                    "1/2 tsp onion juice, grated from fresh onion"
                ]
            },
            {
                title: "Candy Cane Cake Truffles",
                url: "/recipes/candy-cane-cake-truffles/",
                yield: "4 servings",
                categories: ["dessert", "truffle"],
                ingredients: [
                    "1 box devil's food cake mix",
                    "1 can chocolate frosting (16 oz.)",
                    "1 tsp peppermint extract",
                    "1 package almond bark",
                    "8 candy canes, crushed",
                    "Waxed paper"
                ]
            },
            {
                title: "Coconut Pudding with Pineapple",
                url: "/recipes/active-30-min/",
                yield: "6 servings",
                categories: ["dessert", "pudding"],
                ingredients: [
                    "2 cups fresh pineapple, cut into 1/2-inch pieces",
                    "1/4 cup granulated sugar",
                    "1 envelope unflavored powdered gelatin",
                    "1/4 cup water",
                    "1 (14 oz) can sweetened condensed milk",
                    "1 (14 oz) can unsweetened coconut milk",
                    "1 Tbsp plus 1 tsp fresh lime juice",
                    "1/8 tsp pure vanilla extract",
                    "1 large egg white",
                    "2 Tbsp light brown sugar",
                    "1/2 cup salted roasted cashews"
                ]
            }
        ];
    }

    setupEventListeners() {
        const searchInput = document.getElementById('recipe-search');
        const generateButton = document.getElementById('generate-list');
        const downloadButton = document.getElementById('download-list');
        const printButton = document.getElementById('print-list');
        const newListButton = document.getElementById('new-list');

        searchInput.addEventListener('input', (e) => {
            this.filterRecipes(e.target.value);
        });

        generateButton.addEventListener('click', () => {
            this.generateShoppingList();
        });

        downloadButton.addEventListener('click', () => {
            this.downloadList();
        });

        printButton.addEventListener('click', () => {
            this.printList();
        });

        newListButton.addEventListener('click', () => {
            this.resetList();
        });
    }

    renderRecipes(filteredRecipes = null) {
        const grid = document.getElementById('recipe-grid');
        const recipesToRender = filteredRecipes || this.recipes;
        
        grid.innerHTML = recipesToRender.map(recipe => `
            <div class="recipe-card" data-recipe-id="${recipe.url}" onclick="shoppingList.toggleRecipe('${recipe.url}')">
                <h4>${recipe.title}</h4>
                <div class="recipe-meta">
                    <span>Serves: ${recipe.yield || 'Unknown'}</span>
                </div>
                <div class="recipe-categories">
                    ${(recipe.categories || []).map(cat => `<span class="category-tag">${cat}</span>`).join('')}
                </div>
            </div>
        `).join('');
    }

    filterRecipes(searchTerm) {
        const filtered = this.recipes.filter(recipe => 
            recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (recipe.categories || []).some(cat => cat.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        this.renderRecipes(filtered);
    }

    toggleRecipe(recipeUrl) {
        const card = document.querySelector(`[data-recipe-id="${recipeUrl}"]`);
        
        if (this.selectedRecipes.has(recipeUrl)) {
            this.selectedRecipes.delete(recipeUrl);
            card.classList.remove('selected');
        } else {
            this.selectedRecipes.add(recipeUrl);
            card.classList.add('selected');
        }
        
        this.updateSelectedList();
    }

    updateSelectedList() {
        const selectedList = document.getElementById('selected-list');
        const selectedCount = document.getElementById('selected-count');
        const generateButton = document.getElementById('generate-list');
        
        selectedCount.textContent = this.selectedRecipes.size;
        generateButton.disabled = this.selectedRecipes.size === 0;
        
        if (this.selectedRecipes.size === 0) {
            selectedList.innerHTML = '<p>No recipes selected</p>';
            return;
        }
        
        const selectedRecipeData = this.recipes.filter(recipe => 
            this.selectedRecipes.has(recipe.url)
        );
        
        selectedList.innerHTML = selectedRecipeData.map(recipe => `
            <div class="selected-recipe-item">
                <span>${recipe.title}</span>
                <button class="remove-recipe" onclick="shoppingList.toggleRecipe('${recipe.url}')">&times;</button>
            </div>
        `).join('');
    }

    async generateShoppingList() {
        const selectedRecipeData = this.recipes.filter(recipe => 
            this.selectedRecipes.has(recipe.url)
        );
        
        const shoppingList = this.processIngredients(selectedRecipeData);
        this.displayShoppingList(shoppingList);
    }

    processIngredients(recipes) {
        const ingredientMap = new Map();
        
        recipes.forEach(recipe => {
            (recipe.ingredients || []).forEach(ingredient => {
                const normalized = this.normalizeIngredient(ingredient);
                const key = normalized.name.toLowerCase();
                
                if (ingredientMap.has(key)) {
                    const existing = ingredientMap.get(key);
                    existing.quantity = this.combineQuantities(existing.quantity, normalized.quantity);
                    existing.recipes.push(recipe.title);
                } else {
                    normalized.recipes = [recipe.title];
                    ingredientMap.set(key, normalized);
                }
            });
        });
        
        return this.categorizeIngredients(Array.from(ingredientMap.values()));
    }

    normalizeIngredient(ingredient) {
        const cleanIngredient = ingredient.replace(/[""]/g, '"').trim();
        
        // Extract quantity and unit
        const quantityMatch = cleanIngredient.match(/^([\d\s\/\.\-]+(?:\s*(?:to|\-)\s*[\d\s\/\.]+)?)\s*([a-zA-Z]*\.?)\s+(.+)$/);
        
        if (quantityMatch) {
            return {
                quantity: `${quantityMatch[1].trim()} ${quantityMatch[2].trim()}`.trim(),
                name: this.cleanIngredientName(quantityMatch[3]),
                original: ingredient
            };
        }
        
        return {
            quantity: '',
            name: this.cleanIngredientName(cleanIngredient),
            original: ingredient
        };
    }

    cleanIngredientName(name) {
        return name
            .replace(/,.*$/, '')
            .replace(/\(.*?\)/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    combineQuantities(qty1, qty2) {
        if (!qty1) return qty2;
        if (!qty2) return qty1;
        
        const num1 = parseFloat(qty1);
        const num2 = parseFloat(qty2);
        
        if (!isNaN(num1) && !isNaN(num2)) {
            const unit1 = qty1.replace(num1.toString(), '').trim();
            const unit2 = qty2.replace(num2.toString(), '').trim();
            
            if (unit1 === unit2) {
                return `${num1 + num2} ${unit1}`.trim();
            }
        }
        
        return `${qty1} + ${qty2}`;
    }

    categorizeIngredients(ingredients) {
        const categories = {
            'Produce': ['onion', 'garlic', 'tomato', 'pepper', 'cilantro', 'lemon', 'lime', 'spinach', 'lettuce', 'mushroom', 'potato', 'pineapple'],
            'Dairy & Eggs': ['butter', 'cheese', 'milk', 'cream', 'egg', 'margarine'],
            'Pantry': ['flour', 'sugar', 'salt', 'pepper', 'oil', 'vinegar', 'rosemary', 'oregano'],
            'Meat': ['pork', 'bacon'],
            'Other': []
        };
        
        const categorized = {};
        
        ingredients.forEach(ingredient => {
            let category = 'Other';
            for (const [cat, keywords] of Object.entries(categories)) {
                if (keywords.some(keyword => 
                    ingredient.name.toLowerCase().includes(keyword.toLowerCase())
                )) {
                    category = cat;
                    break;
                }
            }
            
            if (!categorized[category]) {
                categorized[category] = [];
            }
            categorized[category].push(ingredient);
        });
        
        return categorized;
    }

    displayShoppingList(categorizedList) {
        const output = document.getElementById('shopping-list-output');
        const content = document.getElementById('shopping-list-content');
        
        let html = '';
        Object.entries(categorizedList).forEach(([category, ingredients]) => {
            if (ingredients.length > 0) {
                html += `
                    <div class="ingredient-category">
                        <h3>${category}</h3>
                        <ul class="ingredient-list">
                            ${ingredients.map(ingredient => `
                                <li>
                                    <input type="checkbox" class="ingredient-checkbox" onchange="this.nextElementSibling.classList.toggle('checked', this.checked)">
                                    <span class="ingredient-text">
                                        ${ingredient.quantity} ${ingredient.name}
                                        <small style="color: #666;">(${ingredient.recipes.join(', ')})</small>
                                    </span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            }
        });
        
        content.innerHTML = html;
        output.style.display = 'block';
        output.scrollIntoView({ behavior: 'smooth' });
    }

    downloadList() {
        const content = document.getElementById('shopping-list-content');
        const categories = content.querySelectorAll('.ingredient-category');
        
        let text = 'Shopping List\\n=============\\n\\n';
        categories.forEach(category => {
            const title = category.querySelector('h3').textContent;
            const items = category.querySelectorAll('.ingredient-text');
            
            text += `${title}:\\n`;
            items.forEach(item => {
                const fullText = item.textContent.trim();
                const mainText = fullText.split('(')[0].trim();
                text += `  - ${mainText}\\n`;
            });
            text += '\\n';
        });
        
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'shopping-list.txt';
        a.click();
        URL.revokeObjectURL(url);
    }

    printList() {
        window.print();
    }

    resetList() {
        this.selectedRecipes.clear();
        document.querySelectorAll('.recipe-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.getElementById('shopping-list-output').style.display = 'none';
        this.updateSelectedList();
    }
}

let shoppingList;
document.addEventListener('DOMContentLoaded', () => {
    shoppingList = new ShoppingListGenerator();
});
