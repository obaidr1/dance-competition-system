import os
import shutil
from app import app, db, User
from werkzeug.security import generate_password_hash

# Delete existing database and migrations
if os.path.exists('dance.db'):
    os.remove('dance.db')
    print("Deleted existing database")

if os.path.exists('migrations'):
    shutil.rmtree('migrations')
    print("Deleted existing migrations")

# Create tables
with app.app_context():
    db.create_all()
    print("Created database tables")

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
    print("\nAdmin user created successfully!")
    print("\nAdmin credentials:")
    print("Username: admin")
    print("Password: admin123")
