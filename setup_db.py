import os
from app import app, db, User
from werkzeug.security import generate_password_hash

# Delete existing database
if os.path.exists('dance.db'):
    os.remove('dance.db')
    print("Deleted existing database")

# Create new database with updated schema
with app.app_context():
    db.create_all()
    print("Created new database with updated schema")

    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        role='admin',
        city='San Francisco',
        city_id=5391959,
        country='United States',
        country_code='US',
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Created admin user")
    print("\nAdmin credentials:")
    print("Username: admin")
    print("Password: admin123")
