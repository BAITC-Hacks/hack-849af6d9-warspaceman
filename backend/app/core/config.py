import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8100").rstrip("/")
