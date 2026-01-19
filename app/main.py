import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, BackgroundTasks
from app.utils import parse_and_validate_csv
from app.services import process_hospitals_background
from app.models import BulkResponse, BulkUploadResponse
from app.state import bulk_progress, failed_batches, batch_results
from app.ws import bulk_progress_ws

app = FastAPI(title="Hospital Bulk Processing API")


@app.post("/hospitals/bulk", response_model=BulkUploadResponse)
async def bulk_create(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a CSV file for bulk hospital creation.
    Returns immediately with a batch_id. Track progress via WebSocket or status endpoint.
    """
    try:
        rows = parse_and_validate_csv(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    batch_id = str(uuid.uuid4())

    # Initialize progress tracking
    bulk_progress[batch_id] = {"total": len(rows), "processed": 0, "failed": 0, "status": "queued"}

    # Schedule background processing
    background_tasks.add_task(run_async_task, rows, batch_id)

    return BulkUploadResponse(
        batch_id=batch_id,
        total_hospitals=len(rows),
        message="Processing started. Track progress via WebSocket or status endpoint.",
    )


async def run_async_task(rows, batch_id: str):
    await process_hospitals_background(rows, batch_id)


@app.get("/hospitals/bulk/{batch_id}/status")
def bulk_status(batch_id: str):
    """Get current processing status for a batch."""
    if batch_id not in bulk_progress:
        raise HTTPException(status_code=404, detail="Batch not found")
    return bulk_progress[batch_id]


@app.get("/hospitals/bulk/{batch_id}/results", response_model=BulkResponse)
def bulk_results(batch_id: str):
    """Get final results for a completed batch."""
    if batch_id not in batch_results:
        if batch_id in bulk_progress:
            status = bulk_progress[batch_id]["status"]
            if status in ("queued", "processing"):
                raise HTTPException(
                    status_code=202, detail=f"Batch is still {status}. Check back later."
                )
        raise HTTPException(status_code=404, detail="Batch not found")

    return BulkResponse(**batch_results[batch_id])


@app.post("/hospitals/bulk/{batch_id}/retry")
async def retry_batch(batch_id: str, background_tasks: BackgroundTasks):
    """Retry failed hospitals from a batch."""
    if batch_id not in failed_batches:
        raise HTTPException(status_code=404, detail="No failed batch")

    rows = failed_batches.pop(batch_id)

    bulk_progress[batch_id] = {"total": len(rows), "processed": 0, "failed": 0, "status": "queued"}

    background_tasks.add_task(run_async_task, rows, batch_id)

    return {
        "batch_id": batch_id,
        "retrying_hospitals": len(rows),
        "message": "Retry started. Track progress via WebSocket or status endpoint.",
    }


@app.websocket("/ws/bulk/{batch_id}")
async def websocket_endpoint(websocket: WebSocket, batch_id: str):
    await bulk_progress_ws(websocket, batch_id)
