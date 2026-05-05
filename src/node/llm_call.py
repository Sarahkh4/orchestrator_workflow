from schema.state import WorkerState
from langchain.messages import SystemMessage, HumanMessage
from utils.llm_planner import llm


async def llm_call(state: WorkerState):
    """Worker writes a section of the report"""
    try:
        section = await llm.ainvoke(
            [
                SystemMessage(content = "Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting"),
                HumanMessage(content = f"Here is the section name {state['section'].name} and description {state['section'].description}")
            ]
        )
        return {"completed_sections": [section.content]}
    
    except Exception as e:
        raise RuntimeError(f"Failed to write section {e}")