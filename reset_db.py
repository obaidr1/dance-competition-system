from app import app, db
from werkzeug.security import generate_password_hash

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        from models import User
        admin = User(
            username='mail@obaid.de',
            email='mail@obaid.de',
            password=generate_password_hash('obaid123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        print("Database reset complete. Admin user created.")

if __name__ == '__main__':
    reset_database()
