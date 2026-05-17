# Server: WhatsApp

def whatsapp_send_text_message(phone: str, message: str) -> dict:
    """
    Send a text message to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send message to
        message (str): Text content of the message to send
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "timestamp": str
        }
    """
    pass

def whatsapp_send_image(phone: str, image_path: str, caption: str = None) -> dict:
    """
    Send an image to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send image to
        image_path (str): Local file path to the image file (JPG/PNG)
        caption (str): [Optional] Caption text to accompany the image
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "timestamp": str
        }
    """
    pass

def whatsapp_send_file(phone: str, file_path: str, caption: str = None) -> dict:
    """
    Send a file to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send file to
        file_path (str): Local file path to the file to send (PDF, DOC, ZIP, etc.)
        caption (str): [Optional] Caption text to accompany the file
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "file_path": str,
            "timestamp": str
        }
    """
    pass

def whatsapp_send_link(phone: str, url: str, preview_text: str = None) -> dict:
    """
    Send a link with preview to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send link to
        url (str): URL to share
        preview_text (str): [Optional] Text description for the link preview
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "url": str,
            "timestamp": str
        }
    """
    pass

def whatsapp_send_location(phone: str, latitude: float, longitude: float, name: str = None) -> dict:
    """
    Send a location to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send location to
        latitude (float): Latitude coordinate of the location
        longitude (float): Longitude coordinate of the location
        name (str): [Optional] Name or label for the location
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "latitude": float,
            "longitude": float,
            "timestamp": str
        }
    """
    pass

def whatsapp_send_contact(phone: str, contact_phone: str, contact_name: str) -> dict:
    """
    Send a contact card to a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to send contact to
        contact_phone (str): Phone number of the contact to share
        contact_name (str): Display name of the contact to share
        
    Returns:
        dict: {
            "message_id": str,
            "phone": str,
            "contact_phone": str,
            "timestamp": str
        }
    """
    pass

def whatsapp_check_phone(phone: str) -> dict:
    """
    Check if a phone number is registered on WhatsApp.
    
    Args:
        phone (str): Phone number to check
        
    Returns:
        dict: {
            "phone": str,
            "is_registered": bool,
            "is_valid": bool
        }
    """
    pass

def whatsapp_list_chats(limit: int = None, archived: bool = False) -> list:
    """
    List all WhatsApp chats for the logged-in account.
    
    Args:
        limit (int): [Optional] Maximum number of chats to return
        archived (bool): [Optional] Include archived chats, defaults to False
        
    Returns:
        list: Each chat contains {
            "phone": str,
            "name": str,
            "unread_count": int,
            "last_message": str,
            "last_message_time": str
        }
    """
    pass

def whatsapp_get_chat_messages(phone: str, limit: int = None) -> list:
    """
    Get message history from a specific WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to retrieve messages from
        limit (int): [Optional] Maximum number of messages to retrieve
        
    Returns:
        list: Each message contains {
            "message_id": str,
            "phone": str,
            "from": str,
            "content": str,
            "timestamp": str,
            "type": str
        }
    """
    pass

def whatsapp_archive_chat(phone: str, archive: bool) -> dict:
    """
    Archive or unarchive a WhatsApp chat.
    
    Args:
        phone (str): Phone number or group ID to archive or unarchive
        archive (bool): True to archive, false to unarchive
        
    Returns:
        dict: {
            "phone": str,
            "archived": bool
        }
    """
    pass

def whatsapp_create_group(name: str, participants: list = None) -> dict:
    """
    Create a new WhatsApp group.
    
    Args:
        name (str): Name of the new group
        participants (list): [Optional] Array of phone numbers to add to the group
        
    Returns:
        dict: {
            "group_id": str,
            "name": str,
            "participants": list
        }
    """
    pass

def whatsapp_get_group_info(group_id: str) -> dict:
    """
    Get information about a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID to retrieve information for
        
    Returns:
        dict: {
            "group_id": str,
            "name": str,
            "participants": list,
            "created_at": str,
            "description": str
        }
    """
    pass

def whatsapp_add_group_participants(group_id: str, participants: list) -> dict:
    """
    Add participants to a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID
        participants (list): Array of phone numbers to add to the group
        
    Returns:
        dict: {
            "group_id": str,
            "added_participants": list,
            "failed_participants": list
        }
    """
    pass

def whatsapp_remove_group_participants(group_id: str, participants: list) -> dict:
    """
    Remove participants from a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID
        participants (list): Array of phone numbers to remove from the group
        
    Returns:
        dict: {
            "group_id": str,
            "removed_participants": list,
            "failed_participants": list
        }
    """
    pass

def whatsapp_update_group_name(group_id: str, name: str) -> dict:
    """
    Update the name of a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID to update
        name (str): New name for the group
        
    Returns:
        dict: {
            "group_id": str,
            "name": str
        }
    """
    pass

def whatsapp_update_group_description(group_id: str, description: str) -> dict:
    """
    Update the description of a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID to update
        description (str): New description for the group
        
    Returns:
        dict: {
            "group_id": str,
            "description": str
        }
    """
    pass

def whatsapp_leave_group(group_id: str) -> dict:
    """
    Leave a WhatsApp group.
    
    Args:
        group_id (str): Group ID/JID to leave
        
    Returns:
        dict: {
            "group_id": str,
            "left": bool
        }
    """
    pass

def whatsapp_get_profile_info(phone: str = None) -> dict:
    """
    Get profile information for a contact or the logged-in account.
    
    Args:
        phone (str): [Optional] Phone number to get profile for, omit for logged-in account
        
    Returns:
        dict: {
            "phone": str,
            "name": str,
            "status": str,
            "profile_picture_url": str
        }
    """
    pass

def whatsapp_change_push_name(push_name: str) -> dict:
    """
    Change the display name (push name) of the logged-in WhatsApp account.
    
    Args:
        push_name (str): New display name for the account
        
    Returns:
        dict: {
            "push_name": str,
            "updated": bool
        }
    """
    pass

def whatsapp_change_avatar(avatar_path: str) -> dict:
    """
    Change the profile avatar/picture of the logged-in WhatsApp account. Note: File upload in MCP context has limitations.
    
    Args:
        avatar_path (str): Local file path to the new avatar image (JPG/PNG)
        
    Returns:
        dict: {
            "updated": bool,
            "avatar_path": str
        }
    """
    pass

def whatsapp_get_contacts(limit: int = None) -> list:
    """
    Get list of contacts from the logged-in WhatsApp account.
    
    Args:
        limit (int): [Optional] Maximum number of contacts to return
        
    Returns:
        list: Each contact contains {
            "phone": str,
            "name": str,
            "is_registered": bool
        }
    """
    pass

def whatsapp_mark_message_read(phone: str, message_id: str = None) -> dict:
    """
    Mark messages as read in a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID to mark messages as read
        message_id (str): [Optional] Specific message ID to mark as read, omit to mark all as read
        
    Returns:
        dict: {
            "phone": str,
            "marked_read": bool
        }
    """
    pass

def whatsapp_delete_message(phone: str, message_id: str) -> dict:
    """
    Delete a message from a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID/JID containing the message
        message_id (str): Message ID to delete
        
    Returns:
        dict: {
            "message_id": str,
            "deleted": bool
        }
    """
    pass

