from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    print("\nAll Users in Database:")
    print("=====================")
    for user in users:
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print("---------------------")
