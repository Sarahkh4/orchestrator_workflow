from pydantic import BaseModel

class TopicRequest(BaseModel):
    topic: str


class PdfRequest(TopicRequest):
    report: str | None = None
    report_job_id: str | None = None
    report_path: str | None = None
