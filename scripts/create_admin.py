import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            dance_role='leader',
            level='Advanced',
            is_admin=True,
            is_judge=True,
            is_head_judge=True,
            city='San Francisco'
        )
        admin.set_password('admin')
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")

if __name__ == '__main__':
    create_admin()
