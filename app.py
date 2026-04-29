from fastapi import FastAPI
from fastapi.responses import FileResponse
from src.workflow import workflow_builder
from pydantic import BaseModel
from src.pdf_generator import generate_pdf

class TopicRequest(BaseModel):
    topic: str
    

app = FastAPI()
orchestrator_worker = workflow_builder()


@app.post("/generate")
def generate(req: TopicRequest):
    result = orchestrator_worker.invoke({"topic": req.topic})

    # adjust key based on your state
    report = result.get("final_report", "No report generated")
    return{
        "topic":req.topic,
        "report": report
    }

@app.post("/download")
def download(req: TopicRequest):
    result = orchestrator_worker.invoke({"topic": req.topic})
    report = result.get("final_report", "")
    pdf_report = generate_pdf(report)
    return FileResponse(pdf_report, filename="report.pdf", media_type="application/pdf")

    