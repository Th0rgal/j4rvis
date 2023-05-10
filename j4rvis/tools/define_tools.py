import getpass
from typing import Any
from langchain.agents import Tool
from langchain.utilities import (
    WikipediaAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    PythonREPL,
)
from .parsers import remove_code_block
from .email_tools import send_email_builder
from .calendar_tools import calendar_tool
from .misc_tools import shell_tool_runner, _get_platform


def define_tools(config: dict[str, Any]):
    return [
        Tool(
            name="Email Sender",
            func=send_email_builder(
                config["email"]["username"],
                config["email"]["password"],
                config["email"]["server_url"],
                config["email"]["port"],
            ),
            description=(
                "A way to send emails from your own account, j4rvis.assistant@gmail.com."
                "Input should be a json object with string fields 'to_email', 'subject' and 'body'."
                "The body contains your message it must be well-formulated and classy."
                "You must specify in it that you are Mr. Thomas Marchand's assistant. "
                "The output will be a confirmation the email was sent or an error."
            ),
        ),
        Tool(
            name="Calendar",
            func=lambda txt: calendar_tool(config, txt),
            description=(
                "A Calendar Tool to create events and retrieve events within a specific date range on your employer calendar. "
                "The input should be a JSON object with 'action' key and optional 'data' key. "
                'To create an event: \'{"action": "create_event", "data": {"summary": "My Event", "dtstart": "2023-06-01T12:00:00", "dtend": "2023-06-01T13:00:00"}}\'. '
                'To get events: \'{"action": "get_events", "data": {"from_dt": "2023-06-01", "to_dt": "2023-06-30"}}\''
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
            name="Search Summary",
            func=DuckDuckGoSearchAPIWrapper().run,
            description=(
                "A wrapper around a search engine. Useful for when "
                "you need to answer questions about current events. "
                "Input should be optimized for a search engine."
                "It returns concatenated summarized results."
            ),
        ),
        Tool(
            name="Search Meta",
            func=lambda txt: str(DuckDuckGoSearchAPIWrapper().results(txt, 10)),
            description=(
                "A wrapper around a search engine. Useful for when "
                "you need to answer questions about current events. "
                "Input should be optimized for a search engine."
                "It returns the 10 first results as a json array of "
                "objects with the following keys: "
                "snippet - The description of the result."
                "title - The title of the result."
                "link - The link to the result."
            ),
        ),
        Tool(
            name="Python REPL",
            func=lambda txt: PythonREPL().run(remove_code_block(txt)),
            description=(
                "A Python shell. Use this to execute python commands. "
                "Input should be a valid python command. "
                "If you want to see the output of a value, you should print it out "
                "with `print(...)`."
            ),
        ),
        Tool(
            name="Terminal",
            func=shell_tool_runner,
            description=(
                f"Run shell commands on this {_get_platform()} machine and returns the output."
                f"Use this as your own machine, you are connected as '{getpass.getuser()}'."
                "Useful when you need to manage files or when you need to query the internet."
                "Input must be a json object with a list of commands, for example:"
                '{"commands": ["echo \'Hello World!'
                '", "time"]}'
            ),
        ),
    ]
