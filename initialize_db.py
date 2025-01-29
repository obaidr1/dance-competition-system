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
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        first_name='Admin',
        last_name='User',
        dance_role='leader',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("\nAdmin user created successfully!")
    print("\nAdmin credentials:")
    print("Email: admin@example.com")
    print("Password: admin123")
