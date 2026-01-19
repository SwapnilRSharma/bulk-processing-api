from pydantic import BaseModel
from typing import List, Optional


class HospitalResult(BaseModel):
    row: int
    hospital_id: Optional[int]
    name: str
    status: str
    error: Optional[str] = None


class BulkUploadResponse(BaseModel):
    """Response returned immediately after upload."""

    batch_id: str
    total_hospitals: int
    message: str


class BulkResponse(BaseModel):
    """Final response with all processing results."""

    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    batch_activated: bool
    hospitals: List[HospitalResult]
