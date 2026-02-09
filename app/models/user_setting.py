from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    morning_enabled = Column(Boolean, default=True)
    morning_time = Column(String, default="08:00")
    evening_enabled = Column(Boolean, default=True)
    evening_time = Column(String, default="21:00")
    fcm_token = Column(String, nullable=True)
    push_enabled = Column(Boolean, default=False)
    last_morning_summary_at = Column(String, nullable=True) # Format: YYYY-MM-DD
    last_evening_summary_at = Column(String, nullable=True) # Format: YYYY-MM-DD

    owner = relationship("User", back_populates="settings")
