from typing import Dict, Any
import json
import platform
from langchain.agents import Tool
from langchain.tools import ShellTool
from langchain.requests import TextRequestsWrapper
from langchain.utilities import (
    WikipediaAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    PythonREPL,
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)


def _clean_url(url: str) -> str:
    """Strips quotes from the url."""
    return url.strip("\"'")


requests_wrapper = TextRequestsWrapper()


def post_request_runner(txt):
    data = _parse_input(txt)
    return requests_wrapper.post(_clean_url(data["url"]), data["data"])


def _get_platform() -> str:
    """Get platform."""
    system = platform.system()
    if system == "Darwin":
        return "MacOS"
    return system


shell_tool = ShellTool()


def shell_tool_runner(txt) -> str:
    data = _parse_input(txt)
    return shell_tool.run(data)


def send_email_builder(email, password, server_url, port):
    def send_email(txt) -> str:
        # Email details
        data = _parse_input(txt)
        to_email = data["to_email"]
        subject = data["subject"]
        body = data["body"]

        # Create the MIME object
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send the email
        try:
            with smtplib.SMTP_SSL(server_url, port) as server:
                server.login(email, password)
                text = msg.as_string()
                server.sendmail(email, to_email, text)
                return "Email sent successfully."
        except Exception as e:
            return f"Error occurred while sending the email: {e}"

    return send_email


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
            name="GET Request",
            func=requests_wrapper.get,
            description=(
                "A portal to the internet. Use this when you need to get specific "
                "content from a website. Input should be a  url (i.e. https://www.google.com). "
                "The output will be the text response of the GET request."
            ),
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
        Tool(
            name="Terminal",
            func=shell_tool_runner,
            description=(
                f"Run shell commands on this {_get_platform()} machine and returns the output."
                "Use this for very generic action, it's your own machine."
                "Input must be a json object with a list of commands, for example:"
                '{"commands": ["echo \'Hello World!'
                '", "time"]}'
            ),
        ),
    ]
