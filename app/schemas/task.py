from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    raw_text: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = "task"
    due_date: Optional[datetime] = None
    end_time: Optional[datetime] = None
    med_timing: Optional[str] = None

    @field_validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('description')
    def sanitize_description(cls, v):
        if v:
            return v.strip()
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    due_date: Optional[datetime] = None
    end_time: Optional[datetime] = None
    med_timing: Optional[str] = None
    external_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    status: str
    type: str
    created_at: datetime
    updated_at: datetime
    external_id: Optional[str] = None
    is_external: bool = False
    
    @property
    def is_completed(self) -> bool:
        return self.status == 'completed'

    class Config:
        from_attributes = True

class PlanSection(BaseModel):
    slot: str  # Morning, Afternoon, Evening, Night
    items: List[TaskResponse]

class PlanResponse(BaseModel):
    morning_message: str
    user_name: str
    sections: List[PlanSection]
    total_count: int
    time_bound_count: int
    upcoming: List[TaskResponse] = []

class SummaryResponse(BaseModel):
    completed_count: int
    pending_count: int
    message: str
    pending_items: List[TaskResponse]

class VoiceProcessRequest(BaseModel):
    text: str
    current_time: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class VoiceProcessResponse(BaseModel):
    status: str # "idle", "incomplete", "ready", "error"
    title: str = "New Task"
    corrected_sentence: str
    time: Optional[str] = None
    end_time: Optional[str] = None
    type: str = "task"
    message: str
    is_cancelled: bool = False




