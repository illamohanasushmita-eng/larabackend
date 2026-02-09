from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import AsyncSessionLocal
from app.services.notification_service import check_and_send_notifications
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_task_check():
    """Background task that runs every minute"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("⏰ Running scheduled task check...")
            await check_and_send_notifications(db)
        except Exception as e:
            logger.error(f"❌ Error in scheduled task check: {e}")

def start_scheduler():
    """Start the APScheduler background job"""
    if not scheduler.running:
        scheduler.add_job(
            scheduled_task_check, 
            "interval", 
            minutes=1,
            id="task_notification_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("🚀 Background Scheduler started (Runs every 1 min)")

def shutdown_scheduler():
    """Shut down the scheduler on app exit"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background Scheduler stopped")
