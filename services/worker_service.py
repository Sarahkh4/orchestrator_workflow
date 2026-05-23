import asyncio
import json
import logging

import redis

from services.celery_app import REDIS_URL, celery_app
from src.pdf_generator import generate_pdf
from src.workflow import workflow_builder


logger = logging.getLogger(__name__)
orchestrator_worker = workflow_builder()
sync_redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
JOB_STATUS_PREFIX = "job_status:"


def _set_job_status(job_id: str, data: dict):
    sync_redis_client.set(f"{JOB_STATUS_PREFIX}{job_id}", json.dumps(data), ex=24 * 60 * 60)


def _publish_event(job_id: str, data: dict):
    _set_job_status(job_id, data)
    sync_redis_client.publish(job_id, json.dumps(data))


async def _run_generation(topic: str, job_type: str) -> dict:
    result = await orchestrator_worker.ainvoke({"topic": topic})
    report = result.get("final_report", "")

    if job_type == "report":
        return {"status": "completed", "report": report}

    if job_type == "pdf":
        pdf_path = await generate_pdf(report)
        return {
            "status": "completed",
            "pdf_path": pdf_path,
            "download_url": f"/download-pdf/{pdf_path}",
            "message": "PDF ready",
        }

    raise ValueError(f"Unsupported job type: {job_type}")


@celery_app.task(bind=True, name="services.worker_service.generate_report_task")
def generate_report_task(self, topic: str, job_type: str = "report"):
    """Celery task for heavyweight report/PDF generation."""
    job_id = self.request.id

    try:
        logger.info("Processing %s job %s for topic: %s", job_type, job_id, topic)
        _publish_event(job_id, {
            "job_id": job_id,
            "topic": topic,
            "job_type": job_type,
            "status": "processing",
            "message": f"{job_type.upper()} generation started",
        })

        payload = asyncio.run(_run_generation(topic, job_type))
        payload.update({
            "job_id": job_id,
            "topic": topic,
            "job_type": job_type,
        })
        _publish_event(job_id, payload)
        logger.info("Job %s completed", job_id)
        return payload

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        payload = {
            "job_id": job_id,
            "topic": topic,
            "job_type": job_type,
            "status": "failed",
            "message": f"Job failed: {exc}",
        }
        _publish_event(job_id, payload)
        raise
