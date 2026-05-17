# Data Source: https://developers.zoom.us/docs/api/
# Server: Zoom
# Category: communication


def create_meeting(topic: str, start_time: str = None, duration: int = 60,
                   type: int = 2, timezone: str = None, password: str = None) -> dict:
    """
    Create a new Zoom meeting for the authenticated user.
    
    Args:
        topic (str): Meeting topic/title
        start_time (str): [Optional] Meeting start time (ISO 8601 format)
        duration (int): [Optional] Meeting duration in minutes (default: 60)
        type (int): [Optional] Meeting type: 1 (instant) | 2 (scheduled) | 
                   3 (recurring no fixed time) | 8 (recurring fixed time)
        timezone (str): [Optional] Timezone (e.g., "America/New_York")
        password (str): [Optional] Meeting password (max 10 chars)
        
    Returns:
        dict: {
            "id": int,              # Meeting ID
            "topic": str,
            "start_time": str,      # ISO 8601 timestamp
            "duration": int,
            "timezone": str,
            "join_url": str,        # URL for participants to join
            "start_url": str,       # URL for host to start
            "password": str,
            "settings": dict        # Meeting settings
        }
    """
    pass


def get_meeting(meeting_id: int) -> dict:
    """
    Retrieve details of a specific meeting.
    
    Args:
        meeting_id (int): Zoom meeting ID
        
    Returns:
        dict: {
            "id": int,
            "topic": str,
            "type": int,
            "start_time": str,
            "duration": int,
            "timezone": str,
            "join_url": str,
            "start_url": str,
            "password": str,
            "status": str,          # waiting | started
            "settings": dict
        }
    """
    pass


def list_meetings(user_id: str = "me", type: str = "scheduled", 
                  page_size: int = 30) -> dict:
    """
    List all meetings for a user.
    
    Args:
        user_id (str): [Optional] User ID or "me" (default: me)
        type (str): [Optional] Filter by type: scheduled | live | upcoming | 
                   previous (default: scheduled)
        page_size (int): [Optional] Number of results per page (default: 30)
        
    Returns:
        dict: {
            "page_count": int,
            "page_number": int,
            "page_size": int,
            "total_records": int,
            "meetings": [{
                "id": int,
                "topic": str,
                "start_time": str,
                "duration": int,
                "timezone": str,
                "join_url": str,
                "type": int
            }]
        }
    """
    pass


def update_meeting(meeting_id: int, topic: str = None, start_time: str = None,
                   duration: int = None, settings: dict = None) -> dict:
    """
    Update an existing meeting's details.
    
    Args:
        meeting_id (int): Zoom meeting ID
        topic (str): [Optional] New meeting topic
        start_time (str): [Optional] New start time (ISO 8601)
        duration (int): [Optional] New duration in minutes
        settings (dict): [Optional] Updated meeting settings
        
    Returns:
        dict: {
            "id": int,
            "topic": str,
            "start_time": str,
            "duration": int,
            "updated_at": str       # ISO 8601 timestamp
        }
    """
    pass


def delete_meeting(meeting_id: int, occurrence_id: str = None,
                   cancel_meeting_reminder: bool = False) -> dict:
    """
    Delete a meeting.
    
    Args:
        meeting_id (int): Zoom meeting ID to delete
        occurrence_id (str): [Optional] Specific occurrence ID for recurring meetings
        cancel_meeting_reminder (bool): [Optional] Send cancellation email (default: False)
        
    Returns:
        dict: {
            "deleted": bool,
            "meeting_id": int,
            "occurrence_id": str
        }
    """
    pass


def list_recordings(user_id: str = "me", start_date: str = None, 
                    end_date: str = None, page_size: int = 30) -> dict:
    """
    List cloud recordings for a user.
    
    Args:
        user_id (str): [Optional] User ID or "me" (default: me)
        start_date (str): [Optional] Start date (YYYY-MM-DD), defaults to 7 days ago
        end_date (str): [Optional] End date (YYYY-MM-DD), defaults to today
        page_size (int): [Optional] Results per page (default: 30)
        
    Returns:
        dict: {
            "from": str,            # Query start date
            "to": str,              # Query end date
            "page_count": int,
            "total_records": int,
            "meetings": [{
                "id": int,
                "topic": str,
                "start_time": str,
                "duration": int,
                "total_size": int,  # Recording size in bytes
                "recording_count": int,
                "recording_files": [{
                    "id": str,
                    "file_type": str,   # MP4 | M4A | TXT | etc.
                    "file_size": int,
                    "play_url": str,
                    "download_url": str,
                    "recording_type": str
                }]
            }]
        }
    """
    pass


def get_recording(meeting_id: int) -> dict:
    """
    Get recording details for a specific meeting.
    
    Args:
        meeting_id (int): Meeting ID
        
    Returns:
        dict: {
            "id": int,
            "topic": str,
            "start_time": str,
            "duration": int,
            "total_size": int,
            "recording_files": [{
                "id": str,
                "file_type": str,
                "file_size": int,
                "play_url": str,
                "download_url": str,
                "recording_type": str,
                "status": str       # completed | processing
            }]
        }
    """
    pass


def delete_recording(meeting_id: int, recording_id: str = None,
                     action: str = "trash") -> dict:
    """
    Delete a meeting recording.
    
    Args:
        meeting_id (int): Meeting ID
        recording_id (str): [Optional] Specific recording file ID (deletes all if not provided)
        action (str): [Optional] delete | trash (default: trash)
        
    Returns:
        dict: {
            "deleted": bool,
            "meeting_id": int,
            "recording_id": str
        }
    """
    pass
