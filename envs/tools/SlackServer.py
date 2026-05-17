
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema

class Channel(BaseModel):
    """Represents a Slack channel or conversation."""
    id: str = Field(..., description="Unique identifier of the channel")
    name: str = Field(default="", description="Display name of the channel")
    is_channel: bool = Field(default=False, description="True if conversation is a channel")
    is_private: bool = Field(default=False, description="True if conversation is private")
    is_im: bool = Field(default=False, description="True if conversation is a DM")
    num_members: int = Field(default=0, ge=0, description="Number of members")
    topic: str = Field(default="", description="Channel topic")

class Message(BaseModel):
    """Represents a Slack message."""
    type: str = Field(default="message", description="Type of message")
    user: str = Field(default="", description="User ID who sent the message")
    text: str = Field(default="", description="Text content of the message")
    ts: str = Field(..., description="Timestamp of the message")
    thread_ts: Optional[str] = Field(default=None, description="Parent thread timestamp")
    reactions: List[Any] = Field(default=[], description="List of reactions")
    channel_id: str = Field(default="", description="Channel this message belongs to")

class SlackScenario(BaseModel):
    """Main scenario model for Slack server state."""
    channels: Dict[str, Any] = Field(default={}, description="Map of channel_id to channel data")
    messages: Dict[str, Any] = Field(default={}, description="Map of channel_id to list of messages")
    threads: Dict[str, Any] = Field(default={}, description="Map of thread_ts to list of reply messages")
    current_time: str = Field(default="2026-04-17T02:12:12", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Channel, Message, SlackScenario]

# Section 2: Class

