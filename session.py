import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager
from app.core.config import DBConfig
from app.core.logger_setup import logger

# Construct the DATABASE_URL
DATABASE_URL = DBConfig.db_uri

# Create the SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created successfully.")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create a session maker
SessionLocal = sessionmaker(bind=engine)

# Define the Base class for your models
Base = declarative_base()

# Dependency to get the SQLAlchemy session
@contextmanager
def scoped_context(auto_flush=True):
    session = SessionLocal(autoflush=auto_flush)
    try:
        yield session
    finally:
        session.close()
