from app.core.celery_app import celery_app

# This is the entry point for the Celery worker
# Run with: celery -A app.tasks.celery_worker worker --loglevel=info
