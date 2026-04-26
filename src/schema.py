from typing import Annotated, List
from pydantic import BaseModel, Field
import operator
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

api_key= os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL")

llm = init_chat_model(
    model = "gpt-4o-mini",
    model_provider = "openai",
    api_key = api_key,
    base_url = base_url
)

# Schema for structured output to use in planning
class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )
# Augment the LLM with schema for structured output
planner = llm.with_structured_output(Sections)

# for testing purpose only

# result = planner.invoke("Generate a report outline(2 sections) with a section about 'Neural Network' that includes the main features of a CNN architecture")

# print(result.sections)

