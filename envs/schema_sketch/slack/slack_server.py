# Data Source: https://github.com/korotovsky/slack-mcp-server#readme
# Server: Slack
# Category: Team Communication


def channels_list(channel_types: str, sort: str = None, limit: int = 100,
                  cursor: str = None) -> dict:
    """
    List Slack conversations such as public channels, private channels, DMs, and group DMs.

    Args:
        channel_types (str): Comma-separated channel types such as "public_channel,private_channel,im"
        sort (str): [Optional] Sort mode such as "popularity"
        limit (int): [Optional] Maximum number of channels to return
        cursor (str): [Optional] Pagination cursor from a previous response

    Returns:
        dict: {
            "channels": list[{
                "id": str,
                "name": str,
                "is_channel": bool,
                "is_private": bool,
                "is_im": bool,
                "num_members": int,
                "topic": str
            }],
            "next_cursor": str
        }
    """
    pass


def conversations_history(channel_id: str, limit: str = "90d",
                          cursor: str = None,
                          include_activity_messages: bool = False) -> dict:
    """
    Fetch messages from a Slack channel, DM, or group DM.

    Args:
        channel_id (str): Channel ID or name such as "C1234567890" or "#general"
        limit (str): [Optional] Time window or message count such as "1d", "30d", "90d", or "50"
        cursor (str): [Optional] Pagination cursor from a previous response
        include_activity_messages (bool): [Optional] Include channel join/leave and other activity messages

    Returns:
        dict: {
            "messages": list[{
                "type": str,
                "user": str,
                "text": str,
                "ts": str,
                "thread_ts": str,
                "reactions": list[dict]
            }],
            "next_cursor": str
        }
    """
    pass


def conversations_replies(channel_id: str, thread_ts: str,
                          limit: str = "90d", cursor: str = None,
                          include_activity_messages: bool = False) -> dict:
    """
    Fetch replies in a Slack message thread.

    Args:
        channel_id (str): Channel ID or name containing the thread
        thread_ts (str): Timestamp of the parent message or a message in the thread
        limit (str): [Optional] Time window or message count
        cursor (str): [Optional] Pagination cursor from a previous response
        include_activity_messages (bool): [Optional] Include channel activity messages

    Returns:
        dict: {
            "messages": list[dict],
            "next_cursor": str,
            "thread_ts": str
        }
    """
    pass


def conversations_search_messages(search_query: str = None,
                                  filter_in_channel: str = None,
                                  filter_users_from: str = None,
                                  filter_date_after: str = None,
                                  filter_date_before: str = None,
                                  filter_threads_only: bool = False,
                                  limit: int = 20,
                                  cursor: str = None) -> dict:
    """
    Search Slack messages across channels, DMs, and threads.

    Args:
        search_query (str): [Optional] Text query or Slack message URL
        filter_in_channel (str): [Optional] Channel ID or name to restrict the search
        filter_users_from (str): [Optional] User ID or display name of message sender
        filter_date_after (str): [Optional] Earliest message date in YYYY-MM-DD format
        filter_date_before (str): [Optional] Latest message date in YYYY-MM-DD format
        filter_threads_only (bool): [Optional] Return only messages that are part of threads
        limit (int): [Optional] Maximum number of matching messages
        cursor (str): [Optional] Pagination cursor from a previous response

    Returns:
        dict: {
            "messages": list[dict],
            "next_cursor": str,
            "total": int
        }
    """
    pass


def conversations_add_message(channel_id: str, payload: str,
                              thread_ts: str = None,
                              content_type: str = "text/markdown") -> dict:
    """
    Add a message to a Slack channel, DM, or thread.

    Args:
        channel_id (str): Channel ID or name where the message should be posted
        payload (str): Message content
        thread_ts (str): [Optional] Thread timestamp for a reply
        content_type (str): [Optional] Payload content type such as "text/markdown" or "text/plain"

    Returns:
        dict: {
            "ok": bool,
            "channel": str,
            "ts": str,
            "message": dict
        }
    """
    pass

