import caldav
from datetime import datetime, timedelta
from icalendar import Event
import pytz
from .parsers import parse_input


def calendar_tool(config, txt: str) -> str:
    data = parse_input(txt)
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
            calendar_name = calendar.name  # Assuming the name property is available
            if calendar_name == "Jarvis":
                jarvis_calendar = calendar
                break

        if not jarvis_calendar:
            return "Jarvis calendar not found."

        # Create a new event
        event = Event()
        event.add("summary", event_data["summary"])
        event.add("dtstart", datetime.fromisoformat(event_data["dtstart"]))
        dtend = datetime.fromisoformat(event_data["dtend"])
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
