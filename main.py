from src.workflow import workflow_builder
from src.pdf_generator import generate_pdf

orchestrator_worker = workflow_builder()
report = orchestrator_worker.invoke({"topic": "Create a report on LLM scaling laws"})
print(report)

