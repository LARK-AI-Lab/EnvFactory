
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Meeting(BaseModel):
    """Represents a Zoom meeting."""
    meeting_id: int = Field(..., ge=1, description="Meeting ID (must be positive)")
    user_id: str = Field(..., description="Host user ID")
    topic: str = Field(..., description="Meeting topic")
    start_time: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", description="Start time in ISO 8601 format")
    duration: Optional[int] = Field(None, ge=1, description="Duration in minutes")
    timezone: Optional[str] = Field(None, description="Timezone")
    password: Optional[str] = Field(None, description="Meeting password")
    join_url: str = Field(..., description="Join URL")
    start_url: str = Field(..., description="Start URL")

class RecordingFile(BaseModel):
    """Represents a recording file."""
    file_id: str = Field(..., description="File ID")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    play_url: str = Field(..., description="Play URL")
    download_url: str = Field(..., description="Download URL")

class Recording(BaseModel):
    """Represents a meeting recording."""
    recording_id: str = Field(..., description="Recording ID")
    meeting_id: int = Field(..., ge=1, description="Meeting ID")
    topic: str = Field(..., description="Meeting topic")
    start_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", description="Start time")
    duration: int = Field(..., ge=1, description="Duration in minutes")
    files: List[RecordingFile] = Field(default=[], description="Recording files")

class ZoomScenario(BaseModel):
    """Main scenario model for Zoom meeting management."""
    meetings: Dict[int, Meeting] = Field(default={}, description="All meetings")
    recordings: Dict[str, Recording] = Field(default={}, description="All recordings")
    next_meeting_id: int = Field(default=1000, ge=1, description="Next meeting ID counter")

Scenario_Schema = [Meeting, RecordingFile, Recording, ZoomScenario]

# Section 2: Class
class ZoomMeetingAPI:
    def __init__(self):
        """Initialize Zoom meeting API with empty state."""
        self.meetings: Dict[int, Meeting] = {}
        self.recordings: Dict[str, Recording] = {}
        self.next_meeting_id: int = 1000

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ZoomScenario(**scenario)
        self.meetings = model.meetings
        self.recordings = model.recordings
        self.next_meeting_id = model.next_meeting_id

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "meetings": {mid: m.model_dump() for mid, m in self.meetings.items()},
            "recordings": {rid: r.model_dump() for rid, r in self.recordings.items()},
            "next_meeting_id": self.next_meeting_id
        }

    def create_meeting(self, user_id: str, topic: str, start_time: Optional[str], duration: Optional[int], timezone: Optional[str], password: Optional[str]) -> dict:
        """Create a new meeting."""
        meeting_id = self.next_meeting_id
        self.next_meeting_id += 1
        
        meeting = Meeting(
            meeting_id=meeting_id,
            user_id=user_id,
            topic=topic,
            start_time=start_time,
            duration=duration,
            timezone=timezone,
            password=password or f"pass{meeting_id}",
            join_url=f"https://zoom.us/j/{meeting_id}",
            start_url=f"https://zoom.us/s/{meeting_id}"
        )
        self.meetings[meeting_id] = meeting
        
        return {
            "meeting_id": meeting.meeting_id,
            "join_url": meeting.join_url,
            "start_url": meeting.start_url,
            "password": meeting.password
        }

    def get_meeting(self, meeting_id: str) -> dict:
        """Retrieve meeting information."""
        mid = int(meeting_id)
        m = self.meetings[mid]
        return {
            "meeting_id": m.meeting_id,
            "topic": m.topic,
            "start_time": m.start_time,
            "duration": m.duration,
            "join_url": m.join_url
        }

    def list_meetings(self, user_id: str, type: Optional[str], page_size: Optional[int]) -> dict:
        """List meetings for a user."""
        user_meetings = [m for m in self.meetings.values() if m.user_id == user_id]
        
        if page_size:
            user_meetings = user_meetings[:page_size]
        
        return {
            "meetings": [
                {
                    "meeting_id": m.meeting_id,
                    "topic": m.topic,
                    "start_time": m.start_time
                }
                for m in user_meetings
            ]
        }

    def update_meeting(self, meeting_id: str, topic: Optional[str], start_time: Optional[str], duration: Optional[int]) -> dict:
        """Update meeting details."""
        mid = int(meeting_id)
        meeting = self.meetings[mid]
        
        if topic:
            meeting.topic = topic
        if start_time:
            meeting.start_time = start_time
        if duration:
            meeting.duration = duration
        
        return {"success": True}

    def delete_meeting(self, meeting_id: str, occurrence_id: Optional[str], cancel_meeting_reminder: Optional[bool]) -> dict:
        """Delete a meeting."""
        mid = int(meeting_id)
        del self.meetings[mid]
        return {"success": True}

    def list_recordings(self, user_id: str, from_date: Optional[str], to_date: Optional[str], page_size: Optional[int]) -> dict:
        """List recordings for a user."""
        user_recordings = []
        for rec in self.recordings.values():
            if rec.meeting_id in self.meetings and self.meetings[rec.meeting_id].user_id == user_id:
                user_recordings.append(rec)
        
        if page_size:
            user_recordings = user_recordings[:page_size]
        
        return {
            "recordings": [
                {
                    "recording_id": r.recording_id,
                    "meeting_id": r.meeting_id,
                    "topic": r.topic,
                    "start_time": r.start_time,
                    "duration": r.duration
                }
                for r in user_recordings
            ]
        }

    def get_recording(self, meeting_id: str) -> dict:
        """Get recording files for a meeting."""
        mid = int(meeting_id)
        recording = None
        for rec in self.recordings.values():
            if rec.meeting_id == mid:
                recording = rec
                break
        
        if not recording:
            return {"recording_files": []}
        
        return {
            "recording_files": [
                {
                    "file_id": f.file_id,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "play_url": f.play_url,
                    "download_url": f.download_url
                }
                for f in recording.files
            ]
        }

    def delete_recording(self, meeting_id: str, action: Optional[str]) -> dict:
        """Delete recording for a meeting."""
        mid = int(meeting_id)
        to_delete = [rid for rid, rec in self.recordings.items() if rec.meeting_id == mid]
        for rid in to_delete:
            del self.recordings[rid]
        return {"success": True}

