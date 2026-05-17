from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Calendar(BaseModel):
    """Represents a calendar."""
    calendar_id: str = Field(..., min_length=1, description="Unique identifier for the calendar")
    calendar_name: str = Field(..., min_length=1, description="Display name of the calendar")
    description: str = Field(default="", description="Descriptive text explaining the purpose or contents of the calendar")
    timezone: str = Field(..., pattern=r"^[A-Za-z/_]+$", description="Default timezone associated with the calendar")
    is_primary: bool = Field(default=False, description="Boolean flag indicating whether this is the user's primary calendar")

class CalendarEvent(BaseModel):
    """Represents a calendar event."""
    event_id: str = Field(..., min_length=1, description="Unique identifier of the event")
    summary: str = Field(..., min_length=1, description="Title or brief description of the event")
    start_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Scheduled start time of the event in ISO 8601 format")
    end_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Scheduled end time of the event in ISO 8601 format")
    description: Optional[str] = Field(default=None, description="Detailed notes or description associated with the event")
    location: Optional[str] = Field(default=None, description="Physical or virtual location where the event occurs")
    calendar_id: str = Field(..., min_length=1, description="Identifier of the calendar containing this event")
    attendees: Optional[List[str]] = Field(default=None, description="List of attendee email addresses")

class CalendarScenario(BaseModel):
    """Main scenario model for calendar management."""
    calendars: Dict[str, Calendar] = Field(default_factory=lambda: {
        "primary": Calendar(
            calendar_id="primary",
            calendar_name="My Calendar",
            description="Primary personal calendar",
            timezone="America/New_York",
            is_primary=True
        ),
        "work": Calendar(
            calendar_id="work",
            calendar_name="Work Calendar",
            description="Work-related events",
            timezone="America/New_York",
            is_primary=False
        )
    }, description="Dictionary of calendars keyed by calendar_id")
    events: Dict[str, CalendarEvent] = Field(default_factory=lambda: {
        "event_1": CalendarEvent(
            event_id="event_1",
            summary="Team Meeting",
            start_time="2023-12-01T10:00:00Z",
            end_time="2023-12-01T11:00:00Z",
            description="Weekly team sync",
            location="Conference Room A",
            calendar_id="primary",
            attendees=["alice@example.com", "bob@example.com"]
        ),
        "event_2": CalendarEvent(
            event_id="event_2",
            summary="Project Review",
            start_time="2023-12-02T14:00:00Z",
            end_time="2023-12-02T15:30:00Z",
            description="Q4 project review",
            location="Virtual",
            calendar_id="work",
            attendees=["charlie@example.com"]
        )
    }, description="Dictionary of events keyed by event_id")
    default_calendar_id: str = Field(default="primary", min_length=1, description="ID of the default calendar")
    event_id_counter: int = Field(default=3, ge=1, description="Counter for generating new event IDs")
    
Scenario_Schema = [Calendar, CalendarEvent, CalendarScenario]

