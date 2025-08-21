/**
 * Allergen Filtering System
 * Allows users to set allergen preferences and filter recipes accordingly
 */

class AllergenFilter {
    constructor() {
        this.storageKey = 'userAllergens';
        this.userAllergens = this.loadUserAllergens();
        this.availableAllergens = [
            'dairy', 'eggs', 'fish', 'gluten', 'nuts', 'peanuts', 
            'sesame', 'shellfish', 'soy', 'tree nuts'
        ];
        this.init();
    }

    init() {
        this.createAllergenUI();
        this.applyFilters();
        this.setupEventListeners();
    }

    loadUserAllergens() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.warn('Failed to load allergen preferences:', e);
            return [];
        }
    }

    saveUserAllergens() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.userAllergens));
        } catch (e) {
            console.warn('Failed to save allergen preferences:', e);
        }
    }

    createAllergenUI() {
        // Create floating allergen preferences button
        const allergenButton = document.createElement('button');
        allergenButton.id = 'allergen-preferences-btn';
        allergenButton.innerHTML = '🚫 Allergen Filters';
        allergenButton.className = 'allergen-preferences-btn';
        
        // Create allergen preferences modal
        const modal = document.createElement('div');
        modal.id = 'allergen-modal';
        modal.className = 'allergen-modal';
        modal.innerHTML = this.createModalHTML();

        // Add to page
        document.body.appendChild(allergenButton);
        document.body.appendChild(modal);

        // Add CSS
        this.addCSS();
    }

    createModalHTML() {
        const checkboxes = this.availableAllergens.map(allergen => {
            const checked = this.userAllergens.includes(allergen) ? 'checked' : '';
            const capitalizedAllergen = allergen.charAt(0).toUpperCase() + allergen.slice(1);
            
            return `
                <label class="allergen-checkbox">
                    <input type="checkbox" value="${allergen}" ${checked}>
                    <span class="checkmark"></span>
                    ${capitalizedAllergen}
                </label>
            `;
        }).join('');

        return `
            <div class="allergen-modal-content">
                <div class="allergen-modal-header">
                    <h3>🚫 My Allergen Restrictions</h3>
                    <button class="allergen-modal-close">&times;</button>
                </div>
                <div class="allergen-modal-body">
                    <p>Select allergens you want to avoid. Recipes containing these allergens will be hidden.</p>
                    <div class="allergen-checkboxes">
                        ${checkboxes}
                    </div>
                    <div class="allergen-actions">
                        <button class="btn-clear-all">Clear All</button>
                        <button class="btn-save">Save Preferences</button>
                    </div>
                    <div class="allergen-stats">
                        <span id="filtered-count">0</span> recipes hidden based on your preferences
                    </div>
                </div>
            </div>
        `;
    }

    addCSS() {
        const style = document.createElement('style');
        style.textContent = `
            .allergen-preferences-btn {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #dc3545;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
                z-index: 1000;
                transition: all 0.3s ease;
            }

            .allergen-preferences-btn:hover {
                background: #c82333;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
            }

            .allergen-modal {
                display: none;
                position: fixed;
                z-index: 2000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                backdrop-filter: blur(4px);
            }

            .allergen-modal.show {
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .allergen-modal-content {
                background: white;
                border-radius: 12px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: modalSlideIn 0.3s ease;
            }

            @keyframes modalSlideIn {
                from { transform: translateY(-50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }

            .allergen-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                border-bottom: 1px solid #dee2e6;
            }

            .allergen-modal-header h3 {
                margin: 0;
                color: #dc3545;
                font-size: 1.25rem;
            }

            .allergen-modal-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #6c757d;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background-color 0.2s ease;
            }

            .allergen-modal-close:hover {
                background-color: #f8f9fa;
                color: #dc3545;
            }

            .allergen-modal-body {
                padding: 20px;
            }

            .allergen-modal-body p {
                margin: 0 0 20px 0;
                color: #6c757d;
            }

            .allergen-checkboxes {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
                margin-bottom: 20px;
            }

            .allergen-checkbox {
                display: flex;
                align-items: center;
                cursor: pointer;
                padding: 8px;
                border-radius: 6px;
                transition: background-color 0.2s ease;
                position: relative;
                user-select: none;
            }

            .allergen-checkbox:hover {
                background-color: #f8f9fa;
            }

            .allergen-checkbox input[type="checkbox"] {
                display: none;
            }

            .checkmark {
                width: 20px;
                height: 20px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                margin-right: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }

            .allergen-checkbox input[type="checkbox"]:checked + .checkmark {
                background-color: #dc3545;
                border-color: #dc3545;
            }

            .allergen-checkbox input[type="checkbox"]:checked + .checkmark::after {
                content: '✓';
                color: white;
                font-size: 12px;
                font-weight: bold;
            }

            .allergen-actions {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }

            .allergen-actions button {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s ease;
            }

            .btn-clear-all {
                background: #6c757d;
                color: white;
            }

            .btn-clear-all:hover {
                background: #5a6268;
            }

            .btn-save {
                background: #28a745;
                color: white;
                flex: 1;
            }

            .btn-save:hover {
                background: #218838;
            }

            .allergen-stats {
                padding: 10px;
                background: #f8f9fa;
                border-radius: 6px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }

            #filtered-count {
                font-weight: 600;
                color: #dc3545;
            }

            /* Recipe hiding styles */
            .recipe-hidden-by-allergen {
                display: none !important;
            }

            .allergen-filter-notice {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 12px;
                margin: 20px 0;
                color: #856404;
            }

            .allergen-filter-notice strong {
                color: #dc3545;
            }

            @media (max-width: 768px) {
                .allergen-preferences-btn {
                    top: 10px;
                    right: 10px;
                    padding: 8px 12px;
                    font-size: 12px;
                }

                .allergen-checkboxes {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupEventListeners() {
        const button = document.getElementById('allergen-preferences-btn');
        const modal = document.getElementById('allergen-modal');
        const closeBtn = modal.querySelector('.allergen-modal-close');
        const clearBtn = modal.querySelector('.btn-clear-all');
        const saveBtn = modal.querySelector('.btn-save');
        const checkboxes = modal.querySelectorAll('input[type="checkbox"]');

        // Open modal
        button.addEventListener('click', () => {
            modal.classList.add('show');
            this.updateStats();
        });

        // Close modal
        const closeModal = () => modal.classList.remove('show');
        closeBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Clear all allergens
        clearBtn.addEventListener('click', () => {
            checkboxes.forEach(cb => cb.checked = false);
            this.updateStats();
        });

        // Save preferences
        saveBtn.addEventListener('click', () => {
            this.userAllergens = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            this.saveUserAllergens();
            this.applyFilters();
            closeModal();
            this.showSaveNotification();
        });

        // Update stats on checkbox change
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => this.updateStats());
        });

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeModal();
            }
        });
    }

    applyFilters() {
        if (this.userAllergens.length === 0) {
            // Show all recipes
            document.querySelectorAll('.recipe-hidden-by-allergen').forEach(el => {
                el.classList.remove('recipe-hidden-by-allergen');
            });
            this.removeFilterNotice();
            return;
        }

        let hiddenCount = 0;
        
        // Find all recipe elements (adjust selectors based on your HTML structure)
        const recipeElements = document.querySelectorAll('[data-allergens], .recipe-item, .recipe-card, article.recipe');
        
        recipeElements.forEach(element => {
            const allergens = this.getRecipeAllergens(element);
            const hasUserAllergen = allergens.some(allergen => 
                this.userAllergens.includes(allergen.toLowerCase())
            );
            
            if (hasUserAllergen) {
                element.classList.add('recipe-hidden-by-allergen');
                hiddenCount++;
            } else {
                element.classList.remove('recipe-hidden-by-allergen');
            }
        });

        this.showFilterNotice(hiddenCount);
        this.updateButtonText();
    }

    getRecipeAllergens(element) {
        // Try multiple ways to get allergen data
        const allergenData = element.dataset.allergens;
        if (allergenData) {
            try {
                return JSON.parse(allergenData);
            } catch (e) {
                return allergenData.split(',').map(a => a.trim());
            }
        }

        // Look for allergen elements within the recipe
        const allergenElements = element.querySelectorAll('.allergen-tag, [data-allergen]');
        const allergens = [];
        
        allergenElements.forEach(el => {
            const allergen = el.dataset.allergen || el.textContent.trim().toLowerCase();
            if (allergen) allergens.push(allergen);
        });

        return allergens;
    }

    updateStats() {
        const modal = document.getElementById('allergen-modal');
        const checkboxes = modal.querySelectorAll('input[type="checkbox"]:checked');
        const selectedAllergens = Array.from(checkboxes).map(cb => cb.value);
        
        // Count recipes that would be hidden
        const recipeElements = document.querySelectorAll('[data-allergens], .recipe-item, .recipe-card, article.recipe');
        let wouldHideCount = 0;
        
        recipeElements.forEach(element => {
            const allergens = this.getRecipeAllergens(element);
            const hasSelectedAllergen = allergens.some(allergen => 
                selectedAllergens.includes(allergen.toLowerCase())
            );
            if (hasSelectedAllergen) wouldHideCount++;
        });

        document.getElementById('filtered-count').textContent = wouldHideCount;
    }

    showFilterNotice(hiddenCount) {
        this.removeFilterNotice();
        
        if (hiddenCount > 0) {
            const notice = document.createElement('div');
            notice.className = 'allergen-filter-notice';
            notice.innerHTML = `
                <strong>${hiddenCount}</strong> recipes are hidden based on your allergen preferences. 
                <button onclick="allergenFilter.clearAllFilters()" style="background: none; border: none; color: #dc3545; text-decoration: underline; cursor: pointer;">
                    Show all recipes
                </button>
            `;
            
            // Insert at the top of main content
            const mainContent = document.querySelector('main, .container, .content');
            if (mainContent) {
                mainContent.insertBefore(notice, mainContent.firstChild);
            }
        }
    }

    removeFilterNotice() {
        const existingNotice = document.querySelector('.allergen-filter-notice');
        if (existingNotice) {
            existingNotice.remove();
        }
    }

    updateButtonText() {
        const button = document.getElementById('allergen-preferences-btn');
        if (this.userAllergens.length > 0) {
            button.innerHTML = `🚫 Filters (${this.userAllergens.length})`;
            button.style.background = '#dc3545';
        } else {
            button.innerHTML = '🚫 Allergen Filters';
            button.style.background = '#6c757d';
        }
    }

    clearAllFilters() {
        this.userAllergens = [];
        this.saveUserAllergens();
        this.applyFilters();
        
        // Update modal checkboxes if open
        const modal = document.getElementById('allergen-modal');
        modal.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    }

    showSaveNotification() {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 3000;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = 'Allergen preferences saved!';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.allergenFilter = new AllergenFilter();
});

// Add animation keyframes
const animationStyle = document.createElement('style');
animationStyle.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(animationStyle);
