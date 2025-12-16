from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import text
import os
from dotenv import load_dotenv
import requests 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///auntypantry.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# FIX FOR PSYCOPG3: Convert postgres:// to postgresql+psycopg://
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database models
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    ingredients = db.relationship('Ingredient', backref='owner', lazy=True)

class Ingredient(db.Model):
    __tablename__ = 'user_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

with app.app_context():
    try:
        print("🔄 Checking/Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Optional: Test the connection
        result = db.session.execute(text('SELECT 1'))
        print(f"✅ Database connection test passed: {result.fetchone()}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Basic routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/test-db')
def test_db():
    try:
        db.session.execute(text('SELECT 1')) 
        return 'Database connection successful!'
    except Exception as e:
        return f'Database connection failed: {str(e)}'

# A simple test route to verify the app is running
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'app': 'Aunty Pantry',
        'version': '1.0.0'
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password_hash=hashed_password, name=name)
    db.session.add(user)
    db.session.commit()
    
    # Auto-login after registration
    login_user(user, remember=True)
    
    return jsonify({
        'message': 'Registration successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/logout')
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('home'))

@app.route('/api/current-user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name
        })
    return jsonify({'user': None})

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's ingredients
    user_ingredients = Ingredient.query.filter_by(user_id=current_user.id).all()
    ingredients_list = [ing.ingredient_name for ing in user_ingredients]
    
    return render_template('dashboard.html', 
                         ingredients=user_ingredients,
                         ingredients_list=ingredients_list)

# Ingredient CRUD API
@app.route('/api/ingredients', methods=['POST'])
@login_required
def handle_ingredients():
    if request.method == 'POST':
        # Add new ingredient
        data = request.get_json()
        ingredient_name = data.get('name', '').strip()
        
        if not ingredient_name:
            return jsonify({'error': 'Ingredient name is required'}), 400
        
        # Check if ingredient already exists for this user
        existing = Ingredient.query.filter_by(
            user_id=current_user.id,
            ingredient_name=ingredient_name
        ).first()
        
        if existing:
            return jsonify({'error': 'Ingredient already in your pantry'}), 400
        
        # Create new ingredient
        ingredient = Ingredient(
            ingredient_name=ingredient_name,
            user_id=current_user.id
        )
        db.session.add(ingredient)
        db.session.commit()
        
        return jsonify({
            'id': ingredient.id,
            'name': ingredient.ingredient_name,
            'date_added': ingredient.date_added.isoformat()
        }), 201
    
    else:  # GET request
        # Get all user's ingredients
        ingredients = Ingredient.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': ing.id,
            'name': ing.ingredient_name,
            'date_added': ing.date_added.isoformat()
        } for ing in ingredients])

@app.route('/api/ingredients/<int:ingredient_id>', methods=['DELETE'])
@login_required
def delete_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    # Verify user owns this ingredient
    if ingredient.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(ingredient)
    db.session.commit()
    return jsonify({'message': 'Ingredient deleted'})

# Spoonacular API Integration
@app.route('/api/find-recipes')
@login_required
def find_recipes():
    # Get user's ingredients
    ingredients = Ingredient.query.filter_by(user_id=current_user.id).all()
    
    if not ingredients:
        return jsonify([])
    
    # Extract ingredient names
    ingredient_names = [ing.ingredient_name for ing in ingredients]
    
    # Get API key from environment
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    
    if not api_key:
        return jsonify({'error': 'API key not configured'}), 500
    
    # Prepare ingredients string (comma-separated, max 5 for better results)
    ingredients_str = ','.join(ingredient_names[:5])
    
    try:
        # Call Spoonacular API
        url = f"https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            'ingredients': ingredients_str,
            'number': 6,  # Get 6 recipes
            'ranking': 2,  # Maximize used ingredients
            'ignorePantry': True,  # Ignore water, salt, etc.
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        
        recipes_data = response.json()
        
        # Format the response
        formatted_recipes = []
        for recipe in recipes_data:
            formatted_recipes.append({
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe['image'],
                'usedIngredientCount': recipe['usedIngredientCount'],
                'missedIngredientCount': recipe['missedIngredientCount'],
                'missedIngredients': [ing['name'] for ing in recipe.get('missedIngredients', [])],
                'usedIngredients': [ing['name'] for ing in recipe.get('usedIngredients', [])]
            })
        
        return jsonify(formatted_recipes)
        
    except requests.exceptions.RequestException as e:
        print(f"Spoonacular API error: {e}")
        # Fallback to mock data if API fails
        return get_mock_recipes(ingredient_names)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Failed to fetch recipes'}), 500

