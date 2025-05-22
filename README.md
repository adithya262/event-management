# Event Management System

A collaborative event management system built with FastAPI and PostgreSQL.

## Features

- User authentication and authorization
- Event creation and management
- Task assignment and tracking
- Real-time collaboration
- API documentation with Swagger UI

## Prerequisites

- Python 3.9+
- PostgreSQL
- pip (Python package manager)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd event-management
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/event_management
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
API_V1_STR=/api/v1
PROJECT_NAME=Event Management System
```

5. Create the database:
```bash
createdb event_management
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation will be available at `http://localhost:8000/docs`

## Project Structure

```
event-management/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core functionality
│   ├── db/              # Database configuration
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test files
├── .env                 # Environment variables
├── .gitignore          # Git ignore file
├── alembic.ini         # Alembic configuration
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Check code style: `flake8`

## License

This project is licensed under the MIT License. 