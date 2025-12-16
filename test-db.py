# test_db.py
from app import app, db, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

with app.app_context():
    # Create all tables
    db.create_all()
    print("✓ Aunty Pantry tables created successfully")
    
    # Test user creation
    hashed_pw = bcrypt.generate_password_hash('test123').decode('utf-8')
    test_user = User(email='test@example.com', password_hash=hashed_pw, name='Test User')
    db.session.add(test_user)
    db.session.commit()
    print("✓ Test user created successfully")
    
    # Query user
    user = User.query.filter_by(email='test@example.com').first()
    print(f"✓ User retrieved: {user.email}")
    
    # Check password
    if bcrypt.check_password_hash(user.password_hash, 'test123'):
        print("✓ Password verification works!")
    
    print("\n=== Aunty Pantry Database Test Complete ===")