from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .database import engine, Base
from .api.routers import auth, tasks
from .api.routers.devices import router as devices_router
from .api.routers.ssh import router as ssh_router
from .tasks import update_device_reachability_status

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize scheduler
scheduler = AsyncIOScheduler()


def scheduled_task(trigger, **job_kwargs):
    def decorator(func):
        scheduler.add_job(func, trigger, **job_kwargs)
        return func

    return decorator


@scheduled_task(IntervalTrigger(seconds=5), coalesce=True, max_instances=1)
async def schedule_update_device_reachability_status():
    await update_device_reachability_status()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="SDN Controller API",
    description="API to manage network devices and run commands using a modular, OOP controller.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - adjust for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the API routers
app.include_router(auth.router, prefix="/api")
app.include_router(devices_router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(ssh_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to the SDN Controller API", "docs": "/docs"}
