from typing import Dict, Any
import json
from langchain.agents import Tool
from langchain.requests import TextRequestsWrapper
from langchain.utilities import (
    WikipediaAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    PythonREPL,
)

requests_wrapper = TextRequestsWrapper()


def _parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)


def _clean_url(url: str) -> str:
    """Strips quotes from the url."""
    return url.strip("\"'")


def post_request_runner(txt):
    data = _parse_input(txt)
    return requests_wrapper.post(_clean_url(data["url"]), data["data"])


def define_tools():
    return [
        Tool(
            name="GET Request",
            func=requests_wrapper.get,
            description="A portal to the internet. Use this when you need to get specific content from a website. Input should be a  url (i.e. https://www.google.com). The output will be the text response of the GET request.",
        ),
        Tool(
            name="POST Request",
            func=post_request_runner,
            description=(
                "A tool for making POST requests. Input should be a JSON string with two keys: "
                "'url' and 'data'. The value of 'url' should be a string, and the value of 'data' "
                "should be a dictionary of key-value pairs you want to POST to the URL."
            ),
        ),
        Tool(
            name="Wikipedia",
            func=WikipediaAPIWrapper().run,
            description=(
                "A wrapper around Wikipedia. "
                "Useful for when you need to answer general questions about "
                "people, places, companies, facts, historical events, or other "
                "subjects. Input should be a search query."
            ),
        ),
        Tool(
            name="Search",
            func=DuckDuckGoSearchAPIWrapper().run,
            description=(
                "A wrapper around a search engine. Useful for when "
                "you need to answer questions about current events."
            ),
        ),
        Tool(
            name="Python REPL",
            func=PythonREPL().run,
            description=(
                "A Python shell. Use this to execute python commands. "
                "Input should be a valid python command. "
                "If you want to see the output of a value, you should print it out "
                "with `print(...)`."
            ),
        ),
    ]
