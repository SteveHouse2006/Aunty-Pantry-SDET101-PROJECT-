# Aunty Pantry

A Flask-based web application that helps users manage pantry ingredients and discover recipes. The system connects user ingredient data with the Spoonacular API to provide personalized cooking suggestions.

## Core Features

### 🧾 **Ingredient Management**
- User authentication system with secure password hashing
- Persistent pantry storage in PostgreSQL database
- CRUD operations for ingredient inventory via RESTful API

### 🍳 **Recipe Discovery Engine**
- Real-time integration with Spoonacular API
- Algorithmic matching of pantry items to recipes
- Recipe details including ingredients, instructions, and preparation time
- Fallback mock data when API is unavailable

### 🏗️ **Technical Architecture**
- **Backend:** Flask 2.3.3 with SQLAlchemy ORM
- **Frontend:** Responsive HTML/CSS/JavaScript interface
- **Database:** PostgreSQL (production) / SQLite (development)
- **Authentication:** Flask-Login with session management
- **Deployment:** Containerized on Render with gunicorn WSGI

## System Endpoints

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| **Authentication** | `POST /api/register`, `POST /api/login`, `GET /api/current-user` | User account management and session handling |
| **Pantry API** | `GET/POST /api/ingredients`, `DELETE /api/ingredients/<id>` | Full ingredient lifecycle management |
| **Recipe Service** | `GET /api/find-recipes`, `GET /api/recipe/<id>` | External API integration with data processing |
| **System Health** | `GET /health`, `GET /test-db` | Deployment monitoring and diagnostics |

## Data Model

```
User
├── id (Primary Key)
├── email (Unique)
├── password_hash (Bcrypt)
├── name
└── ingredients (One-to-Many)
    └── Ingredient
        ├── ingredient_name
        └── user_id (Foreign Key)
```

## Key Technical Decisions

1. **Database Abstraction:** SQLAlchemy enables seamless transition between SQLite (development) and PostgreSQL (production)
2. **Error Resilience:** Graceful fallback to mock recipe data when external API fails
3. **Security:** Password hashing via Flask-Bcrypt, environment-based configuration
4. **Deployment:** Python 3.11.9 for compatibility with psycopg2 database adapter

## External Integration

- **Spoonacular API:** Primary recipe data source with parameterized queries
- **Render Platform:** Automated deployment with managed PostgreSQL and health checks

---

**Live Application:** [https://aunty-pantry.onrender.com](https://aunty-pantry.onrender.com)  
**Source Code:** [https://github.com/SteveHouse2006/Aunty-Pantry-SDET101-PROJECT](https://github.com/SteveHouse2006/Aunty-Pantry-SDET101-PROJECT)

*This project demonstrates full-stack development with Flask, external API integration, and cloud deployment.*
