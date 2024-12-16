# Jack & Jill Dance Competition Management System

A web application for managing Jack & Jill dance competitions, including features for competition organization, judging, and result tracking.

[![codecov](https://codecov.io/gh/obaidr1/dance-competition-system/branch/master/graph/badge.svg)](https://codecov.io/gh/obaidr1/dance-competition-system)

## Features

### Admin Panel
- Create and manage multiple Jack & Jill competitions
- Add, edit, and delete dancers with detailed profiles
- Manage competition rounds and advancement
- Random pairing generation for each round

### Judge Panel
- Secure login system for judges
- Scoring interface with multiple criteria:
  - Timing
  - Technique
  - Partner Connection
  - Musical Interpretation
  - Presentation
- Real-time score submission

### Public Results
- View competition results and rankings
- Dynamic updates as rounds progress
- Detailed scoring breakdown

## Project Structure
```
├── app.py              # Main Flask application
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Custom styles
│   └── js/
│       └── main.js    # Frontend JavaScript
└── templates/
    └── base.html      # Base template
```

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://localhost:5000`

## User Roles

### Admin
- Create and manage competitions
- Add and manage dancers
- Generate round pairings
- View all competition data

### Judge
- Access assigned competitions
- Submit scores for dance pairs
- View competition progress

### Public
- View competition results
- Track competition progress

## Competition Structure

### Divisions
- Newcomer
- Novice
- Intermediate
- Advanced
- All-Star
- Champions
- Junior/Masters

### Rounds
- Preliminary
- Semi-final
- Final

## Security
- Secure user authentication
- Role-based access control
- Protected API endpoints

## Technologies Used
- Flask (Python web framework)
- SQLAlchemy (Database ORM)
- Bootstrap (Frontend framework)
- JavaScript (Dynamic frontend functionality)
