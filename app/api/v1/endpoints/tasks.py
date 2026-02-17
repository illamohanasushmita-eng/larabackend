from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, PlanResponse, SummaryResponse, VoiceProcessRequest, VoiceProcessResponse
from app.services import task_service, ai_service, mappls_service
import logging

logger = logging.getLogger(__name__)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await task_service.create_new_task(db, task, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process-voice", response_model=VoiceProcessResponse)
async def process_voice(
    request: VoiceProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await ai_service.process_voice_command(request.text, db, current_user.id, request.current_time)
    
    # 🗺️ MAPPLS INTEGRATION
    intent = res.get("intent")
    
    if intent == "NearbySearch":
        category = res.get("category")
        if request.lat and request.lng:
            logger.info(f"🗺️ Executing Nearby Search for '{category}' at {request.lat}, {request.lng}")
            places = await mappls_service.MapplsService.search_nearby(category, request.lat, request.lng)
            
            # Format conversational response
            formatted_msg = mappls_service.MapplsService.format_places_response(places, category)
            res["message"] = formatted_msg
            res["type"] = "map_search" # Frontend can use this to show a map UI if needed
            res["status"] = "ready" # Ensure it's ready
            res["nearby_places"] = places[:5]  # Return top 5 places for UI display
        else:
            res["message"] = "I can find places for you, but I need your location access."
            res["status"] = "incomplete"

    elif intent == "Directions":
        # Placeholder for routing
        pass
    
    # 🎯 Overlap Check for Voice Command (Only for Tasks)
    if intent == "CreateTask" and res.get("status") == "ready" and res.get("time"):
        from dateutil import parser
        try:
            start_t = parser.parse(res["time"])
            end_t = parser.parse(res["end_time"]) if res.get("end_time") else None
            
            conflict = await task_service.check_time_overlap(db, current_user.id, start_t, end_t)
            if conflict:
                from datetime import timedelta
                ist_time = conflict.due_date + timedelta(hours=5, minutes=30)
                time_str = ist_time.strftime("%I:%M %p")
                
                # Update message to warn user
                conflict_msg = f"Wait, you already have a {conflict.type} at {time_str} ('{conflict.title}'). Would you like to choose another slot?"
                res["message"] = conflict_msg
                # Optionally, we can set status back to incomplete so the UI continues listening for a new time
                # but for now let's just warn and let user decide if they want to force it or click cancel.
                # Actually user said "dont add overlap tasks".
                res["status"] = "incomplete" 
        except Exception as e:
            print(f"Overlap check error: {e}")

    return res


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_tasks(db, skip=skip, limit=limit, user_id=current_user.id)

@router.get("/plan/", response_model=PlanResponse)
async def get_daily_plan(
    date: Optional[str] = None, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_daily_plan(db, date_str=date, user_id=current_user.id)

@router.get("/summary/", response_model=SummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_end_of_day_summary(db, user_id=current_user.id)

@router.get("/insights")
async def get_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_user_insights(db, user_id=current_user.id)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = await task_service.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, 
    task: TaskUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_task = await task_service.update_task_status(db, task_id, task, current_user.id)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(
    task_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_task = await task_service.delete_task(db, task_id, current_user.id)
    if not deleted_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return deleted_task

@router.post("/{task_id}/postpone", response_model=TaskResponse)
async def postpone_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Postpone task reminder - updates last_nudged_at so backend waits 30min before next nudge"""
    postponed_task = await task_service.postpone_task_reminder(db, task_id, current_user.id)
    if not postponed_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return postponed_task
