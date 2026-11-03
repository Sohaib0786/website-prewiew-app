from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    sites = relationship("Site", back_populates="owner", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    preview_file = Column(String(255), nullable=False)
    # screenshot | thumbnail | og_image | placeholder
    preview_type = Column(String(30), nullable=False, default="screenshot")
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    owner = relationship("User", back_populates="sites")
