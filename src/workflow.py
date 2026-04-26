from .nodes import(
    orchestrater,
    llm_call,
    synthesizer,
    assign_workers
)

from langgraph.graph import START,END, STATEGRAPH


builder = StateGraph(State)

builder.add_node("orchestrator",orchestrator)
builder.add_node("llm_call",llm_call)
builder.add_node("synthesizer",synthesizer)
builder.add_node("assign_workers",assign_workers)

builder.add_edge()

