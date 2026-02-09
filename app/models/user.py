from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    dob = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    
    # Google OAuth fields
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="owner", cascade="all, delete-orphan")
