"""Database setup with SQLAlchemy."""
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserBehaviorData(Base):
    """Bảng lưu hành vi người dùng."""
    __tablename__ = "user_behavior_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    product_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # view, click, add_to_cart, purchase, search, wishlist, remove_from_cart, review
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
