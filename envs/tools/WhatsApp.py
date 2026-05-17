from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
import uuid
import re

# Section 1: Schema
class Message(BaseModel):
    """Represents a WhatsApp message."""
    message_id: str = Field(..., description="Unique message identifier")
    phone: str = Field(..., description="Recipient phone number or group ID")
    from_me: bool = Field(default=False, description="Whether message was sent by logged-in account")
    content: str = Field(default="", description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    type: str = Field(default="text", description="Message type (text, image, file, etc.)")

class Chat(BaseModel):
    """Represents a WhatsApp chat."""
    phone: str = Field(..., description="Phone number or group ID")
    name: str = Field(..., description="Display name of chat/contact")
    unread_count: int = Field(default=0, ge=0, description="Number of unread messages")
    last_message: str = Field(default="", description="Content of most recent message")
    last_message_time: str = Field(default="", description="Timestamp of most recent message")
    archived: bool = Field(default=False, description="Whether chat is archived")

class Contact(BaseModel):
    """Represents a WhatsApp contact."""
    phone: str = Field(..., description="Phone number")
    name: str = Field(..., description="Display name")
    is_registered: bool = Field(default=False, description="Whether contact is registered on WhatsApp")

class Group(BaseModel):
    """Represents a WhatsApp group."""
    group_id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group name")
    participants: List[str] = Field(default=[], description="List of participant phone numbers")
    created_at: str = Field(..., description="Group creation timestamp")
    description: str = Field(default="", description="Group description")

class WhatsAppScenario(BaseModel):
    """Main scenario model for WhatsApp messaging server."""
    messages: Dict[str, Message] = Field(default={}, description="All messages by message ID")
    chats: Dict[str, Chat] = Field(default={}, description="All chats by phone number")
    contacts: Dict[str, Contact] = Field(default={}, description="All contacts by phone number")
    groups: Dict[str, Group] = Field(default={}, description="All groups by group ID")
    profile: Dict[str, Any] = Field(default={
        "push_name": "WhatsApp User",
        "status": "Hey there! I am using WhatsApp.",
        "profile_picture_url": ""
    }, description="Profile information")
    phone_validity_map: Dict[str, bool] = Field(default={
        "+1234567890": True, "+1987654321": True, "+1555123456": True,
        "+1408555123": True, "+1312555987": True, "+1212555678": True,
        "+1415555234": True, "+1617555123": True, "+1631555987": True,
        "+1646555123": True, "+1206555123": True, "+1303555123": True,
        "+1503555123": True, "+1703555123": True, "+1803555123": True,
        "+1903555123": True, "+1415555123": True, "+1510555123": True,
        "+1610555123": True, "+1710555123": True
    }, description="Phone number validity mapping")
    whatsapp_registered_map: Dict[str, bool] = Field(default={
        "+1234567890": True, "+1987654321": True, "+1555123456": True,
        "+1408555123": True, "+1312555987": True, "+1212555678": True,
        "+1415555234": True, "+1617555123": True, "+1631555987": True,
        "+1646555123": True, "+1206555123": True, "+1303555123": True,
        "+1503555123": True, "+1703555123": True, "+1803555123": True,
        "+1903555123": True, "+1415555123": False, "+1510555123": False,
        "+1610555123": False, "+1710555123": False
    }, description="WhatsApp registration status mapping")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Message, Chat, Contact, Group, WhatsAppScenario]

