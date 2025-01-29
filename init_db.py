from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            dance_role='leader',
            level='advanced',
            is_admin=True,
            is_organizer=True,
            is_judge=True,
            is_dancer=True
        )
        
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
