import asyncio
from fastapi import WebSocket
from app.state import bulk_progress


async def bulk_progress_ws(websocket: WebSocket, batch_id: str):
    await websocket.accept()

    while True:
        if batch_id not in bulk_progress:
            await websocket.send_json({"error": "Batch not found"})
            break

        await websocket.send_json(bulk_progress[batch_id])

        if bulk_progress[batch_id]["status"] in ("completed", "partial_failed"):
            break

        await asyncio.sleep(1)