class SlackAPI:
    def __init__(self):
        """Initialize Slack API with empty state."""
        self.channels: Dict[str, Any] = {}
        self.messages: Dict[str, Any] = {}
        self.threads: Dict[str, Any] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = SlackScenario(**scenario)
        self.channels = model.channels
        self.messages = model.messages
        self.threads = model.threads
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "channels": self.channels,
            "messages": self.messages,
            "threads": self.threads,
            "current_time": self.current_time,
        }

    def channels_list(self, channel_types: str, sort: Optional[str] = None, limit: int = 100, cursor: Optional[str] = None) -> dict:
        """List Slack conversations filtered by channel types."""
        types = [t.strip() for t in channel_types.split(",")]
        result = []
        for ch in self.channels.values():
            if "public_channel" in types and ch.get("is_channel") and not ch.get("is_private") and not ch.get("is_im"):
                result.append(ch)
            elif "private_channel" in types and ch.get("is_private") and not ch.get("is_im"):
                result.append(ch)
            elif "im" in types and ch.get("is_im"):
                result.append(ch)
            elif "mpim" in types and ch.get("is_mpim"):
                result.append(ch)

        if sort == "popularity":
            result.sort(key=lambda c: c.get("num_members", 0), reverse=True)

        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0

        page = result[start:start + limit]
        next_cursor = str(start + limit) if start + limit < len(result) else ""
        return {"channels": page, "next_cursor": next_cursor}

    def conversations_history(self, channel_id: str, limit: Optional[str] = None, cursor: Optional[str] = None, include_activity_messages: bool = False) -> dict:
        """Fetch messages from a Slack channel."""
        channel_id = channel_id.lstrip("#")
        # resolve name to id
        resolved_id = channel_id
        for cid, ch in self.channels.items():
            if ch.get("name") == channel_id:
                resolved_id = cid
                break

        msgs = list(self.messages.get(resolved_id, []))
        if not include_activity_messages:
            msgs = [m for m in msgs if m.get("subtype") not in ("channel_join", "channel_leave")]

        max_count = 50
        if limit and limit.isdigit():
            max_count = int(limit)

        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0

        page = msgs[start:start + max_count]
        next_cursor = str(start + max_count) if start + max_count < len(msgs) else ""
        return {"messages": page, "next_cursor": next_cursor}

    def conversations_replies(self, channel_id: str, thread_ts: str, limit: Optional[str] = None, cursor: Optional[str] = None, include_activity_messages: bool = False) -> dict:
        """Fetch replies in a Slack message thread."""
        replies = list(self.threads.get(thread_ts, []))
        if not include_activity_messages:
            replies = [m for m in replies if m.get("subtype") not in ("channel_join", "channel_leave")]

        max_count = 50
        if limit and limit.isdigit():
            max_count = int(limit)

        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0

        page = replies[start:start + max_count]
        next_cursor = str(start + max_count) if start + max_count < len(replies) else ""
        return {"messages": page, "next_cursor": next_cursor, "thread_ts": thread_ts}

    def conversations_search_messages(self, search_query: Optional[str] = None, filter_in_channel: Optional[str] = None,
                                       filter_users_from: Optional[str] = None, filter_date_after: Optional[str] = None,
                                       filter_date_before: Optional[str] = None, filter_threads_only: bool = False,
                                       limit: int = 20, cursor: Optional[str] = None) -> dict:
        """Search Slack messages across channels and threads."""
        all_msgs = []
        for cid, msgs in self.messages.items():
            for m in msgs:
                m_copy = dict(m)
                m_copy["channel_id"] = cid
                all_msgs.append(m_copy)
        for thread_ts, replies in self.threads.items():
            for m in replies:
                m_copy = dict(m)
                if "channel_id" not in m_copy:
                    m_copy["thread_ts"] = thread_ts
                all_msgs.append(m_copy)

        results = []
        for m in all_msgs:
            if search_query and search_query.lower() not in m.get("text", "").lower():
                continue
            if filter_in_channel:
                ch = filter_in_channel.lstrip("#")
                if m.get("channel_id") != ch:
                    # try name match
                    ch_data = self.channels.get(m.get("channel_id", ""), {})
                    if ch_data.get("name") != ch:
                        continue
            if filter_users_from and m.get("user") != filter_users_from:
                continue
            if filter_date_after and m.get("ts", "") < filter_date_after:
                continue
            if filter_date_before and m.get("ts", "") > filter_date_before:
                continue
            if filter_threads_only and not m.get("thread_ts"):
                continue
            results.append(m)

        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0

        page = results[start:start + limit]
        next_cursor = str(start + limit) if start + limit < len(results) else ""
        return {"messages": page, "next_cursor": next_cursor, "total": len(results)}

    def conversations_add_message(self, channel_id: str, payload: str, thread_ts: Optional[str] = None, content_type: Optional[str] = None) -> dict:
        """Add a message to a Slack channel or thread."""
        channel_id = channel_id.lstrip("#")
        resolved_id = channel_id
        for cid, ch in self.channels.items():
            if ch.get("name") == channel_id:
                resolved_id = cid
                break

        ts = self.current_time.replace("T", ".").replace(":", "").replace("-", "") + "000"
        msg = {"type": "message", "user": "bot", "text": payload, "ts": ts}
        if thread_ts:
            msg["thread_ts"] = thread_ts
            if thread_ts not in self.threads:
                self.threads[thread_ts] = []
            self.threads[thread_ts].append(msg)
        else:
            if resolved_id not in self.messages:
                self.messages[resolved_id] = []
            self.messages[resolved_id].append(msg)

        return {"ok": True, "channel": resolved_id, "ts": ts, "message": msg}


# Section 3: MCP Tools

mcp = FastMCP(name="SlackServer")
api = SlackAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Slack API.

    Args:
        scenario (dict): Scenario dictionary matching SlackScenario schema.

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
    Save current Slack state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def channels_list(channel_types: str, sort: Optional[str] = None, limit: int = 100, cursor: Optional[str] = None) -> dict:
    """
    List Slack conversations such as public channels, private channels, DMs, and group DMs.

    Args:
        channel_types (str): Comma-separated channel types such as "public_channel,private_channel,im".
        sort (str): [Optional] Sort mode such as "popularity".
        limit (int): [Optional] Maximum number of channels to return (default 100).
        cursor (str): [Optional] Pagination cursor from a previous response.

    Returns:
        channels (list): List of channel objects.
        next_cursor (str): Cursor for the next page of results.
    """
    try:
        if not channel_types or not isinstance(channel_types, str):
            raise ValueError("channel_types must be a non-empty string")
        return api.channels_list(channel_types, sort, limit, cursor)
    except Exception as e:
        raise e

