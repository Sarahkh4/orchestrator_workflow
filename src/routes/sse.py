from fastapi import APIRouter
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from services.queue_service import get_job_status, redis_client
import json
import asyncio
from pathlib import Path

from fastapi import HTTPException

router = APIRouter()


async def stream_events(job_id: str):
    """Reusable event streaming logic for any job ID"""
    current_status = await get_job_status(job_id)
    if current_status:
        yield {"data": json.dumps(current_status)}
        if current_status["status"] in ("completed", "failed"):
            return

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(job_id)

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=30
            )
            if message:
                data = json.loads(message["data"])
                yield {"data": json.dumps(data)}

                if data["status"] in ("completed", "failed"):
                    break

            await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe(job_id)


@router.get("/status/{job_id}")
async def report_status(job_id: str):
    """SSE endpoint for report jobs"""
    return EventSourceResponse(stream_events(job_id))


@router.get("/jobs/{job_id}")
async def job_status(job_id: str):
    """Fetch latest persisted job status without opening an SSE stream."""
    status = await get_job_status(job_id)
    return status or {"job_id": job_id, "status": "unknown"}


@router.get("/pdf-status/{job_id}")
async def pdf_status(job_id: str):
    """SSE endpoint for PDF jobs"""
    return EventSourceResponse(stream_events(job_id))


@router.get("/docx-status/{job_id}")
async def docx_status(job_id: str):
    """SSE endpoint for DOCX jobs"""
    return EventSourceResponse(stream_events(job_id))


@router.get("/download-pdf/{file_name:path}")
async def download_pdf(file_name: str):
    """Serve the generated PDF file once ready"""
    clean_name = file_name.replace("\\", "/").lstrip("/")
    clean_name = clean_name.removeprefix("download-pdf/").removeprefix("pdfs/")
    file_path = Path("pdfs") / clean_name

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(file_path, filename="report.pdf", media_type="application/pdf")


@router.get("/download-docx/{file_name:path}")
async def download_docx(file_name: str):
    """Serve the generated DOCX file once ready"""
    clean_name = file_name.replace("\\", "/").lstrip("/")
    clean_name = clean_name.removeprefix("download-docx/").removeprefix("docx/")
    file_path = Path("docx") / clean_name

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="DOCX file not found")

    return FileResponse(
        file_path,
        filename="report.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
