from schema.state import State
from langchain.messages import SystemMessage, HumanMessage
from utils.llm_planner import planner
from utils.prompts.orchestrator_prompt import ORCHESTRATOR_PROMPT

async def orchestrator(state: State):
    """Orchestrator that generates a plan for the report"""
    
        
    try:
        report_sections = await planner.ainvoke(
            [
                SystemMessage(content = ORCHESTRATOR_PROMPT),
                HumanMessage(content = f"Here is the report topic: {state['topic']}"),
            ]
        )
        return {"sections": report_sections.sections}
    
    except Exception as e:
        raise RuntimeError(f"Failed to generate report plan from LLM: {e}")