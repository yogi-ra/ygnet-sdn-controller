from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import engine, Base
from .api.routers import auth, devices
from .tasks import check_device_for_changes, update_device_reachability_status # Import new task

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SDN Controller API",
    description="API to manage network devices and run commands using a modular, OOP controller.",
    version="1.0.0",
)

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Include the API routers
app.include_router(auth.router, prefix="/api")
app.include_router(devices.router, prefix="/api")


def scheduled_task(trigger):
    def decorator(func):
        scheduler.add_job(func, trigger)
        return func
    return decorator


@scheduled_task(IntervalTrigger(minutes=5))
async def schedule_check_device_for_changes():
    await check_device_for_changes()


@scheduled_task(IntervalTrigger(seconds=5))
async def schedule_update_device_reachability_status():
    await update_device_reachability_status()


@app.on_event("startup")
async def startup_event():
    scheduler.start()



@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.get("/")
def read_root():
    return {"message": "Welcome to the SDN Controller API", "docs": "/docs"}
