# Server: Calendar

def list_calendars() -> list:
    """
    List all available calendars.
    
    Returns:
        list: A list of available calendars, each calendar is a dict containing calendar_id (str), calendar_name (str), description (str), timezone (str), is_primary (bool).
    """
    pass

def list_events(calendar_id: str = None, time_min: str = None, time_max: str = None, max_results: int = None) -> list:
    """
    List events with date filtering.
    
    Args:
        calendar_id (str): [Optional] the unique identifier of the calendar to search within, if not provided, uses default calendar
        time_min (str): [Optional] Start time in ISO format (e.g., "2024-01-01T00:00:00Z"), if not provided, starts from now
        time_max (str): [Optional] End time in ISO format (e.g., "2024-12-31T23:59:59Z"), if not provided, no upper limit
        max_results (int): [Optional] Maximum number of events to return
        
    Returns:
        list: A list of events, each event is a dict containing event_id (str), summary (str), start_time (str), end_time (str), description (str), location (str), calendar_id (str).
    """
    pass

def search_events(query: str, calendar_id: str = None, time_min: str = None, time_max: str = None) -> list:
    """
    Search events by text query.
    
    Args:
        query (str): Text query to search for in event titles, descriptions, or locations
        calendar_id (str): [Optional] the unique identifier of the calendar to search within, if not provided, searches all calendars
        time_min (str): [Optional] Start time in ISO format for search range
        time_max (str): [Optional] End time in ISO format for search range
        
    Returns:
        list: A list of matching events, each event is a dict containing event_id (str), summary (str), start_time (str), end_time (str), description (str), location (str), calendar_id (str).
    """
    pass     

def create_event(summary: str, start_time: str, end_time: str, calendar_id: str = None, description: str = None, location: str = None, attendees: list = None, timezone: str = "UTC") -> dict:
    """
    Create new calendar events.
    
    Args:
        summary (str): Title of the event
        start_time (str): Start time in ISO format (e.g., "2024-01-01T10:00:00Z")
        end_time (str): End time in ISO format (e.g., "2024-01-01T11:00:00Z")
        calendar_id (str): [Optional] The calendar ID from list_calendars, if not provided, uses default calendar
        description (str): [Optional] Description of the event
        location (str): [Optional] Location of the event
        attendees (list): [Optional] List of attendee email addresses (list of str)
        timezone (str): [Optional] Time zone for the event, defaults to "UTC"
        
    Returns:
        dict: A dictionary containing the created event information including event_id (str), summary (str), start_time (str), end_time (str), description (str), location (str), calendar_id (str).
    """
    pass

def update_event(event_id: str, summary: str = None, start_time: str = None, end_time: str = None, description: str = None, location: str = None, attendees: list = None) -> dict:
    """
    Update existing events.
    
    Args:
        event_id (str): Unique identifier of the event within its calendar.
        summary (str): [Optional] New title of the event
        start_time (str): [Optional] New start time in ISO format
        end_time (str): [Optional] New end time in ISO format
        description (str): [Optional] New description of the event
        location (str): [Optional] New location of the event
        attendees (list): [Optional] New list of attendee email addresses (list of str)
        
    Returns:
        dict: A dictionary containing the updated event information including event_id (str), summary (str), start_time (str), end_time (str), description (str), location (str), calendar_id (str).
    """
    pass

def delete_event(event_id: str) -> None:
    """
    Delete events.
    
    Args:
        event_id (str): Unique identifier of the event within its calendar.
        
    Returns:
        None
    """
    pass

