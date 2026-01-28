# Daily Tribune News Platform

A modern news platform API built with FastAPI.

## Features

- **Article Management** (SCRUM-5)
  - Rich text editor support (SCRUM-6)
  - Publishing workflow: Draft -> Review -> Published (SCRUM-7)
  - Full-text search (SCRUM-8)
  - Scheduled publishing (SCRUM-9)

- **User Authentication** (SCRUM-10)
  - JWT with refresh tokens (SCRUM-11)
  - Social login: Google, Apple (SCRUM-12)
  - Subscription tiers: Free, Premium, VIP (SCRUM-13)
  - User profiles and preferences (SCRUM-14)

- **Comments & Community** (SCRUM-15)
  - Threaded comments (SCRUM-16)
  - Moderation system (SCRUM-17)
  - Reactions (SCRUM-18)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy
- **Database**: PostgreSQL (SCRUM-19)
- **Cache**: Redis (SCRUM-20)
- **Search**: Elasticsearch (SCRUM-21)
- **Auth**: JWT, OAuth 2.0

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
