from fastapi import APIRouter
from schema.app import TopicRequest
from services.queue_service import enqueue_job

router = APIRouter()


@router.post("/generate")
async def generate(req: TopicRequest):
    """Queue a report generation job and return job ID instantly"""
    job_id = await enqueue_job(req.topic, job_type="report")
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Report queued. Connect to /status/{job_id} for SSE updates or /jobs/{job_id} for latest status."
    }


@router.post("/download")
async def download(req: TopicRequest):
    """Queue a PDF generation job and return job ID instantly"""
    job_id = await enqueue_job(req.topic, job_type="pdf")
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"PDF queued. Connect to /pdf-status/{job_id} for SSE updates or /jobs/{job_id} for latest status."
    }