# Section 3: MCP Tools
mcp = FastMCP(name="ZoomMeetingServer")
api = ZoomMeetingAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Zoom meeting API.

    Args:
        scenario (dict): Scenario dictionary matching ZoomScenario schema.

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
    Save current Zoom meeting state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def create_meeting(user_id: str, topic: str, start_time: str = None, duration: int = None, timezone: str = None, password: str = None) -> dict:
    """
    Schedule a new Zoom meeting for a user.

    Args:
        user_id (str): The unique identifier of the Zoom user who will host the meeting.
        topic (str): The title or subject of the meeting.
        start_time (str) [Optional]: The scheduled start time of the meeting in ISO 8601 format.
        duration (int) [Optional]: The planned duration of the meeting in minutes.
        timezone (str) [Optional]: The timezone for the meeting start time.
        password (str) [Optional]: Optional passcode required for participants to join the meeting.

    Returns:
        meeting_id (int): The unique identifier assigned to the created meeting.
        join_url (str): The URL that participants use to join the meeting.
        start_url (str): The URL that the host uses to start the meeting.
        password (str): The passcode required for participants to join the meeting.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string")
        return api.create_meeting(user_id, topic, start_time, duration, timezone, password)
    except Exception as e:
        raise e

@mcp.tool()
def get_meeting(meeting_id: str) -> dict:
    """
    Retrieve detailed information about a specific meeting.

    Args:
        meeting_id (str): The unique identifier of the meeting to retrieve.

    Returns:
        meeting_id (int): The unique identifier assigned to the created meeting.
        topic (str): The title or subject of the meeting.
        start_time (str): The scheduled start time of the meeting in ISO 8601 format.
        duration (int): The planned duration of the meeting in minutes.
        join_url (str): The URL that participants use to join the meeting.
    """
    try:
        if not meeting_id or not isinstance(meeting_id, str):
            raise ValueError("meeting_id must be a non-empty string")
        mid = int(meeting_id)
        if mid not in api.meetings:
            raise ValueError(f"Meeting {meeting_id} not found")
        return api.get_meeting(meeting_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_meetings(user_id: str, type: str = None, page_size: int = None) -> dict:
    """
    List all meetings for a specific user with optional filtering.

    Args:
        user_id (str): The unique identifier of the Zoom user who will host the meeting.
        type (str) [Optional]: Filter meetings by status.
        page_size (int) [Optional]: The maximum number of meetings to return per page.

    Returns:
        meetings (list): List of meetings matching the filter criteria.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        return api.list_meetings(user_id, type, page_size)
    except Exception as e:
        raise e

