import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from utils.constant import TAVILY_MAX_RESULTS
load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

tavily_client = TavilySearch(api_key=api_key, max_results=TAVILY_MAX_RESULTS)