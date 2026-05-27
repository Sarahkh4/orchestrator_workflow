import asyncio
import json
import logging
from pathlib import Path
import redis
from services.celery_app import REDIS_URL, celery_app
from src.docx_generator import generate_docx
from src.pdf_generator import generate_pdf
from src.workflow import workflow_builder


logger = logging.getLogger(__name__)
orchestrator_worker = workflow_builder()
sync_redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
JOB_STATUS_PREFIX = "job_status:"
REPORTS_DIR = Path("reports")


def _set_job_status(job_id: str, data: dict):
    sync_redis_client.set(f"{JOB_STATUS_PREFIX}{job_id}", json.dumps(data), ex=24 * 60 * 60)


def _publish_event(job_id: str, data: dict):
    _set_job_status(job_id, data)
    sync_redis_client.publish(job_id, json.dumps(data))


def _save_report_markdown(job_id: str, report: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"report_{job_id}.md"
    report_path.write_text(report, encoding="utf-8")
    return str(report_path)


def _load_report_from_existing_job(report_job_id: str | None) -> str | None:
    if not report_job_id:
        return None

    raw_status = sync_redis_client.get(f"{JOB_STATUS_PREFIX}{report_job_id}")
    if raw_status:
        status = json.loads(raw_status)
        if status.get("report"):
            return status["report"]
        report_path = status.get("report_path")
        if report_path and Path(report_path).is_file():
            return Path(report_path).read_text(encoding="utf-8")

    report_path = REPORTS_DIR / f"report_{report_job_id}.md"
    if report_path.is_file():
        return report_path.read_text(encoding="utf-8")

    return None


def _load_report_from_path(report_path: str | None) -> str | None:
    if not report_path:
        return None

    path = Path(report_path)
    if path.is_file():
        return path.read_text(encoding="utf-8")

    return None


async def _run_generation(
    topic: str,
    job_type: str,
    job_id: str,
    existing_report: str | None = None,
    report_job_id: str | None = None,
    report_path: str | None = None,
) -> dict:
    if job_type == "report":
        result = await orchestrator_worker.ainvoke({"topic": topic})
        report = result.get("final_report", "")
        saved_report_path = _save_report_markdown(job_id, report)
        return {
            "status": "completed",
            "report": report,
            "report_path": saved_report_path,
        }

    if job_type in {"pdf", "docx"}:
        report = (
            existing_report
            or _load_report_from_existing_job(report_job_id)
            or _load_report_from_path(report_path)
        )

        if not report:
            raise ValueError(f"{job_type.upper()} generation requires an existing generated report. Generate the report first.")

        if job_type == "docx":
            docx_path = await generate_docx(report)
            return {
                "status": "completed",
                "docx_path": docx_path,
                "download_url": f"/download-docx/{docx_path}",
                "message": "DOCX ready",
            }

        pdf_path = await generate_pdf(report)
        return {
            "status": "completed",
            "pdf_path": pdf_path,
            "download_url": f"/download-pdf/{pdf_path}",
            "message": "PDF ready",
        }

    raise ValueError(f"Unsupported job type: {job_type}")


@celery_app.task(bind=True, name="services.worker_service.generate_report_task")
def generate_report_task(
    self,
    topic: str,
    job_type: str = "report",
    report: str | None = None,
    report_job_id: str | None = None,
    report_path: str | None = None,
):
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

        payload = asyncio.run(_run_generation(topic, job_type, job_id, report, report_job_id, report_path))
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