# Section 2: Class
class WhatsAppAPI:
    def __init__(self):
        """Initialize WhatsApp API with empty state."""
        self.messages: Dict[str, Message] = {}
        self.chats: Dict[str, Chat] = {}
        self.contacts: Dict[str, Contact] = {}
        self.groups: Dict[str, Group] = {}
        self.profile: Dict[str, Any] = {}
        self.phone_validity_map: Dict[str, bool] = {}
        self.whatsapp_registered_map: Dict[str, bool] = {}
        self.current_time: str = ""
        
    def validate_phone_format(self, phone: str) -> bool:
        """Validate phone number format."""
        return bool(re.match(r'^\+\d{10,15}$', phone))
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        try:
            model = WhatsAppScenario(**scenario)
            self.messages = model.messages
            self.chats = model.chats
            self.contacts = model.contacts
            self.groups = model.groups
            self.profile = model.profile
            self.phone_validity_map = model.phone_validity_map
            self.whatsapp_registered_map = model.whatsapp_registered_map
            self.current_time = model.current_time
        except Exception as e:
            raise ValueError(f"Invalid scenario data: {str(e)}")

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "messages": {msg_id: msg.model_dump() for msg_id, msg in self.messages.items()},
            "chats": {phone: chat.model_dump() for phone, chat in self.chats.items()},
            "contacts": {phone: contact.model_dump() for phone, contact in self.contacts.items()},
            "groups": {group_id: group.model_dump() for group_id, group in self.groups.items()},
            "profile": self.profile,
            "phone_validity_map": self.phone_validity_map,
            "whatsapp_registered_map": self.whatsapp_registered_map,
            "current_time": self.current_time
        }

    def whatsapp_send_text_message(self, phone: str, message: str) -> dict:
        """Send a text message to a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=message,
            timestamp=timestamp,
            type="text"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = message
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=message,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "timestamp": timestamp
        }

    def whatsapp_send_image(self, phone: str, image_path: str, caption: Optional[str] = "") -> dict:
        """Send an image to a WhatsApp chat or group with optional caption."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        content = f"Image: {image_path}"
        if caption:
            content += f" - {caption}"
            
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=content,
            timestamp=timestamp,
            type="image"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = content
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=content,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "timestamp": timestamp
        }

    def whatsapp_send_file(self, phone: str, file_path: str, caption: Optional[str] = "") -> dict:
        """Send a file to a WhatsApp chat or group with optional caption."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        content = f"File: {file_path}"
        if caption:
            content += f" - {caption}"
            
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=content,
            timestamp=timestamp,
            type="file"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = content
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=content,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "file_path": file_path,
            "timestamp": timestamp
        }

    def whatsapp_send_link(self, phone: str, url: str, preview_text: Optional[str] = "") -> dict:
        """Send a link with optional preview to a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        content = f"Link: {url}"
        if preview_text:
            content += f" - {preview_text}"
            
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=content,
            timestamp=timestamp,
            type="link"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = content
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=content,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "url": url,
            "timestamp": timestamp
        }

    def whatsapp_send_location(self, phone: str, latitude: float, longitude: float, name: Optional[str] = "") -> dict:
        """Send a geographic location to a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        content = f"Location: {latitude}, {longitude}"
        if name:
            content += f" - {name}"
            
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=content,
            timestamp=timestamp,
            type="location"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = content
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=content,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp
        }

    def whatsapp_send_contact(self, phone: str, contact_phone: str, contact_name: str) -> dict:
        """Send a contact card to a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
        if not self.validate_phone_format(contact_phone):
            raise ValueError("Invalid contact phone number format")
            
        message_id = str(uuid.uuid4())
        timestamp = self.current_time
        
        content = f"Contact: {contact_name} ({contact_phone})"
            
        msg = Message(
            message_id=message_id,
            phone=phone,
            from_me=True,
            content=content,
            timestamp=timestamp,
            type="contact"
        )
        self.messages[message_id] = msg
        
        if phone in self.chats:
            self.chats[phone].last_message = content
            self.chats[phone].last_message_time = timestamp
        else:
            self.chats[phone] = Chat(
                phone=phone,
                name=phone,
                last_message=content,
                last_message_time=timestamp
            )
        
        return {
            "message_id": message_id,
            "phone": phone,
            "contact_phone": contact_phone,
            "timestamp": timestamp
        }

    def whatsapp_check_phone(self, phone: str) -> dict:
        """Check if a phone number is registered on WhatsApp."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        is_valid = self.phone_validity_map.get(phone, False)
        is_registered = self.whatsapp_registered_map.get(phone, False) if is_valid else False
        
        return {
            "phone": phone,
            "is_registered": is_registered,
            "is_valid": is_valid
        }

    def whatsapp_list_chats(self, limit: Optional[int] = None, archived: bool = False) -> dict:
        """List all WhatsApp chats for the logged-in account."""
        filtered_chats = [
            chat for chat in self.chats.values()
            if chat.archived == archived
        ]
        
        if limit:
            filtered_chats = filtered_chats[:limit]
        
        return {
            "chats": [
                {
                    "phone": chat.phone,
                    "name": chat.name,
                    "unread_count": chat.unread_count,
                    "last_message": chat.last_message,
                    "last_message_time": chat.last_message_time
                }
                for chat in filtered_chats
            ]
        }

    def whatsapp_get_chat_messages(self, phone: str, limit: Optional[int] = None) -> dict:
        """Get message history from a specific WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        chat_messages = [
            msg for msg in self.messages.values()
            if msg.phone == phone
        ]
        
        if limit:
            chat_messages = chat_messages[:limit]
        
        return {
            "messages": [
                {
                    "message_id": msg.message_id,
                    "phone": msg.phone,
                    "from": "me" if msg.from_me else msg.phone,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "type": msg.type
                }
                for msg in chat_messages
            ]
        }

    def whatsapp_archive_chat(self, phone: str, archive: bool) -> dict:
        """Archive or unarchive a WhatsApp chat."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        if phone not in self.chats:
            self.chats[phone] = Chat(phone=phone, name=phone)
        
        self.chats[phone].archived = archive
        
        return {
            "phone": phone,
            "archived": self.chats[phone].archived
        }

    def whatsapp_create_group(self, name: str, participants: Optional[List[str]] = None) -> dict:
        """Create a new WhatsApp group with optional initial participants."""
        group_id = f"group_{str(uuid.uuid4())}"
        timestamp = self.current_time
        
        if participants is None:
            participants = []
        
        # Validate all participant phone numbers
        for phone in participants:
            if not self.validate_phone_format(phone):
                raise ValueError(f"Invalid participant phone number: {phone}")
        
        group = Group(
            group_id=group_id,
            name=name,
            participants=participants,
            created_at=timestamp
        )
        self.groups[group_id] = group
        
        return {
            "group_id": group_id,
            "name": name,
            "participants": participants
        }

    def whatsapp_get_group_info(self, group_id: str) -> dict:
        """Get detailed information about a WhatsApp group."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        group = self.groups[group_id]
        return {
            "group_id": group.group_id,
            "name": group.name,
            "participants": group.participants,
            "created_at": group.created_at,
            "description": group.description
        }

    def whatsapp_add_group_participants(self, group_id: str, participants: List[str]) -> dict:
        """Add new participants to an existing WhatsApp group."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        # Validate all participant phone numbers
        for phone in participants:
            if not self.validate_phone_format(phone):
                raise ValueError(f"Invalid participant phone number: {phone}")
        
        group = self.groups[group_id]
        added_participants = []
        failed_participants = []
        
        for participant in participants:
            if participant not in group.participants:
                group.participants.append(participant)
                added_participants.append(participant)
            else:
                failed_participants.append(participant)
        
        return {
            "group_id": group_id,
            "added_participants": added_participants,
            "failed_participants": failed_participants
        }

    def whatsapp_remove_group_participants(self, group_id: str, participants: List[str]) -> dict:
        """Remove participants from an existing WhatsApp group."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        group = self.groups[group_id]
        removed_participants = []
        failed_participants = []
        
        for participant in participants:
            if participant in group.participants:
                group.participants.remove(participant)
                removed_participants.append(participant)
            else:
                failed_participants.append(participant)
        
        return {
            "group_id": group_id,
            "removed_participants": removed_participants,
            "failed_participants": failed_participants
        }

    def whatsapp_update_group_name(self, group_id: str, name: str) -> dict:
        """Update the name of an existing WhatsApp group."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        self.groups[group_id].name = name
        
        return {
            "group_id": group_id,
            "name": name
        }

    def whatsapp_update_group_description(self, group_id: str, description: str) -> dict:
        """Update the description of an existing WhatsApp group."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        self.groups[group_id].description = description
        
        return {
            "group_id": group_id,
            "description": description
        }

    def whatsapp_leave_group(self, group_id: str) -> dict:
        """Leave a WhatsApp group that the logged-in account is a member of."""
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} not found")
        
        del self.groups[group_id]
        
        return {
            "group_id": group_id,
            "left": True
        }

    def whatsapp_get_profile_info(self, phone: Optional[str] = None) -> dict:
        """Get profile information for a contact or the logged-in account."""
        if phone is not None:
            if not self.validate_phone_format(phone):
                raise ValueError("Invalid phone number format")
        
        if phone is None:
            return {
                "phone": "me",
                "name": self.profile.get("push_name", "WhatsApp User"),
                "status": self.profile.get("status", "Hey there! I am using WhatsApp."),
                "profile_picture_url": self.profile.get("profile_picture_url", "")
            }
        
        if phone in self.contacts:
            contact = self.contacts[phone]
            return {
                "phone": phone,
                "name": contact.name,
                "status": "Available",
                "profile_picture_url": ""
            }
        
        return {
            "phone": phone,
            "name": phone,
            "status": "",
            "profile_picture_url": ""
        }

    def whatsapp_change_push_name(self, push_name: str) -> dict:
        """Change the display name (push name) of the logged-in WhatsApp account."""
        self.profile["push_name"] = push_name
        
        return {
            "push_name": push_name,
            "updated": True
        }

    def whatsapp_change_avatar(self, avatar_path: str) -> dict:
        """Change the profile avatar/picture of the logged-in WhatsApp account."""
        self.profile["profile_picture_url"] = avatar_path
        
        return {
            "updated": True,
            "avatar_path": avatar_path
        }

    def whatsapp_get_contacts(self, limit: Optional[int] = None) -> dict:
        """Get the list of contacts from the logged-in WhatsApp account."""
        contacts_list = list(self.contacts.values())
        
        if limit:
            contacts_list = contacts_list[:limit]
        
        return {
            "contacts": [
                {
                    "phone": contact.phone,
                    "name": contact.name,
                    "is_registered": contact.is_registered
                }
                for contact in contacts_list
            ]
        }

    def whatsapp_mark_message_read(self, phone: str, message_id: Optional[str] = None) -> dict:
        """Mark messages as read in a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
            
        if phone in self.chats:
            self.chats[phone].unread_count = 0
        
        return {
            "phone": phone,
            "marked_read": True
        }

    def whatsapp_delete_message(self, phone: str, message_id: str) -> dict:
        """Delete a message from a WhatsApp chat or group."""
        if not self.validate_phone_format(phone):
            raise ValueError("Invalid phone number format")
        if not message_id or not isinstance(message_id, str):
            raise ValueError("Message ID must be a non-empty string")
            
        if message_id in self.messages:
            del self.messages[message_id]
            deleted = True
        else:
            deleted = False
        
        return {
            "message_id": message_id,
            "deleted": deleted
        }

# Section 3: MCP Tools
mcp = FastMCP(name="WhatsApp")
api = WhatsAppAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the WhatsApp API.
    
    Args:
        scenario (dict): Scenario dictionary matching WhatsAppScenario schema.
    
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
    Save current WhatsApp state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_text_message(phone: str, message: str) -> dict:
    """
    Send a text message to a WhatsApp chat or group.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        message (str): The text content to send.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        return api.whatsapp_send_text_message(phone, message)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_image(phone: str, image_path: str, caption: Optional[str] = "") -> dict:
    """
    Send an image to a WhatsApp chat or group with optional caption.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        image_path (str): Local file path to the image.
        caption (str): [Optional] Caption text.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not image_path or not isinstance(image_path, str):
            raise ValueError("Image path must be a non-empty string")
        return api.whatsapp_send_image(phone, image_path, caption)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_file(phone: str, file_path: str, caption: Optional[str] = "") -> dict:
    """
    Send a file to a WhatsApp chat or group with optional caption.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        file_path (str): Local file path to the file.
        caption (str): [Optional] Caption text.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        file_path (str): Path of the sent file.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not file_path or not isinstance(file_path, str):
            raise ValueError("File path must be a non-empty string")
        return api.whatsapp_send_file(phone, file_path, caption)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_link(phone: str, url: str, preview_text: Optional[str] = "") -> dict:
    """
    Send a link with optional preview to a WhatsApp chat or group.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        url (str): URL to share.
        preview_text (str): [Optional] Preview description.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        url (str): Shared URL.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        return api.whatsapp_send_link(phone, url, preview_text)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_location(phone: str, latitude: float, longitude: float, name: Optional[str] = "") -> dict:
    """
    Send a geographic location to a WhatsApp chat or group.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        latitude (float): Latitude coordinate.
        longitude (float): Longitude coordinate.
        name (str): [Optional] Location name.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        latitude (float): Shared latitude.
        longitude (float): Shared longitude.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("Latitude and longitude must be numbers")
        return api.whatsapp_send_location(phone, latitude, longitude, name)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_send_contact(phone: str, contact_phone: str, contact_name: str) -> dict:
    """
    Send a contact card to a WhatsApp chat or group.
    
    Args:
        phone (str): The phone number or group ID/JID of the recipient.
        contact_phone (str): Phone number of the contact to share.
        contact_name (str): Name of the contact to share.
    
    Returns:
        message_id (str): Unique identifier for the sent message.
        phone (str): Recipient phone number.
        contact_phone (str): Shared contact phone number.
        timestamp (str): Message timestamp.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not contact_phone or not isinstance(contact_phone, str):
            raise ValueError("Contact phone must be a non-empty string")
        if not contact_name or not isinstance(contact_name, str):
            raise ValueError("Contact name must be a non-empty string")
        return api.whatsapp_send_contact(phone, contact_phone, contact_name)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_check_phone(phone: str) -> dict:
    """
    Check if a phone number is registered on WhatsApp.
    
    Args:
        phone (str): Phone number to check.
    
    Returns:
        phone (str): Checked phone number.
        is_registered (bool): Whether number is registered on WhatsApp.
        is_valid (bool): Whether phone number format is valid.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        return api.whatsapp_check_phone(phone)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_list_chats(limit: Optional[int] = None, archived: bool = False) -> dict:
    """
    List all WhatsApp chats for the logged-in account.
    
    Args:
        limit (int): [Optional] Maximum number of chats to return.
        archived (bool): Whether to include archived chats. Defaults to false.
    
    Returns:
        chats (list): List of chat objects.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return api.whatsapp_list_chats(limit, archived)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_get_chat_messages(phone: str, limit: Optional[int] = None) -> dict:
    """
    Get message history from a specific WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID of the chat.
        limit (int): [Optional] Maximum number of messages to retrieve.
    
    Returns:
        messages (list): List of message objects.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return api.whatsapp_get_chat_messages(phone, limit)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_archive_chat(phone: str, archive: bool) -> dict:
    """
    Archive or unarchive a WhatsApp chat.
    
    Args:
        phone (str): Phone number or group ID of the chat.
        archive (bool): True to archive, false to unarchive.
    
    Returns:
        phone (str): Chat phone number.
        archived (bool): Current archive status.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not isinstance(archive, bool):
            raise ValueError("Archive must be a boolean value")
        return api.whatsapp_archive_chat(phone, archive)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_create_group(name: str, participants: Optional[List[str]] = None) -> dict:
    """
    Create a new WhatsApp group with optional initial participants.
    
    Args:
        name (str): Name for the new group.
        participants (list): [Optional] Phone numbers to add as initial participants.
    
    Returns:
        group_id (str): Unique identifier of the new group.
        name (str): Name of the new group.
        participants (list): List of participant phone numbers.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        return api.whatsapp_create_group(name, participants)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_get_group_info(group_id: str) -> dict:
    """
    Get detailed information about a WhatsApp group.
    
    Args:
        group_id (str): Unique identifier of the group.
    
    Returns:
        group_id (str): Group identifier.
        name (str): Group name.
        participants (list): List of participant phone numbers.
        created_at (str): Group creation timestamp.
        description (str): Group description.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        return api.whatsapp_get_group_info(group_id)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_add_group_participants(group_id: str, participants: List[str]) -> dict:
    """
    Add new participants to an existing WhatsApp group.
    
    Args:
        group_id (str): Unique identifier of the group.
        participants (list): Phone numbers to add to the group.
    
    Returns:
        group_id (str): Group identifier.
        added_participants (list): Successfully added phone numbers.
        failed_participants (list): Failed phone numbers.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        if not isinstance(participants, list) or not all(isinstance(p, str) for p in participants):
            raise ValueError("Participants must be a list of strings")
        return api.whatsapp_add_group_participants(group_id, participants)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_remove_group_participants(group_id: str, participants: List[str]) -> dict:
    """
    Remove participants from an existing WhatsApp group.
    
    Args:
        group_id (str): Unique identifier of the group.
        participants (list): Phone numbers to remove from the group.
    
    Returns:
        group_id (str): Group identifier.
        removed_participants (list): Successfully removed phone numbers.
        failed_participants (list): Failed phone numbers.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        if not isinstance(participants, list) or not all(isinstance(p, str) for p in participants):
            raise ValueError("Participants must be a list of strings")
        return api.whatsapp_remove_group_participants(group_id, participants)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_update_group_name(group_id: str, name: str) -> dict:
    """
    Update the name of an existing WhatsApp group.
    
    Args:
        group_id (str): Unique identifier of the group.
        name (str): New name for the group.
    
    Returns:
        group_id (str): Group identifier.
        name (str): Updated group name.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        return api.whatsapp_update_group_name(group_id, name)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_update_group_description(group_id: str, description: str) -> dict:
    """
    Update the description of an existing WhatsApp group.
    
    Args:
        group_id (str): Unique identifier of the group.
        description (str): New description for the group.
    
    Returns:
        group_id (str): Group identifier.
        description (str): Updated group description.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Description must be a non-empty string")
        return api.whatsapp_update_group_description(group_id, description)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_leave_group(group_id: str) -> dict:
    """
    Leave a WhatsApp group that the logged-in account is a member of.
    
    Args:
        group_id (str): Unique identifier of the group to leave.
    
    Returns:
        group_id (str): Group identifier.
        left (bool): Whether successfully left the group.
    """
    try:
        if not group_id or not isinstance(group_id, str):
            raise ValueError("Group ID must be a non-empty string")
        return api.whatsapp_leave_group(group_id)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_get_profile_info(phone: Optional[str] = None) -> dict:
    """
    Get profile information for a contact or the logged-in account.
    
    Args:
        phone (str): [Optional] Phone number to get profile for. Omit for own profile.
    
    Returns:
        phone (str): Profile phone number.
        name (str): Display name.
        status (str): Status message.
        profile_picture_url (str): Profile picture URL.
    """
    try:
        if phone is not None and not isinstance(phone, str):
            raise ValueError("Phone must be a string or None")
        return api.whatsapp_get_profile_info(phone)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_change_push_name(push_name: str) -> dict:
    """
    Change the display name (push name) of the logged-in WhatsApp account.
    
    Args:
        push_name (str): New display name.
    
    Returns:
        push_name (str): Updated display name.
        updated (bool): Whether successfully updated.
    """
    try:
        if not push_name or not isinstance(push_name, str):
            raise ValueError("Push name must be a non-empty string")
        return api.whatsapp_change_push_name(push_name)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_change_avatar(avatar_path: str) -> dict:
    """
    Change the profile avatar/picture of the logged-in WhatsApp account.
    
    Args:
        avatar_path (str): Local file path to the avatar image.
    
    Returns:
        updated (bool): Whether successfully updated.
        avatar_path (str): Path of the avatar image.
    """
    try:
        if not avatar_path or not isinstance(avatar_path, str):
            raise ValueError("Avatar path must be a non-empty string")
        return api.whatsapp_change_avatar(avatar_path)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_get_contacts(limit: Optional[int] = None) -> dict:
    """
    Get the list of contacts from the logged-in WhatsApp account.
    
    Args:
        limit (int): [Optional] Maximum number of contacts to return.
    
    Returns:
        contacts (list): List of contact objects.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return api.whatsapp_get_contacts(limit)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_mark_message_read(phone: str, message_id: Optional[str] = None) -> dict:
    """
    Mark messages as read in a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID of the chat.
        message_id (str): [Optional] Specific message ID to mark as read.
    
    Returns:
        phone (str): Chat phone number.
        marked_read (bool): Whether messages were marked as read.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        return api.whatsapp_mark_message_read(phone, message_id)
    except Exception as e:
        raise e

@mcp.tool()
def whatsapp_delete_message(phone: str, message_id: str) -> dict:
    """
    Delete a message from a WhatsApp chat or group.
    
    Args:
        phone (str): Phone number or group ID of the chat.
        message_id (str): Unique identifier of the message to delete.
    
    Returns:
        message_id (str): Deleted message identifier.
        deleted (bool): Whether message was successfully deleted.
    """
    try:
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string")
        if not message_id or not isinstance(message_id, str):
            raise ValueError("Message ID must be a non-empty string")
        return api.whatsapp_delete_message(phone, message_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()