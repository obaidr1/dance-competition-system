from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Drop and recreate all tables
    db.drop_all()
    db.create_all()
    print("Database has been recreated successfully!")

    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        role='admin',
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user has been created successfully!")
    print("Email: admin@example.com")
    print("Password: admin123")