@mcp.tool()
def update_meeting(meeting_id: str, topic: str = None, start_time: str = None, duration: int = None) -> dict:
    """
    Modify the settings or details of an existing meeting.

    Args:
        meeting_id (str): The unique identifier of the meeting to retrieve.
        topic (str) [Optional]: The title or subject of the meeting.
        start_time (str) [Optional]: The scheduled start time of the meeting in ISO 8601 format.
        duration (int) [Optional]: The planned duration of the meeting in minutes.

    Returns:
        success (bool): Indicates whether the meeting was successfully updated.
    """
    try:
        if not meeting_id or not isinstance(meeting_id, str):
            raise ValueError("meeting_id must be a non-empty string")
        mid = int(meeting_id)
        if mid not in api.meetings:
            raise ValueError(f"Meeting {meeting_id} not found")
        return api.update_meeting(meeting_id, topic, start_time, duration)
    except Exception as e:
        raise e

@mcp.tool()
def delete_meeting(meeting_id: str, occurrence_id: str = None, cancel_meeting_reminder: bool = None) -> dict:
    """
    Delete or cancel a scheduled meeting.

    Args:
        meeting_id (str): The unique identifier of the meeting to retrieve.
        occurrence_id (str) [Optional]: For recurring meetings, the specific occurrence instance to delete.
        cancel_meeting_reminder (bool) [Optional]: Whether to send cancellation notifications to registered participants.

    Returns:
        success (bool): Indicates whether the meeting was successfully deleted.
    """
    try:
        if not meeting_id or not isinstance(meeting_id, str):
            raise ValueError("meeting_id must be a non-empty string")
        mid = int(meeting_id)
        if mid not in api.meetings:
            raise ValueError(f"Meeting {meeting_id} not found")
        return api.delete_meeting(meeting_id, occurrence_id, cancel_meeting_reminder)
    except Exception as e:
        raise e

@mcp.tool()
def list_recordings(user_id: str, from_date: str = None, to_date: str = None, page_size: int = None) -> dict:
    """
    Retrieve cloud recordings for a user within a date range.

    Args:
        user_id (str): The unique identifier of the Zoom user who will host the meeting.
        from_date (str) [Optional]: The start date for the recording search range in YYYY-MM-DD format.
        to_date (str) [Optional]: The end date for the recording search range in YYYY-MM-DD format.
        page_size (int) [Optional]: The maximum number of recordings to return per page.

    Returns:
        recordings (list): List of cloud recordings within the specified date range.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        return api.list_recordings(user_id, from_date, to_date, page_size)
    except Exception as e:
        raise e

@mcp.tool()
def get_recording(meeting_id: str) -> dict:
    """
    Retrieve recording files and download URLs for a specific meeting.

    Args:
        meeting_id (str): The unique identifier of the meeting to retrieve.

    Returns:
        recording_files (list): List of recording files available for the meeting.
    """
    try:
        if not meeting_id or not isinstance(meeting_id, str):
            raise ValueError("meeting_id must be a non-empty string")
        return api.get_recording(meeting_id)
    except Exception as e:
        raise e

@mcp.tool()
def delete_recording(meeting_id: str, action: str = None) -> dict:
    """
    Delete or move recording files to trash for a meeting.

    Args:
        meeting_id (str): The unique identifier of the meeting to retrieve.
        action (str) [Optional]: The deletion action to perform: delete or trash.

    Returns:
        success (bool): Indicates whether the recording was successfully deleted or moved to trash.
    """
    try:
        if not meeting_id or not isinstance(meeting_id, str):
            raise ValueError("meeting_id must be a non-empty string")
        return api.delete_recording(meeting_id, action)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
