from typing import Dict, Any
import re
import getpass
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
import caldav
from datetime import datetime, timedelta
from icalendar import Event
import pytz


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


def remove_code_block(code_txt: str) -> str:
    # Define regex patterns for the different markdown code markers
    patterns = [r"^```(?:py|python)\n(.*?)\n```\s*$"]

    for pattern in patterns:
        # Search for the pattern in the input string
        match = re.search(pattern, code_txt, re.DOTALL)

        if match:
            # Return the matched code without the markdown code markers
            return match.group(1)

    # If no markdown code markers are found, return the original string
    return code_txt


def calendar_tool(config, txt: str) -> str:
    data = _parse_input(txt)
    action = data.get("action")

    # Connect to the CalDAV server
    client = caldav.DAVClient(
        config["calendar"]["server_url"],
        username=config["calendar"]["username"],
        password=config["calendar"]["password"],
    )
    principal = client.principal()
    calendars = principal.calendars()

    if not calendars:
        return "No calendars found."

    if action == "create_event":
        event_data = data["data"]

        # Find the "Jarvis" calendar
        jarvis_calendar = None
        for calendar in calendars:
            if (
                calendar.get_properties([caldav.dav.DisplayName()])[
                    caldav.dav.DisplayName()
                ]
                == "Jarvis"
            ):
                jarvis_calendar = calendar
                break

        if not jarvis_calendar:
            return "Jarvis calendar not found."

        # Create a new event
        event = Event()
        event.add("summary", event_data["summary"])
        event.add("dtstart", datetime.fromisoformat(event_data["dtstart"]))
        dtend = datetime.fromisoformat(event_data["dtend"]) + timedelta(days=1)
        event.add("dtend", dtend)
        event.add("dtstamp", datetime.now(pytz.utc))

        # Add the event to the "Jarvis" calendar
        jarvis_calendar.add_event(event.to_ical())
        return "Event created successfully."

    elif action == "get_events":
        from_dt_str = data["data"]["from_dt"]
        to_dt_str = data["data"]["to_dt"]

        # Convert the date strings to datetime objects
        from_dt = datetime.strptime(from_dt_str, "%Y-%m-%d")
        to_dt = datetime.strptime(to_dt_str, "%Y-%m-%d") + timedelta(days=1)

        event_list = []

        # Iterate through all calendars
        for calendar in calendars:
            events = calendar.date_search(from_dt, to_dt)

            for event in events:
                print(event)
                event_data = event.data
                event_list.append(event_data)

        return event_list

    else:
        return "Invalid action for the Calendar Tool."


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
                "Input must be a json object with a list of commands, for example:"
                '{"commands": ["echo \'Hello World!'
                '", "time"]}'
            ),
        ),
    ]
