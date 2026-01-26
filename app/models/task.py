from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.timezone import get_ist_time

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String, index=True)
    raw_text = Column(String, nullable=True) # Storing original voice input
    description = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)
    type = Column(String, default="task", index=True) # task | reminder
    due_date = Column(DateTime(timezone=True), nullable=True)
    notified_10m = Column(Boolean, default=False)
    notified_20m = Column(Boolean, default=False)
    notified_due = Column(Boolean, default=False)
    notified_completion = Column(Boolean, default=False)
    notified_30m_post = Column(Boolean, default=False)
    last_nudged_at = Column(DateTime(timezone=True), nullable=True) # Last time user was nudged
    med_timing = Column(String, nullable=True) # e.g. "morning,afternoon,night"
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime(timezone=True), default=get_ist_time)
    updated_at = Column(DateTime(timezone=True), default=get_ist_time, onupdate=get_ist_time)

    owner = relationship("User", back_populates="tasks")
