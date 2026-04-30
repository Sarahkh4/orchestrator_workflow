from .state import State, WorkerState
from langchain.messages import SystemMessage, HumanMessage
from .schema import llm, planner
from langgraph.types import Send


async def orchestrator(state: State):
    """Orchestrator that generates a plan for the report"""

    try:
        report_sections = await planner.ainvoke(
            [
                SystemMessage(content = "Generate a plan for the report"),
                HumanMessage(content = f"Here is the report topic: {state["topic"]}"),
            ]
        )
        return {"sections": report_sections.sections}
    
    except Exception as e:
        raise RuntimeError(f"Failed to generate report plan from LLM: {e}")

async def llm_call(state: WorkerState):
    """Worker writes a section of the report"""
    try:
        section = await llm.ainvoke(
            [
                SystemMessage(content = "Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting"),
                HumanMessage(content = f"Here is the section name {state["section"].name} and description {state["section"].description}")
            ]
        )
        return {"completed_sections": [section.content]}
    
    except Exception as e:
        raise RuntimeError(f"Failed to write section {e}")

def synthesizer(state: State):
        
    try:

        """Synthesize full report from sections"""
        completed_sections = state["completed_sections"]
        if not completed_sections:
            raise ValueError("No completed sections found in state. Cannot synthesize report.")
        
        completed_report_sections = "\n\n---\n\n".join(completed_sections)

        return {"final_report": completed_report_sections}
    
    except Exception as e:
        raise RuntimeError(f"Failed to synthesize report: {e}")

def assign_workers(state: State):

    """Assign a worker to each section in the plan"""

    return [Send("llm_call",{"section":s}) for s in state["sections"]] 








