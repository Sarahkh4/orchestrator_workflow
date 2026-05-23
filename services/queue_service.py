import json
import os

import redis.asyncio as redis

from services.celery_app import celery_app


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JOB_STATUS_PREFIX = "job_status:"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def enqueue_job(topic: str, job_type: str = "report") -> str:
    """
    Enqueue a report/PDF generation task with Celery.
    Redis is used by Celery as the broker and by the API for live job status.
    """
    task = celery_app.send_task(
        "services.worker_service.generate_report_task",
        args=[topic, job_type],
    )
    await set_job_status(task.id, {
        "job_id": task.id,
        "topic": topic,
        "job_type": job_type,
        "status": "queued",
    })
    return task.id


async def set_job_status(job_id: str, data: dict):
    """Persist latest job state so clients can reconnect safely."""
    await redis_client.set(
        f"{JOB_STATUS_PREFIX}{job_id}",
        json.dumps(data),
        ex=24 * 60 * 60,
    )


async def get_job_status(job_id: str) -> dict | None:
    """Fetch the last known state for a queued Celery job."""
    raw = await redis_client.get(f"{JOB_STATUS_PREFIX}{job_id}")
    return json.loads(raw) if raw else None


async def publish_event(job_id: str, data: dict):
    """Publish progress/completion event to a Redis channel."""
    await set_job_status(job_id, data)
    await redis_client.publish(job_id, json.dumps(data))
