from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult
from src.celery_app import celery_app

router = APIRouter(tags=["Tasks"])

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Get the status and result of a Celery task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    # For debugging, let's return more information about the task
    response = {
        "task_id": task_id,
        "status": task_result.state,
        "info": str(task_result.info) if task_result.info else None,
        "result": task_result.result if task_result.ready() else None,
    }
    
    # Add traceback for failed tasks
    if task_result.state == 'FAILURE' and task_result.traceback:
        response["traceback"] = task_result.traceback
    
    return response
