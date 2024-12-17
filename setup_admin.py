from app import app, db, User
from werkzeug.security import generate_password_hash

# Create admin user
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
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
        print("Admin user created successfully!")
        print("\nAdmin credentials:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Admin user already exists")
