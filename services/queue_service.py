import redis.asyncio as redis
import json
import uuid
import os


# Redis connection — same pattern as tavily_client and llm objects
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

QUEUE_NAME = "report_jobs"


async def enqueue_job(topic: str) -> str:
    """
    Push a new report job into the Redis queue.
    Returns a unique job ID the user can use to track progress.
    """
    job_id = uuid.uuid4().hex

    job = {
        "job_id": job_id,
        "topic": topic,
        "status": "pending"
    }

    # lpush adds job to the left of the Redis list (queue)
    # push item INTO the list (like adding to a queue)
    await redis_client.lpush(QUEUE_NAME, json.dumps(job))

    return job_id


async def publish_event(job_id: str, data: dict):
    """
    Publish a progress/completion event to a Redis channel.
    SSE endpoint listens to this channel and forwards it to the user.
    """
    await redis_client.publish(job_id, json.dumps(data))