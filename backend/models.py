# VoiceNote UK - Database Configuration
# PostgreSQL setup with SQLAlchemy ORM (with SQLite fallback for development)

import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, UUID, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

# Database URL from environment - use SQLite if not properly configured
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Check if we should use SQLite fallback
_USE_SQLITE = False
if not DATABASE_URL or DATABASE_URL.startswith("postgresql://user:password@localhost"):
    # No valid database configured, use SQLite
    _USE_SQLITE = True
    DATABASE_URL = "sqlite:///./voicenote.db"
    print("[INFO] Using SQLite database for development. Set DATABASE_URL for PostgreSQL.")

# Create engine with appropriate settings
if _USE_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User model (linked to Clerk)
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_id = Column(String(255), unique=True, nullable=True, index=True)  # Made nullable for non-Clerk auth
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    usage_stats = relationship("UsageStats", back_populates="user", cascade="all, delete-orphan")

# Note model
class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255))
    transcript = Column(Text, nullable=False)
    summary = Column(Text)
    tone = Column(String(50))
    template_type = Column(String(50))  # 'meeting', 'lecture', 'interview', 'brainstorm', 'custom'
    audio_file_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    duration_seconds = Column(Integer)
    word_count = Column(Integer)
    is_archived = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="notes")
    key_points = relationship("KeyPoint", back_populates="note", cascade="all, delete-orphan", order_by="KeyPoint.order_index")
    action_items = relationship("ActionItem", back_populates="note", cascade="all, delete-orphan", order_by="ActionItem.order_index")
    exports = relationship("Export", back_populates="note", cascade="all, delete-orphan")

# Key Points model
class KeyPoint(Base):
    __tablename__ = "key_points"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String(36), ForeignKey("notes.id"), nullable=False, index=True)
    point = Column(Text, nullable=False)
    order_index = Column(Integer)
    is_completed = Column(Boolean, default=False)

    # Relationships
    note = relationship("Note", back_populates="key_points")

# Action Items model
class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String(36), ForeignKey("notes.id"), nullable=False, index=True)
    task = Column(Text, nullable=False)
    order_index = Column(Integer)
    is_completed = Column(Boolean, default=False)
    assigned_to = Column(String(255))
    due_date = Column(Date)

    # Relationships
    note = relationship("Note", back_populates="action_items")

# Templates model
class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # NULL for global templates
    name = Column(String(255), nullable=False)
    template_type = Column(String(50))  # 'meeting', 'lecture', 'interview', 'brainstorm', 'custom'
    prompt_template = Column(Text)  # Custom AI instruction
    sections = Column(JSON)  # Predefined sections structure
    is_global = Column(Boolean, default=False)  # System templates
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="templates")

# Usage Statistics model
class UsageStats(Base):
    __tablename__ = "usage_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, default=datetime.utcnow().date, index=True)
    notes_created = Column(Integer, default=0)
    transcription_minutes = Column(Integer, default=0)  # Total audio duration
    export_count = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="usage_stats")

# Email Logs model
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    note_id = Column(String(36), ForeignKey("notes.id"), nullable=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255))
    status = Column(String(50))  # 'sent', 'failed', 'bounced'
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)

# Exports model
class Export(Base):
    __tablename__ = "exports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String(36), ForeignKey("notes.id"), nullable=False, index=True)
    format = Column(String(50))  # 'pdf', 'docx', 'markdown'
    file_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # For temporary URLs

    # Relationships
    note = relationship("Note", back_populates="exports")

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("[INFO] Database tables created successfully!")