@mcp.tool()
def conversations_history(channel_id: str, limit: Optional[str] = None, cursor: Optional[str] = None, include_activity_messages: bool = False) -> dict:
    """
    Fetch messages from a Slack channel, DM, or group DM.

    Args:
        channel_id (str): Channel ID or name such as "C1234567890" or "#general".
        limit (str): [Optional] Time window or message count such as "1d", "30d", "90d", or "50".
        cursor (str): [Optional] Pagination cursor from a previous response.
        include_activity_messages (bool): [Optional] Include channel join/leave and other activity messages.

    Returns:
        messages (list): List of message objects.
        next_cursor (str): Cursor for the next page of results.
    """
    try:
        if not channel_id or not isinstance(channel_id, str):
            raise ValueError("channel_id must be a non-empty string")
        return api.conversations_history(channel_id, limit, cursor, include_activity_messages)
    except Exception as e:
        raise e

@mcp.tool()
def conversations_replies(channel_id: str, thread_ts: str, limit: Optional[str] = None, cursor: Optional[str] = None, include_activity_messages: bool = False) -> dict:
    """
    Fetch replies in a Slack message thread.

    Args:
        channel_id (str): Channel ID or name containing the thread.
        thread_ts (str): Timestamp of the parent message or a message in the thread.
        limit (str): [Optional] Time window or message count.
        cursor (str): [Optional] Pagination cursor from a previous response.
        include_activity_messages (bool): [Optional] Include channel activity messages.

    Returns:
        messages (list): List of message objects in the thread.
        next_cursor (str): Cursor for the next page of results.
        thread_ts (str): The timestamp of the parent message in the thread.
    """
    try:
        if not channel_id or not isinstance(channel_id, str):
            raise ValueError("channel_id must be a non-empty string")
        if not thread_ts or not isinstance(thread_ts, str):
            raise ValueError("thread_ts must be a non-empty string")
        if thread_ts not in api.threads:
            raise ValueError(f"Thread {thread_ts} not found")
        return api.conversations_replies(channel_id, thread_ts, limit, cursor, include_activity_messages)
    except Exception as e:
        raise e

@mcp.tool()
def conversations_search_messages(search_query: Optional[str] = None, filter_in_channel: Optional[str] = None,
                                   filter_users_from: Optional[str] = None, filter_date_after: Optional[str] = None,
                                   filter_date_before: Optional[str] = None, filter_threads_only: bool = False,
                                   limit: int = 20, cursor: Optional[str] = None) -> dict:
    """
    Search Slack messages across channels, DMs, and threads.

    Args:
        search_query (str): [Optional] Text query or Slack message URL.
        filter_in_channel (str): [Optional] Channel ID or name to restrict the search.
        filter_users_from (str): [Optional] User ID or display name of message sender.
        filter_date_after (str): [Optional] Earliest message date in YYYY-MM-DD format.
        filter_date_before (str): [Optional] Latest message date in YYYY-MM-DD format.
        filter_threads_only (bool): [Optional] Return only messages that are part of threads.
        limit (int): [Optional] Maximum number of matching messages.
        cursor (str): [Optional] Pagination cursor from a previous response.

    Returns:
        messages (list): List of matching message objects.
        next_cursor (str): Cursor for the next page of results.
        total (int): Total number of matching messages.
    """
    try:
        return api.conversations_search_messages(search_query, filter_in_channel, filter_users_from,
                                                  filter_date_after, filter_date_before, filter_threads_only,
                                                  limit, cursor)
    except Exception as e:
        raise e

@mcp.tool()
def conversations_add_message(channel_id: str, payload: str, thread_ts: Optional[str] = None, content_type: Optional[str] = None) -> dict:
    """
    Add a message to a Slack channel, DM, or thread.

    Args:
        channel_id (str): Channel ID or name where the message should be posted.
        payload (str): Message content.
        thread_ts (str): [Optional] Thread timestamp for a reply.
        content_type (str): [Optional] Payload content type such as "text/markdown" or "text/plain".

    Returns:
        ok (bool): True if the message was posted successfully.
        channel (str): The unique identifier of the channel where the message was posted.
        ts (str): The timestamp of the posted message.
        message (dict): The full message object that was posted.
    """
    try:
        if not channel_id or not isinstance(channel_id, str):
            raise ValueError("channel_id must be a non-empty string")
        if not payload or not isinstance(payload, str):
            raise ValueError("payload must be a non-empty string")
        return api.conversations_add_message(channel_id, payload, thread_ts, content_type)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
