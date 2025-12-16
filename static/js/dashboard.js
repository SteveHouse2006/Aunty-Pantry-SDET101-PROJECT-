// Dashboard JavaScript for Aunty Pantry
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    
    // Get DOM elements
    const addForm = document.getElementById('addIngredientForm');
    const input = document.getElementById('ingredientInput');
    const list = document.getElementById('ingredientsList');
    const findBtn = document.getElementById('findRecipesBtn');
    const countBadge = document.getElementById('ingredientCount');
    
    // Update counts on page load
    updateAllCounts();
    
    // ADD INGREDIENT
    if (addForm) {
        addForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const name = input.value.trim();
            if (!name) return;
            
            try {
                const response = await fetch('/api/ingredients', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    input.value = '';
                    addToList(data);
                    updateAllCounts();
                    showMessage('Ingredient added!', 'success');
                } else {
                    showMessage(data.error || 'Failed to add', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('Network error', 'error');
            }
        });
    }
    
    // DELETE INGREDIENT
    if (list) {
        list.addEventListener('click', function(e) {
            if (e.target.classList.contains('delete-ingredient')) {
                const id = e.target.dataset.id;
                deleteIngredient(id);
            }
        });
    }
    
    // FIND RECIPES
    if (findBtn) {
        findBtn.addEventListener('click', function() {
            findRecipes();
        });
    }
    
    // ===== HELPER FUNCTIONS =====
    
    function addToList(ingredient) {
        // Remove empty message if present
        const emptyMsg = list.querySelector('.alert-info');
        if (emptyMsg) {
            emptyMsg.remove();
        }
        
        // Create new list item
        const item = document.createElement('div');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        item.dataset.id = ingredient.id;
        item.innerHTML = `
            <span>${ingredient.name}</span>
            <button class="btn btn-sm btn-outline-danger delete-ingredient" 
                    data-id="${ingredient.id}">
                Remove
            </button>
        `;
        
        // Add to list
        list.appendChild(item);
    }
    
    async function deleteIngredient(id) {
        try {
            const response = await fetch(`/api/ingredients/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                // Remove from DOM
                const item = document.querySelector(`[data-id="${id}"]`);
                if (item) {
                    item.remove();
                }
                
                updateAllCounts();
                
                // If list is now empty, show message
                if (list.children.length === 0) {
                    list.innerHTML = `
                        <div class="alert alert-info">
                            Your pantry is empty! Add some ingredients to find recipes.
                        </div>
                    `;
                }
                
                showMessage('Ingredient removed', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Delete failed', 'error');
        }
    }
    
    function updateAllCounts() {
        // Count actual ingredient items (not alerts)
        let count = 0;
        if (list) {
            const items = list.querySelectorAll('.list-group-item');
            count = items.length;
            console.log('Counted items:', count);
        }
        
        // Update BOTH counters:
        
        // 1. Update the badge in Find Recipes button
        if (countBadge) {
            countBadge.textContent = count;
            console.log('Updated badge to:', count);
        }
        
        // 2. Update the "Your Ingredients (X)" title
        const dynamicCount = document.getElementById('dynamicCount');
        if (dynamicCount) {
            dynamicCount.textContent = count;
            console.log('Updated dynamicCount to:', count);
        }
        
        // Update button text and state
        if (findBtn) {
            // Update the badge inside the button too
            const btnBadge = findBtn.querySelector('.badge');
            if (btnBadge) {
                btnBadge.textContent = count;
            }
            
            // Enable/disable button
            findBtn.disabled = count === 0;
            
            // Update entire button HTML to be sure
            findBtn.innerHTML = `Find Recipes 
                <span class="badge bg-light text-dark ms-2">${count}</span>`;
            
            console.log('Button updated, disabled:', findBtn.disabled);
        }
    }
    
    function showMessage(text, type) {
        // Create temporary message
        const msg = document.createElement('div');
        msg.className = `alert alert-${type === 'error' ? 'danger' : 'success'} mt-3`;
        msg.textContent = text;
        msg.style.position = 'fixed';
        msg.style.top = '20px';
        msg.style.right = '20px';
        msg.style.zIndex = '1000';
        
        document.body.appendChild(msg);
        
        // Remove after 3 seconds
        setTimeout(() => {
            msg.remove();
        }, 3000);
    }
    
    // ===== SPOONACULAR API FUNCTIONS =====
    
    async function findRecipes() {
        console.log('findRecipes() called');
        
        const recipeResultsCard = document.getElementById('recipeResultsCard');
        const recipeResults = document.getElementById('recipeResults');
        const recipeLoading = document.getElementById('recipeLoading');
        const recipeError = document.getElementById('recipeError');
        
        if (!recipeResultsCard || !recipeResults || !recipeLoading) {
            console.error('Recipe elements not found!');
            return;
        }
        
        // Show loading state
        recipeResultsCard.style.display = 'block';
        recipeLoading.style.display = 'block';
        recipeResults.innerHTML = '';
        recipeError.style.display = 'none';
        
        console.log('Fetching recipes from API...');
        
        try {
            const response = await fetch('/api/find-recipes');
            console.log('API response status:', response.status);
            
            const recipes = await response.json();
            console.log('API response data:', recipes);
            
            recipeLoading.style.display = 'none';
            
            // Check if it's an error object
            if (recipes.error) {
                recipeResults.innerHTML = `
                    <div class="alert alert-danger">
                        ${recipes.error}
                    </div>
                `;
                return;
            }
            
            if (recipes.length === 0) {
                recipeResults.innerHTML = `
                    <div class="alert alert-warning">
                        No recipes found with your current ingredients. Try adding more!
                    </div>
                `;
                return;
            }
            
            // Display recipes
            console.log(`Displaying ${recipes.length} recipes`);
            recipes.forEach(recipe => {
                const recipeCard = createRecipeCard(recipe);
                recipeResults.appendChild(recipeCard);
            });
            
        } catch (error) {
            console.error('Error fetching recipes:', error);
            recipeLoading.style.display = 'none';
            recipeError.style.display = 'block';
            recipeError.textContent = 'Failed to fetch recipes. Please try again.';
        }
    }
    
    function createRecipeCard(recipe) {
        const div = document.createElement('div');
        div.className = 'card mb-3';
        
        // Handle missing image
        const imageUrl = recipe.image || 'https://via.placeholder.com/312x231?text=No+Image';
        
        div.innerHTML = `
            <div class="row g-0">
                <div class="col-md-4">
                    <img src="${imageUrl}" class="img-fluid rounded-start" alt="${recipe.title}" 
                         style="height: 150px; width: 100%; object-fit: cover;"
                         onerror="this.src='https://via.placeholder.com/312x231?text=Image+Error'">
                </div>
                <div class="col-md-8">
                    <div class="card-body">
                        <h6 class="card-title">${recipe.title}</h6>
                        <p class="card-text">
                            <small class="text-muted">
                                <span class="text-success">✅ Uses ${recipe.usedIngredientCount || 0} ingredients you have</span><br>
                                <span class="text-danger">❌ Missing ${recipe.missedIngredientCount || 0} ingredients</span>
                            </small>
                        </p>
                        <button class="btn btn-sm btn-outline-primary view-recipe" 
                                data-id="${recipe.id}">
                            View Recipe
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add click event for view recipe button
        div.querySelector('.view-recipe').addEventListener('click', function() {
            viewRecipeDetails(recipe.id);
        });
        
        return div;
    }
    
    async function viewRecipeDetails(recipeId) {
        console.log('Viewing recipe details for ID:', recipeId);
        
        try {
            const response = await fetch(`/api/recipe/${recipeId}`);
            const recipe = await response.json();
            
            // Check if it's an error object
            if (recipe.error) {
                alert('Error: ' + recipe.error);
                return;
            }
            
            // Populate modal
            document.getElementById('recipeModalTitle').textContent = recipe.title;
            
            // Handle missing image
            const imageUrl = recipe.image || 'https://via.placeholder.com/500x300?text=No+Image';
            
            // Format ingredients list
            const ingredientsHtml = recipe.ingredients && recipe.ingredients.length > 0 
                ? recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')
                : '<li>No ingredient information available</li>';
            
            document.getElementById('recipeModalBody').innerHTML = `
                <div class="text-center mb-3">
                    <img src="${imageUrl}" class="img-fluid rounded" 
                         style="max-height: 300px; object-fit: cover;"
                         onerror="this.src='https://via.placeholder.com/500x300?text=Image+Error'">
                </div>
                <div class="row mb-3">
                    <div class="col-6">
                        <strong><i class="fas fa-utensils"></i> Servings:</strong> ${recipe.servings || 'N/A'}
                    </div>
                    <div class="col-6">
                        <strong><i class="fas fa-clock"></i> Ready in:</strong> ${recipe.readyInMinutes || 'N/A'} minutes
                    </div>
                </div>
                <h6><i class="fas fa-carrot"></i> Ingredients:</h6>
                <ul class="mb-3">
                    ${ingredientsHtml}
                </ul>
                <h6><i class="fas fa-list-ol"></i> Instructions:</h6>
                <div class="mb-3" style="max-height: 200px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    ${recipe.instructions || 'No instructions available.'}
                </div>
            `;
            
            // Show modal using Bootstrap 5 proper method
            const modalElement = document.getElementById('recipeModal');
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true
            });
            
            // Show the modal
            modal.show();
            
            // Clean up when modal is hidden
            modalElement.addEventListener('hidden.bs.modal', function () {
                console.log('Modal closed, cleaning up...');
                // Force cleanup
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => backdrop.remove());
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }, { once: true });
            
        } catch (error) {
            console.error('Error loading recipe details:', error);
            alert('Failed to load recipe details. Please try again.');
        }
    }
    
    // Add click handler for recipe modal buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-recipe')) {
            const recipeId = e.target.dataset.id;
            viewRecipeDetails(recipeId);
        }
    });
});