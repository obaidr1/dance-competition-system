# Dance Competition System

A comprehensive system for managing dance competitions, including participant registration, scoring, and results management.

## Features

- Participant registration and management
- Competition scheduling
- Real-time scoring system
- Results calculation and leaderboard
- Judge management interface

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

## Development

This project uses Python with pytest for testing.

### Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest tests/`

### Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

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