# Section 2: Class
class CalendarAPI:
    def __init__(self):
        """Initialize calendar API with empty state."""
        self.calendars: Dict[str, Calendar] = {}
        self.events: Dict[str, CalendarEvent] = {}
        self.default_calendar_id: str = "primary"
        self.event_id_counter: int = 1
        
    def load_scenario(self, scenario: dict) -> None:
        """
        Load scenario data into the API instance.
        
        Args:
            scenario (dict): Scenario dictionary matching CalendarScenario schema.
        """
        model = CalendarScenario(**scenario)
        self.calendars = model.calendars
        self.events = model.events
        self.default_calendar_id = model.default_calendar_id
        self.event_id_counter = model.event_id_counter

    def save_scenario(self) -> dict:
        """
        Save current state as scenario dictionary.
        
        Returns:
            dict: Dictionary containing all current state variables.
        """
        return {
            "calendars": {k: v.model_dump() for k, v in self.calendars.items()},
            "events": {k: v.model_dump() for k, v in self.events.items()},
            "default_calendar_id": self.default_calendar_id,
            "event_id_counter": self.event_id_counter
        }
        
    def list_calendars(self) -> List[dict]:
        """
        Retrieves a list of all available calendars.
        
        Returns:
            calendars (List[dict]): Array of calendar objects.
        """
        return [calendar.model_dump() for calendar in self.calendars.values()]
    
    def list_events(self, calendar_id: Optional[str] = None, time_min: Optional[str] = None, 
                    time_max: Optional[str] = None, max_results: Optional[int] = None) -> List[dict]:
        """
        Retrieves a list of calendar events for a specified calendar and time range.
        
        Args:
            calendar_id (str): [Optional] The unique identifier of the calendar to query.
            time_min (str): [Optional] The start time boundary for event filtering in ISO 8601 format.
            time_max (str): [Optional] The end time boundary for event filtering in ISO 8601 format.
            max_results (int): [Optional] Maximum number of events to return.
        
        Returns:
            events (List[dict]): Array of event objects.
        """
        if calendar_id is None:
            calendar_id = self.default_calendar_id
        
        filtered_events = [event for event in self.events.values() if event.calendar_id == calendar_id]
        
        if time_min:
            filtered_events = [event for event in filtered_events if event.start_time >= time_min]
        if time_max:
            filtered_events = [event for event in filtered_events if event.end_time <= time_max]
        
        filtered_events.sort(key=lambda e: e.start_time)
        
        if max_results is not None and max_results > 0:
            filtered_events = filtered_events[:max_results]
        
        return [event.model_dump() for event in filtered_events]
    
    def search_events(self, query: str, calendar_id: Optional[str] = None, 
                      time_min: Optional[str] = None, time_max: Optional[str] = None) -> List[dict]:
        """
        Searches calendar events by text query across event titles, descriptions, and locations.
        
        Args:
            query (str): The text search term.
            calendar_id (str): [Optional] The unique identifier of the calendar to search within.
            time_min (str): [Optional] The start time boundary for the search window.
            time_max (str): [Optional] The end time boundary for the search window.
        
        Returns:
            events (List[dict]): Array of matching event objects.
        """
        query_lower = query.lower()
        
        if calendar_id:
            search_pool = [event for event in self.events.values() if event.calendar_id == calendar_id]
        else:
            search_pool = list(self.events.values())
        
        if time_min:
            search_pool = [event for event in search_pool if event.start_time >= time_min]
        if time_max:
            search_pool = [event for event in search_pool if event.end_time <= time_max]
        
        matching_events = []
        for event in search_pool:
            if (query_lower in event.summary.lower() or 
                (event.description and query_lower in event.description.lower()) or
                (event.location and query_lower in event.location.lower())):
                matching_events.append(event)
        
        matching_events.sort(key=lambda e: e.start_time)
        
        return [event.model_dump() for event in matching_events]
    
    def create_event(self, summary: str, start_time: str, end_time: str, 
                     calendar_id: Optional[str] = None, description: Optional[str] = None,
                     location: Optional[str] = None, attendees: Optional[List[str]] = None,
                     timezone: Optional[str] = None) -> dict:
        """
        Creates a new calendar event with specified timing and details.
        
        Args:
            summary (str): The title or brief summary of the event.
            start_time (str): The scheduled start time in ISO 8601 format.
            end_time (str): The scheduled end time in ISO 8601 format.
            calendar_id (str): [Optional] The unique identifier of the calendar.
            description (str): [Optional] Detailed description or notes.
            location (str): [Optional] Physical or virtual location.
            attendees (List[str]): [Optional] List of attendee email addresses.
            timezone (str): [Optional] The timezone applied to the event timing.
        
        Returns:
            event (dict): The created event object.
        """
        if calendar_id is None:
            calendar_id = self.default_calendar_id
        
        if calendar_id not in self.calendars:
            raise ValueError(f"Calendar {calendar_id} not found")
        
        event_id = f"event_{self.event_id_counter}"
        self.event_id_counter += 1
        
        new_event = CalendarEvent(
            event_id=event_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            calendar_id=calendar_id,
            attendees=attendees
        )
        
        self.events[event_id] = new_event
        
        return new_event.model_dump()
    
    def update_event(self, event_id: str, summary: Optional[str] = None, 
                     start_time: Optional[str] = None, end_time: Optional[str] = None,
                     description: Optional[str] = None, location: Optional[str] = None,
                     attendees: Optional[List[str]] = None) -> dict:
        """
        Updates an existing calendar event by its identifier.
        
        Args:
            event_id (str): The unique identifier of the event to update.
            summary (str): [Optional] New title for the event.
            start_time (str): [Optional] New start time in ISO 8601 format.
            end_time (str): [Optional] New end time in ISO 8601 format.
            description (str): [Optional] New description.
            location (str): [Optional] New location.
            attendees (List[str]): [Optional] New list of attendee email addresses.
        
        Returns:
            event (dict): The updated event object.
        """
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        
        if summary is not None:
            event.summary = summary
        if start_time is not None:
            event.start_time = start_time
        if end_time is not None:
            event.end_time = end_time
        if description is not None:
            event.description = description
        if location is not None:
            event.location = location
        if attendees is not None:
            event.attendees = attendees
        
        return event.model_dump()
    
    def delete_event(self, event_id: str) -> dict:
        """
        Deletes a calendar event by its identifier.
        
        Args:
            event_id (str): The unique identifier of the event to delete.
        
        Returns:
            result (dict): Empty dictionary.
        """
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        del self.events[event_id]
        
        return {}

