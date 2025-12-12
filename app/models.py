import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    watches = relationship("Watch", back_populates="user", cascade="all, delete-orphan")


class Watch(Base):
    __tablename__ = "watches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prefecture = Column(String, nullable=False)
    product_url = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="watches")
    notifications = relationship("Notification", back_populates="watch", cascade="all, delete-orphan")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id = Column(UUID(as_uuid=True), ForeignKey("watches.id"), nullable=False)
    notified_at = Column(DateTime(timezone=True), server_default=func.now())
    payload_json = Column(Text, nullable=True)

    watch = relationship("Watch", back_populates="notifications")
