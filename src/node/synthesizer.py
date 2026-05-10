from schema.state import State

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