# Section 3: MCP Tools
mcp = FastMCP(name="CalendarAPI")
api = CalendarAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the calendar API.
    
    Args:
        scenario (dict): Scenario dictionary matching CalendarScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current calendar state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_calendars() -> List[dict]:
    """
    Retrieves a list of all available calendars.
    
    Returns:
        calendars (List[dict]): Array of calendar objects.
    """
    try:
        return api.list_calendars()
    except Exception as e:
        raise e

@mcp.tool()
def list_events(calendar_id: Optional[str] = None, time_min: Optional[str] = None,
                time_max: Optional[str] = None, max_results: Optional[int] = None) -> List[dict]:
    """
    Retrieves a list of calendar events for a specified calendar and time range.
    
    Args:
        calendar_id (str): [Optional] The unique identifier of the calendar to query.
        time_min (str): [Optional] The start time boundary for event filtering in ISO 8601 format.
        time_max (str): [Optional] The end time boundary for event filtering in ISO 8601 format.
        max_results (int): [Optional] Maximum number of events to return.
    
    Returns:
        events (List[dict]): Array of event objects.
    """
    try:
        if max_results is not None and (not isinstance(max_results, int) or max_results <= 0):
            raise ValueError("max_results must be a positive integer if provided")
        return api.list_events(calendar_id, time_min, time_max, max_results)
    except Exception as e:
        raise e

@mcp.tool()
def search_events(query: str, calendar_id: Optional[str] = None,
                  time_min: Optional[str] = None, time_max: Optional[str] = None) -> List[dict]:
    """
    Searches calendar events by text query across event titles, descriptions, and locations.
    
    Args:
        query (str): The text search term.
        calendar_id (str): [Optional] The unique identifier of the calendar to search within.
        time_min (str): [Optional] The start time boundary for the search window.
        time_max (str): [Optional] The end time boundary for the search window.
    
    Returns:
        events (List[dict]): Array of matching event objects.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_events(query, calendar_id, time_min, time_max)
    except Exception as e:
        raise e

@mcp.tool()
def create_event(summary: str, start_time: str, end_time: str,
                 calendar_id: Optional[str] = None, description: Optional[str] = None,
                 location: Optional[str] = None, attendees: Optional[List[str]] = None,
                 timezone: Optional[str] = None) -> dict:
    """
    Creates a new calendar event with specified timing and details.
    
    Args:
        summary (str): The title or brief summary of the event.
        start_time (str): The scheduled start time in ISO 8601 format.
        end_time (str): The scheduled end time in ISO 8601 format.
        calendar_id (str): [Optional] The unique identifier of the calendar.
        description (str): [Optional] Detailed description or notes.
        location (str): [Optional] Physical or virtual location.
        attendees (List[str]): [Optional] List of attendee email addresses.
        timezone (str): [Optional] The timezone applied to the event timing.
    
    Returns:
        event (dict): The created event object.
    """
    try:
        if not summary or not isinstance(summary, str):
            raise ValueError("Summary must be a non-empty string")
        if not start_time or not isinstance(start_time, str):
            raise ValueError("Start time must be a non-empty string")
        if not end_time or not isinstance(end_time, str):
            raise ValueError("End time must be a non-empty string")
        if attendees is not None and not isinstance(attendees, list):
            raise ValueError("Attendees must be a list if provided")
        return api.create_event(summary, start_time, end_time, calendar_id, description, location, attendees, timezone)
    except Exception as e:
        raise e

@mcp.tool()
def update_event(event_id: str, summary: Optional[str] = None,
                 start_time: Optional[str] = None, end_time: Optional[str] = None,
                 description: Optional[str] = None, location: Optional[str] = None,
                 attendees: Optional[List[str]] = None) -> dict:
    """
    Updates an existing calendar event by its identifier.
    
    Args:
        event_id (str): The unique identifier of the event to update.
        summary (str): [Optional] New title for the event.
        start_time (str): [Optional] New start time in ISO 8601 format.
        end_time (str): [Optional] New end time in ISO 8601 format.
        description (str): [Optional] New description.
        location (str): [Optional] New location.
        attendees (List[str]): [Optional] New list of attendee email addresses.
    
    Returns:
        event (dict): The updated event object.
    """
    try:
        if not event_id or not isinstance(event_id, str):
            raise ValueError("Event ID must be a non-empty string")
        return api.update_event(event_id, summary, start_time, end_time, description, location, attendees)
    except Exception as e:
        raise e

@mcp.tool()
def delete_event(event_id: str) -> dict:
    """
    Deletes a calendar event by its identifier.
    
    Args:
        event_id (str): The unique identifier of the event to delete.
    
    Returns:
        result (dict): Empty dictionary.
    """
    try:
        if not event_id or not isinstance(event_id, str):
            raise ValueError("Event ID must be a non-empty string")
        return api.delete_event(event_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()