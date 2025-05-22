# 📅 Event Management System API

A collaborative event/task management system built with **FastAPI**, **PostgreSQL**, **Celery**, and **Redis**.

This documentation describes how to install, configure, and run the API, including available endpoints and environment configurations.

---

## 📘 Overview

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Background Tasks:** Celery + Redis
- **Authentication:** JWT (token-based)
- **API Docs:** Swagger/OpenAPI at `/docs`, ReDoc at `/redoc`
- **Project Status:** 🚧 Under Active Development

---

## 📦 Installation

### Option 1: 🚀 Run via Docker (Recommended)

#### ✅ Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

#### 📥 Clone the Repository

```bash
git clone <repository-url>
cd event-management
```

#### ⚙️ Configure Environment Variables

Copy and edit the environment file:

```bash
cp .env.example .env
```

Edit `.env` and set at least:
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://postgres:postgres@db:5432/event_management
REDIS_URL=redis://redis:6379
#### 🏗️ Build and Start the Containers

```bash
docker-compose up --build
```

- FastAPI server: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`

---

### Option 2: 🧪 Run Locally Without Docker

#### ✅ Prerequisites

- Python 3.9+
- PostgreSQL
- pip

#### 🔧 Manual Setup

```bash
git clone <repository-url>
cd event-management
python -m venv venv
source venv/bin/activate  # On Windows use venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file manually or copy from `.env.example`:
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/event_management



Create database and run migrations:

```bash
createdb event_management
alembic upgrade head
```

Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing & Linting

- **Run tests:**  
  `pytest`

- **Code style checks:**  
  `flake8`

- **Auto-format code:**  
  `black .`

---

## 📂 Directory Structure

event-management/
│
├── app/ # Main application package
│ ├── api/ # API route definitions (FastAPI routers)
│ ├── core/ # App settings, security, JWT utilities
│ ├── db/ # Database session and base setup
│ ├── models/ # SQLAlchemy ORM models
│ ├── schemas/ # Pydantic schemas for requests/responses
│ ├── services/ # Business logic and service layer
│ └── main.py # Application entry point (FastAPI instance)
│
├── alembic/ # Alembic migrations directory
│
├── tests/ # Unit and integration tests
│
├── docker-compose.yml # Docker orchestration config
├── requirements.txt # Python dependencies
├── alembic.ini # Alembic configuration file
├── .env.example # Example environment variable file
└── README.md # Project documentation




---

## 🔐 Authentication

Authorization: Bearer <your-access-token>


- JWT token-based authentication is used.
- Use the `/api/auth/login` endpoint to obtain an access token.
- Include the token in the `Authorization` header for protected routes:


---

## 🚨 Common Pitfalls

- **Never commit your `.env` file.** Only share `.env.example`.
- Ensure ports `8000`, `5433` (Postgres), and `6379` (Redis) are free.
- Database credentials must match in both `.env` and `docker-compose.yml`.
- If you change any credentials, update them everywhere.


---

## 📮 API Reference

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

**Happy coding! For questions or contributions, open an issue or pull request.**
