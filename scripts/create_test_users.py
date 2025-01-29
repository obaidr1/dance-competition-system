import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User

def create_test_users():
    with app.app_context():
        # Create 10 leaders
        leaders = [
            {
                'email': f'leader{i}@test.com',
                'password': 'password123',
                'first_name': f'Leader{i}',
                'last_name': 'Test',
                'dance_role': 'leader',
                'level': 'Novice',
                'city': 'Test City',
                'is_admin': False,
                'is_judge': False
            } for i in range(1, 11)
        ]

        # Create 10 followers
        followers = [
            {
                'email': f'follower{i}@test.com',
                'password': 'password123',
                'first_name': f'Follower{i}',
                'last_name': 'Test',
                'dance_role': 'follower',
                'level': 'Novice',
                'city': 'Test City',
                'is_admin': False,
                'is_judge': False
            } for i in range(1, 11)
        ]

        # Create all users
        for user_data in leaders + followers:
            # Check if user already exists
            if not User.query.filter_by(email=user_data['email']).first():
                user = User()
                user.email = user_data['email']
                user.set_password(user_data['password'])
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.dance_role = user_data['dance_role']
                user.level = user_data['level']
                user.city = user_data['city']
                user.is_admin = user_data['is_admin']
                user.is_judge = user_data['is_judge']
                db.session.add(user)
        
        try:
            db.session.commit()
            print("Successfully created test users!")
            print("\nLeaders:")
            for l in leaders:
                print(f"Email: {l['email']}, Password: {l['password']}")
            print("\nFollowers:")
            for f in followers:
                print(f"Email: {f['email']}, Password: {f['password']}")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test users: {str(e)}")

if __name__ == '__main__':
    create_test_users()
