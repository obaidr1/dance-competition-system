from app import db, create_app
from app.models import User, DanceRole, DanceLevel
from faker import Faker
import random

fake = Faker()

def create_fake_users():
    # Create 10 leaders and 10 followers with varying experience levels
    roles = [DanceRole.LEADER, DanceRole.FOLLOWER]
    levels = [
        {'level': DanceLevel.NOVICE, 'points': (0, 20)},
        {'level': DanceLevel.INTERMEDIATE, 'points': (20, 25)},
        {'level': DanceLevel.ADVANCED, 'points': (25, 35)}
    ]

    users = []
    
    for role in roles:
        for i in range(10):
            # Randomly select a level and points
            level_info = random.choice(levels)
            points = random.randint(level_info['points'][0], level_info['points'][1])
            
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                dance_role=role,
                dance_level=level_info['level'],
                points=points
            )
            user.set_password('password123')  # Set a default password
            users.append(user)
    
    return users

def main():
    app = create_app()
    with app.app_context():
        # Create users
        users = create_fake_users()
        
        # Add users to database
        for user in users:
            db.session.add(user)
        
        try:
            db.session.commit()
            print("Successfully created fake users!")
            
            # Print summary
            print("\nCreated Users Summary:")
            for user in users:
                print(f"Username: {user.username}, Role: {user.dance_role.name}, "
                      f"Level: {user.dance_level.name}, Points: {user.points}")
        
        except Exception as e:
            print(f"Error creating users: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main()
