from .parsers import parse_input, clean_url
from langchain.requests import TextRequestsWrapper
from langchain.tools import ShellTool

requests_wrapper = TextRequestsWrapper()
shell_tool = ShellTool()

def post_request_runner(txt):
    data = parse_input(txt)
    return requests_wrapper.post(clean_url(data["url"]), data["data"])

def shell_tool_runner(txt) -> str:
    data = parse_input(txt)
    return shell_tool.run(data)
