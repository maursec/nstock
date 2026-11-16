"""
Database connection for NStock.

Reads the connection string from the DATABASE_URL environment variable,
which you set in backend/.env (never commit .env):

    DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/nstock

The tables themselves come from database/nstock_schema.sql, which is the
source of truth. This file only connects to them.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Create backend/.env with a line like:\n"
        "DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/nstock"
    )

# pool_pre_ping reconnects if MySQL dropped an idle connection
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: one database session per request.

    Use it in an endpoint like this:
        def get_products(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
