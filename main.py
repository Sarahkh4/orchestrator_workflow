from src.workflow import workflow_builder


orchestrator_worker = workflow_builder()
report = orchestrator_worker.invoke({"topic": "Create a report on LLM scaling laws"})
print(report)