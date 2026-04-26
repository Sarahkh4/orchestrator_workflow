from .state import State, WorkerState
from langchain.messages import SystemMessage, HumanMessage

def orchestrator(state: State):
    """Orchestrator that generates a plan for the report"""
    report_setions = planner.invoke(
        [
            SystemMessage(content = "Generate a plan for the report"),
            HumanMessage(content = f"Here is the report topic: {state[topic]}"),
        ]
    )
    return {"sections": report_sections.sections}

def llm_call(state: WorkerState):
    """Worker writes a section of the report"""
    section = llm.invoke(
        [
            SystemMessage(content = "Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting"),
            HumanMessage(content = f"Here is the section name {state['section'].name} and description {state['section'].description}")
        ]
    )
    return {"completed_sections": section.content}

def synthesizer(state: State):
    """Synthesize full report from sections"""
    completed_sections = state["completed_sections"]
    completed_report_sections = "\n\n---\n\n".join(compeleted_sections)

    return {"final_report": completed_report_sections}

def assign_workers(state: State):
    """Assign a worker to each section in the plan"""

    return [Send("llm_call",{"section:s"} for s in state["sections"])] 

    
       





