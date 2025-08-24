from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import engine, Base
from .api.routers import auth, devices
from .tasks import check_device_for_changes

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


@app.on_event("startup")
async def startup_event():
    # Add the job to the scheduler
    # Runs every 5 minutes
    scheduler.add_job(check_device_for_changes, "interval", minutes=5)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.get("/")
def read_root():
    return {"message": "Welcome to the SDN Controller API", "docs": "/docs"}
