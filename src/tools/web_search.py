from langchain_tavily import TavilySearch
from langchain.tools import tool
from services.tavily_search import tavily_client

@tool
def tavily_tool(query:str):
    """
    Creates and returns a configured TavilySearch tool for web searching.

    This tool is used by the section writer agent to search the internet
    for accurate, up-to-date information when writing report sections.

    Args:
        None

    Returns:
        TavilySearch: A configured Tavily search tool instance that can be
        passed to a LangChain agent as part of its tools list.

    """
    return tavily_client 