from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print("Admin user already exists!")
            return

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
        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: admin123")

if __name__ == '__main__':
    create_admin()
