from app import app, db
from models import Competition

def update_competition_model():
    with app.app_context():
        # Get all competitions
        competitions = Competition.query.all()
        
        # Update each competition's scoring dimensions
        for competition in competitions:
            # Get existing dimensions in whatever format they're in
            dimensions = competition.get_scoring_dimensions()
            # Set them back using the new format
            competition.set_scoring_dimensions(dimensions)
        
        # Commit all changes
        db.session.commit()
        print("Successfully updated competition models")
