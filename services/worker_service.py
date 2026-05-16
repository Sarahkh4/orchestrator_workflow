import json
import asyncio
import logging
from services.queue_service import redis_client, QUEUE_NAME, publish_event
from workflow import workflow_builder

logger = logging.getLogger(__name__)

orchestrator_worker = workflow_builder()


async def process_jobs():
    """
    Continuously listens to the Redis queue and processes jobs one by one.
    This runs in the background when the app starts.
    """
    logger.info("Worker started, listening for jobs...")

    while True:
        try:
            # brpop blocks and waits until a job appears in the queue
            # It's like standing at a conveyor belt, waiting for the next item

            # brpop  → pop item OUT of the list (b = blocking, waits until something appears)

            job_data = await redis_client.brpop(QUEUE_NAME, timeout=1)

            if not job_data:
                continue  # No job yet, keep waiting

            _, raw = job_data
            job = json.loads(raw)
            job_id = job["job_id"]
            topic = job["topic"]

            logger.info(f"Processing job {job_id} for topic: {topic}")

            # Tell the user their job started
            await publish_event(job_id, {
                "status": "processing",
                "message": "Report generation started"
            })

            # Run the actual workflow
            result = await orchestrator_worker.ainvoke({"topic": topic})
            report = result.get("final_report", "")

            # Tell the user it's done and send the report
            await publish_event(job_id, {
                "status": "completed",
                "report": report
            })

            logger.info(f"Job {job_id} completed")

        except Exception as e:
            logger.error(f"Worker error: {e}")
            await publish_event(job_id, {
                "status": "failed",
                "message": f"Report generation failed: {str(e)}"
            })

            await asyncio.sleep(1)  # Brief pause before retrying after error