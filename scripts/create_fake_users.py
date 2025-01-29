import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User
from faker import Faker
import random

fake = Faker()

def create_fake_users(num_users=20):
    with app.app_context():
        # Define dance roles and levels with weights
        dance_roles = ['leader', 'follower']
        levels = ['Novice', 'Intermediate', 'Advanced', 'AllStar']
        level_weights = [0.4, 0.3, 0.2, 0.1]  # More beginners, fewer advanced dancers
        
        # Cities with dance scenes
        cities = [
            'San Francisco', 'Los Angeles', 'New York', 'Miami', 'Seattle',
            'Chicago', 'Boston', 'Austin', 'Portland', 'San Diego'
        ]
        
        # Create users
        created_users = []
        for i in range(num_users):
            # Alternate between leaders and followers to maintain balance
            dance_role = dance_roles[i % 2]
            
            # Generate user data
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            
            # Create user with random attributes
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                dance_role=dance_role,
                level=random.choices(levels, weights=level_weights)[0],
                city=random.choice(cities),
                is_judge=random.random() < 0.2,  # 20% chance of being a judge
            )
            user.set_password('password123')
            
            # Add random points based on level
            if user.level == 'Novice':
                user.novice_points = random.randint(0, 20)
            elif user.level == 'Intermediate':
                user.novice_points = 25
                user.intermediate_points = random.randint(0, 25)
            elif user.level == 'Advanced':
                user.intermediate_points = 30
                user.advanced_points = random.randint(0, 35)
            elif user.level == 'AllStar':
                user.advanced_points = 40
            
            created_users.append(user)
            db.session.add(user)
        
        try:
            db.session.commit()
            print(f"Created {num_users} fake users:")
            for user in created_users:
                print(f"- {user.first_name} {user.last_name} ({user.dance_role}, {user.level})")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating users: {str(e)}")

if __name__ == '__main__':
    create_fake_users()
