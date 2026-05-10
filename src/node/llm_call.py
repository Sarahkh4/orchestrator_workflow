from schema.state import WorkerState
from langchain.messages import SystemMessage, HumanMessage
from utils.llm_planner import llm
from langchain.agents import create_agent
from src.tools.web_search import tavily_tool


agent = create_agent(
    model = llm,
    tools = [tavily_tool],
)

async def llm_call(state: WorkerState):
    """Worker writes a section of the report"""
    try:
        section = await agent.ainvoke(
           { "messages":
            [
                SystemMessage(content = "Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting"),
                HumanMessage(content = f"Here is the section name {state['section'].name} and description {state['section'].description}")
            ]
        })
        final_message = section["messages"][-1].content
        return {"completed_sections": [final_message]}
    
    except Exception as e:
        raise RuntimeError(f"Failed to write section {e}")