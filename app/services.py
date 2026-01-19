import time
import httpx
from app.config import HOSPITAL_DIRECTORY_BASE_URL
from app.models import HospitalResult
from app.state import bulk_progress, failed_batches, batch_results


async def process_hospitals_background(rows, batch_id: str):
    """Background task to process hospitals asynchronously."""
    results = []

    bulk_progress[batch_id] = {
        "total": len(rows),
        "processed": 0,
        "failed": 0,
        "status": "processing",
    }

    start = time.time()

    async with httpx.AsyncClient(
        base_url=HOSPITAL_DIRECTORY_BASE_URL, timeout=httpx.Timeout(30.0, connect=10.0)
    ) as client:
        for idx, row in enumerate(rows, start=1):
            try:
                payload = {
                    "name": row["name"],
                    "address": row["address"],
                    "phone": row.get("phone"),
                    "creation_batch_id": batch_id,
                }

                res = await client.post("/hospitals/", json=payload)
                res.raise_for_status()
                data = res.json()

                results.append(
                    HospitalResult(
                        row=idx, hospital_id=data["id"], name=data["name"], status="created"
                    )
                )

                bulk_progress[batch_id]["processed"] += 1

            except Exception as e:
                print(f"Error processing hospital {idx}: {e}")
                results.append(
                    HospitalResult(
                        row=idx,
                        hospital_id=None,
                        name=row.get("name", ""),
                        status="failed",
                        error=str(e),
                    )
                )

                bulk_progress[batch_id]["failed"] += 1
                failed_batches.setdefault(batch_id, []).append(row)

        # Activate batch if all succeeded
        if bulk_progress[batch_id]["failed"] == 0:
            try:
                await client.patch(f"/hospitals/batch/{batch_id}/activate")
                for r in results:
                    r.status = "created_and_activated"
                bulk_progress[batch_id]["status"] = "completed"
                activated = True
            except Exception:
                bulk_progress[batch_id]["status"] = "completed"
                activated = False
        else:
            bulk_progress[batch_id]["status"] = "partial_failed"
            activated = False

    duration = round(time.time() - start, 2)

    # Store final results
    batch_results[batch_id] = {
        "batch_id": batch_id,
        "total_hospitals": len(rows),
        "processed_hospitals": bulk_progress[batch_id]["processed"],
        "failed_hospitals": bulk_progress[batch_id]["failed"],
        "processing_time_seconds": duration,
        "batch_activated": activated,
        "hospitals": results,
    }
