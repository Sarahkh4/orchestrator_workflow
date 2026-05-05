from src.node.orchestrator import orchestrator
from src.node.llm_call import llm_call
from src.node.assign_workers import assign_workers
from src.node.synthesizer import synthesizer

from langgraph.graph import START,END, StateGraph
from schema.state import State


def workflow_builder():
    builder = StateGraph(State)

    builder.add_node("orchestrator",orchestrator)
    builder.add_node("llm_call",llm_call)
    builder.add_node("synthesizer",synthesizer)
    builder.add_node("assign_workers",assign_workers)

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges(
        "orchestrator",
        assign_workers , ["llm_call"]
        )
    builder.add_edge("llm_call", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()