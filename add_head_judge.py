from app import app, db
from models import Competition

def add_head_judge_column():
    with app.app_context():
        # Create the head_judge_id column
        db.engine.execute('ALTER TABLE competition ADD COLUMN head_judge_id INTEGER REFERENCES user(id)')
        db.session.commit()

if __name__ == '__main__':
    add_head_judge_column()