def get_mock_recipes(ingredient_names):
    """Fallback mock recipes if API fails"""
    mock_recipes = [
        {
            'id': 1,
            'title': f'Chicken with {ingredient_names[0] if ingredient_names else "Vegetables"}',
            'image': 'https://spoonacular.com/recipeImages/1-312x231.jpg',
            'usedIngredientCount': min(2, len(ingredient_names)),
            'missedIngredientCount': 3,
            'missedIngredients': ['olive oil', 'garlic', 'salt'],
            'usedIngredients': ingredient_names[:2] if len(ingredient_names) >= 2 else ingredient_names
        },
        {
            'id': 2,
            'title': f'Stir Fry with {ingredient_names[0] if ingredient_names else "Ingredients"}',
            'image': 'https://spoonacular.com/recipeImages/2-312x231.jpg',
            'usedIngredientCount': min(1, len(ingredient_names)),
            'missedIngredientCount': 4,
            'missedIngredients': ['soy sauce', 'ginger', 'onion', 'sesame oil'],
            'usedIngredients': ingredient_names[:1] if ingredient_names else []
        }
    ]
    return mock_recipes

@app.route('/api/recipe/<int:recipe_id>')
@login_required
def get_recipe_details(recipe_id):
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    
    if not api_key:
        # Return mock data if no API key
        return get_mock_recipe_details(recipe_id)
    
    try:
        # Get recipe information
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {
            'apiKey': api_key,
            'includeNutrition': False
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        recipe_data = response.json()
        
        # Format the response
        formatted_recipe = {
            'id': recipe_data['id'],
            'title': recipe_data['title'],
            'image': recipe_data['image'],
            'servings': recipe_data.get('servings', 1),
            'readyInMinutes': recipe_data.get('readyInMinutes', 30),
            'sourceUrl': recipe_data.get('sourceUrl', '#'),
            'instructions': recipe_data.get('instructions', 'No instructions available.'),
            'ingredients': []
        }
        
        # Extract ingredients
        if 'extendedIngredients' in recipe_data:
            formatted_recipe['ingredients'] = [
                f"{ing['amount']} {ing['unit']} {ing['name']}" 
                for ing in recipe_data['extendedIngredients']
            ]
        
        return jsonify(formatted_recipe)
        
    except requests.exceptions.RequestException as e:
        print(f"Spoonacular API error for recipe {recipe_id}: {e}")
        return get_mock_recipe_details(recipe_id)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Failed to fetch recipe details'}), 500

def get_mock_recipe_details(recipe_id):
    """Fallback mock recipe details"""
    return jsonify({
        'id': recipe_id,
        'title': f'Delicious Recipe #{recipe_id}',
        'image': f'https://spoonacular.com/recipeImages/{recipe_id}-312x231.jpg',
        'servings': 4,
        'readyInMinutes': 30,
        'sourceUrl': f'https://spoonacular.com/recipe/{recipe_id}',
        'instructions': '1. Prepare all ingredients. 2. Cook according to your preference. 3. Serve hot and enjoy!',
        'ingredients': [
            '2 cups main ingredient',
            '1 tablespoon oil',
            'Salt and pepper to taste',
            '1 teaspoon herbs'
        ]
    })

# Debug routes for testing
@app.route('/debug/env')
def debug_env():
    return jsonify({
        'api_key_exists': bool(os.environ.get('SPOONACULAR_API_KEY')),
        'api_key_length': len(os.environ.get('SPOONACULAR_API_KEY', '')) if os.environ.get('SPOONACULAR_API_KEY') else 0,
    })

@app.route('/test-api')
def test_api():
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    
    if not api_key:
        return "❌ API key not found in .env file"
    
    try:
        # Simple test call to Spoonacular
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            'apiKey': api_key,
            'query': 'pasta',
            'number': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            return f"✅ API key works! Status: {response.status_code}"
        elif response.status_code == 401:
            return f"❌ API key is INVALID (401 Unauthorized)"
        else:
            return f"⚠️ API returned status: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("=== Aunty Pantry Starting ===")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Server running at: http://localhost:5000")
        print("=============================")
    app.run(debug=True)
