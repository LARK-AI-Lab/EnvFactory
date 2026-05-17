from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import uuid

# Section 1: Schema
class Block(BaseModel):
    """Represents a Notion block."""
    block_id: str = Field(..., description="Unique identifier of the block")
    type: str = Field(..., description="Block type")
    content: Dict[str, Any] = Field(default={}, description="Block content")
    created_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    last_edited_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    parent_id: Optional[str] = Field(default=None, description="Parent block/page ID")
    archived: bool = Field(default=False, description="Whether block is archived")

class Page(BaseModel):
    """Represents a Notion page."""
    page_id: str = Field(..., description="Unique identifier of the page")
    title: str = Field(..., description="Page title")
    properties: Dict[str, Any] = Field(default={}, description="Page properties")
    created_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    last_edited_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    parent: Optional[Dict[str, Any]] = Field(default=None, description="Parent descriptor")
    archived: bool = Field(default=False, description="Whether page is archived")

class Database(BaseModel):
    """Represents a Notion database."""
    database_id: str = Field(..., description="Unique identifier of the database")
    title: str = Field(..., description="Database title")
    properties: Dict[str, Any] = Field(default={}, description="Database property schema")
    created_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    last_edited_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    parent: Optional[Dict[str, Any]] = Field(default=None, description="Parent descriptor")
    archived: bool = Field(default=False, description="Whether database is archived")

class User(BaseModel):
    """Represents a Notion user."""
    user_id: str = Field(..., description="Unique identifier of the user")
    name: str = Field(..., description="User name")
    email: Optional[str] = Field(default=None, description="User email")
    type: str = Field(default="person", description="User type")

class Comment(BaseModel):
    """Represents a Notion comment."""
    comment_id: str = Field(..., description="Unique identifier of the comment")
    rich_text: List[Dict[str, Any]] = Field(..., description="Comment content")
    created_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    last_edited_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    parent_id: str = Field(..., description="Parent page/block ID")
    discussion_id: Optional[str] = Field(default=None, description="Discussion thread ID")
    resolved: bool = Field(default=False, description="Whether comment is resolved")
    resolved_time: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="ISO 8601 timestamp")
    resolved_by: Optional[Dict[str, Any]] = Field(default=None, description="User who resolved")

class NotionScenario(BaseModel):
    """Main scenario model for Notion workspace."""
    blocks: Dict[str, Block] = Field(default={}, description="All blocks in workspace")
    pages: Dict[str, Page] = Field(default={}, description="All pages in workspace")
    databases: Dict[str, Database] = Field(default={}, description="All databases in workspace")
    users: Dict[str, User] = Field(default={}, description="All users in workspace")
    comments: Dict[str, Comment] = Field(default={}, description="All comments in workspace")
    blockChildren: Dict[str, List[str]] = Field(default={}, description="Mapping of block ID to child block IDs")
    pageChildren: Dict[str, List[str]] = Field(default={}, description="Mapping of page ID to child block IDs")
    databaseItems: Dict[str, List[str]] = Field(default={}, description="Mapping of database ID to page IDs")
    commentThreads: Dict[str, List[str]] = Field(default={}, description="Mapping of parent ID to comment IDs")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Block, Page, Database, User, Comment, NotionScenario]

# Section 2: Class
class NotionAPI:
    def __init__(self):
        """Initialize Notion API with empty state."""
        self.blocks: Dict[str, Block] = {}
        self.pages: Dict[str, Page] = {}
        self.databases: Dict[str, Database] = {}
        self.users: Dict[str, User] = {}
        self.comments: Dict[str, Comment] = {}
        self.blockChildren: Dict[str, List[str]] = {}
        self.pageChildren: Dict[str, List[str]] = {}
        self.databaseItems: Dict[str, List[str]] = {}
        self.commentThreads: Dict[str, List[str]] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = NotionScenario(**scenario)
        self.blocks = model.blocks
        self.pages = model.pages
        self.databases = model.databases
        self.users = model.users
        self.comments = model.comments
        self.blockChildren = model.blockChildren
        self.pageChildren = model.pageChildren
        self.databaseItems = model.databaseItems
        self.commentThreads = model.commentThreads
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "blocks": {block_id: block.model_dump() for block_id, block in self.blocks.items()},
            "pages": {page_id: page.model_dump() for page_id, page in self.pages.items()},
            "databases": {db_id: db.model_dump() for db_id, db in self.databases.items()},
            "users": {user_id: user.model_dump() for user_id, user in self.users.items()},
            "comments": {comment_id: comment.model_dump() for comment_id, comment in self.comments.items()},
            "blockChildren": self.blockChildren,
            "pageChildren": self.pageChildren,
            "databaseItems": self.databaseItems,
            "commentThreads": self.commentThreads,
            "current_time": self.current_time
        }

    def _generate_timestamp(self) -> str:
        """Generate ISO 8601 timestamp."""
        return self.current_time

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())

    def notion_append_block_children(self, block_id: str, children: List[Dict[str, Any]], format: str = "markdown") -> dict:
        """Append one or more child blocks to an existing parent block."""
        if block_id not in self.blocks:
            raise ValueError(f"Block {block_id} not found")
        
        child_ids = []
        for child_data in children:
            child_id = self._generate_id()
            block = Block(
                block_id=child_id,
                type=child_data.get("type", "paragraph"),
                content=child_data.get("content", {}),
                created_time=self._generate_timestamp(),
                last_edited_time=self._generate_timestamp(),
                parent_id=block_id
            )
            self.blocks[child_id] = block
            child_ids.append(child_id)
        
        if block_id not in self.blockChildren:
            self.blockChildren[block_id] = []
        self.blockChildren[block_id].extend(child_ids)
        
        return {
            "block_id": block_id,
            "children_count": len(self.blockChildren[block_id])
        }

    def notion_retrieve_block_children(self, block_id: str, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
        """Fetch the child blocks contained within a given parent block with optional pagination."""
        if block_id not in self.blocks:
            raise ValueError(f"Block {block_id} not found")
        
        children = self.blockChildren.get(block_id, [])
        results = []
        
        start_idx = 0
        if start_cursor:
            try:
                start_idx = children.index(start_cursor) + 1
            except ValueError:
                start_idx = 0
        
        end_idx = min(start_idx + page_size, len(children))
        page_children = children[start_idx:end_idx]
        
        for child_id in page_children:
            if child_id in self.blocks:
                block = self.blocks[child_id]
                results.append({
                    "block_id": block.block_id,
                    "type": block.type,
                    "content": block.content
                })
        
        next_cursor = None
        if end_idx < len(children):
            next_cursor = children[end_idx - 1] if end_idx > 0 else None
        
        return {
            "results": results,
            "next_cursor": next_cursor
        }

    def notion_create_block(self, parent_id: str, block_type: str, content: Dict[str, Any], format: str = "markdown") -> dict:
        """Create a single new block and attach it to the specified parent page or block."""
        block_id = self._generate_id()
        timestamp = self._generate_timestamp()
        
        block = Block(
            block_id=block_id,
            type=block_type,
            content=content,
            created_time=timestamp,
            last_edited_time=timestamp,
            parent_id=parent_id
        )
        self.blocks[block_id] = block
        
        if parent_id in self.blocks:
            if parent_id not in self.blockChildren:
                self.blockChildren[parent_id] = []
            self.blockChildren[parent_id].append(block_id)
        elif parent_id in self.pages:
            if parent_id not in self.pageChildren:
                self.pageChildren[parent_id] = []
            self.pageChildren[parent_id].append(block_id)
        
        return {
            "block_id": block_id,
            "type": block_type,
            "content": content,
            "created_time": timestamp,
            "last_edited_time": timestamp
        }

    def notion_update_block(self, block_id: str, block_type: Optional[str] = None, content: Optional[Dict[str, Any]] = None, archived: Optional[bool] = None, format: str = "markdown") -> dict:
        """Modify the type, content, or archived status of an existing block."""
        if block_id not in self.blocks:
            raise ValueError(f"Block {block_id} not found")
        
        block = self.blocks[block_id]
        if block_type is not None:
            block.type = block_type
        if content is not None:
            block.content = content
        if archived is not None:
            block.archived = archived
        block.last_edited_time = self._generate_timestamp()
        
        return {
            "block_id": block_id,
            "type": block.type,
            "content": block.content,
            "last_edited_time": block.last_edited_time
        }

    def notion_delete_block(self, block_id: str, format: str = "markdown") -> dict:
        """Delete (archive) a specific block."""
        if block_id not in self.blocks:
            raise ValueError(f"Block {block_id} not found")
        
        self.blocks[block_id].archived = True
        self.blocks[block_id].last_edited_time = self._generate_timestamp()
        
        return {
            "block_id": block_id,
            "deleted": True
        }

    def notion_retrieve_page(self, page_id: str, format: str = "markdown") -> dict:
        """Fetch metadata and properties of a specific page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        page = self.pages[page_id]
        return {
            "page_id": page.page_id,
            "title": page.title,
            "properties": page.properties,
            "created_time": page.created_time,
            "last_edited_time": page.last_edited_time
        }

    def notion_create_page(self, parent: Dict[str, Any], properties: Optional[Dict[str, Any]] = None, children: Optional[List[Dict[str, Any]]] = None, format: str = "markdown") -> dict:
        """Create a new page inside a specified parent page or database."""
        page_id = self._generate_id()
        timestamp = self._generate_timestamp()
        
        page = Page(
            page_id=page_id,
            title="New Page",
            properties=properties or {},
            created_time=timestamp,
            last_edited_time=timestamp,
            parent=parent
        )
        self.pages[page_id] = page
        
        if children:
            for child_data in children:
                child_id = self._generate_id()
                block = Block(
                    block_id=child_id,
                    type=child_data.get("type", "paragraph"),
                    content=child_data.get("content", {}),
                    created_time=timestamp,
                    last_edited_time=timestamp,
                    parent_id=page_id
                )
                self.blocks[child_id] = block
                if page_id not in self.pageChildren:
                    self.pageChildren[page_id] = []
                self.pageChildren[page_id].append(child_id)
        
        return {
            "page_id": page_id,
            "parent": parent,
            "properties": page.properties,
            "created_time": timestamp,
            "last_edited_time": timestamp
        }

    def notion_delete_page(self, page_id: str, format: str = "markdown") -> dict:
        """Delete (archive) a specific page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        self.pages[page_id].archived = True
        self.pages[page_id].last_edited_time = self._generate_timestamp()
        
        return {
            "page_id": page_id,
            "deleted": True,
            "archived": True
        }

    def notion_update_page_properties(self, page_id: str, properties: Dict[str, Any], format: str = "markdown") -> dict:
        """Update property values of an existing page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        page = self.pages[page_id]
        updated_keys = []
        for key, value in properties.items():
            if key in page.properties:
                if page.properties[key] != value:
                    updated_keys.append(key)
            else:
                updated_keys.append(key)
            page.properties[key] = value
        
        page.last_edited_time = self._generate_timestamp()
        
        return {
            "page_id": page_id,
            "updated_properties": updated_keys,
            "last_edited_time": page.last_edited_time
        }

    def notion_update_page_content(self, page_id: str, children: List[Dict[str, Any]], format: str = "markdown") -> dict:
        """Append or replace content blocks within an existing page."""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        timestamp = self._generate_timestamp()
        
        for child_data in children:
            child_id = self._generate_id()
            block = Block(
                block_id=child_id,
                type=child_data.get("type", "paragraph"),
                content=child_data.get("content", {}),
                created_time=timestamp,
                last_edited_time=timestamp,
                parent_id=page_id
            )
            self.blocks[child_id] = block
            if page_id not in self.pageChildren:
                self.pageChildren[page_id] = []
            self.pageChildren[page_id].append(child_id)
        
        self.pages[page_id].last_edited_time = timestamp
        
        return {
            "page_id": page_id,
            "children_count": len(self.pageChildren.get(page_id, [])),
            "last_edited_time": timestamp
        }

    def notion_create_database(self, parent: Dict[str, Any], title: List[Dict[str, Any]], properties: Dict[str, Any], format: str = "markdown") -> dict:
        """Create a new database inside a specified parent page or workspace."""
        database_id = self._generate_id()
        timestamp = self._generate_timestamp()
        
        db = Database(
            database_id=database_id,
            title="New Database",
            properties=properties,
            created_time=timestamp,
            last_edited_time=timestamp,
            parent=parent
        )
        self.databases[database_id] = db
        
        return {
            "database_id": database_id,
            "title": "New Database",
            "properties": properties,
            "created_time": timestamp
        }

    def notion_query_database(self, database_id: str, filter: Optional[Dict[str, Any]] = None, sorts: Optional[List[Dict[str, Any]]] = None, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
        """Query a database and retrieve pages that match optional filter and sort criteria."""
        if database_id not in self.databases:
            raise ValueError(f"Database {database_id} not found")
        
        items = self.databaseItems.get(database_id, [])
        results = []
        
        start_idx = 0
        if start_cursor:
            try:
                start_idx = items.index(start_cursor) + 1
            except ValueError:
                start_idx = 0
        
        end_idx = min(start_idx + page_size, len(items))
        page_items = items[start_idx:end_idx]
        
        for page_id in page_items:
            if page_id in self.pages:
                page = self.pages[page_id]
                results.append({
                    "page_id": page.page_id,
                    "properties": page.properties
                })
        
        next_cursor = None
        if end_idx < len(items):
            next_cursor = items[end_idx - 1] if end_idx > 0 else None
        
        return {
            "results": results,
            "next_cursor": next_cursor,
            "has_more": end_idx < len(items)
        }

    def notion_retrieve_database(self, database_id: str, format: str = "markdown") -> dict:
        """Fetch metadata and property schema of a specific database."""
        if database_id not in self.databases:
            raise ValueError(f"Database {database_id} not found")
        
        db = self.databases[database_id]
        return {
            "database_id": db.database_id,
            "title": db.title,
            "properties": db.properties,
            "created_time": db.created_time,
            "last_edited_time": db.last_edited_time
        }

    def notion_update_database(self, database_id: str, title: Optional[List[Dict[str, Any]]] = None, description: Optional[List[Dict[str, Any]]] = None, properties: Optional[Dict[str, Any]] = None, format: str = "markdown") -> dict:
        """Modify title, description, or property schema of an existing database."""
        if database_id not in self.databases:
            raise ValueError(f"Database {database_id} not found")
        
        db = self.databases[database_id]
        if title is not None:
            db.title = "Updated Database"
        if properties is not None:
            db.properties.update(properties)
        
        db.last_edited_time = self._generate_timestamp()
        
        return {
            "database_id": database_id,
            "last_edited_time": db.last_edited_time
        }

    def notion_delete_database(self, database_id: str, format: str = "markdown") -> dict:
        """Delete (archive) a specific database."""
        if database_id not in self.databases:
            raise ValueError(f"Database {database_id} not found")
        
        self.databases[database_id].archived = True
        self.databases[database_id].last_edited_time = self._generate_timestamp()
        
        return {
            "database_id": database_id,
            "deleted": True,
            "archived": True
        }

    def notion_create_database_item(self, database_id: str, properties: Dict[str, Any], format: str = "markdown") -> dict:
        """Add a new row (page) to a database with the provided properties."""
        if database_id not in self.databases:
            raise ValueError(f"Database {database_id} not found")
        
        page_id = self._generate_id()
        timestamp = self._generate_timestamp()
        
        page = Page(
            page_id=page_id,
            title="Database Item",
            properties=properties,
            created_time=timestamp,
            last_edited_time=timestamp,
            parent={"database_id": database_id}
        )
        self.pages[page_id] = page
        
        if database_id not in self.databaseItems:
            self.databaseItems[database_id] = []
        self.databaseItems[database_id].append(page_id)
        
        return {
            "page_id": page_id,
            "database_id": database_id,
            "properties": properties,
            "created_time": timestamp
        }

    def notion_search(self, query: Optional[str] = None, filter: Optional[Dict[str, Any]] = None, sort: Optional[Dict[str, Any]] = None, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
        """Global search across pages and databases by title with optional filtering and sorting."""
        results = []
        
        # Search pages
        for page_id, page in self.pages.items():
            if not page.archived:
                if query is None or query.lower() in page.title.lower():
                    results.append({
                        "object_id": page_id,
                        "object_type": "page",
                        "title": page.title
                    })
        
        # Search databases
        for db_id, db in self.databases.items():
            if not db.archived:
                if query is None or query.lower() in db.title.lower():
                    results.append({
                        "object_id": db_id,
                        "object_type": "database",
                        "title": db.title
                    })
        
        # Pagination
        start_idx = 0
        if start_cursor:
            try:
                start_idx = int(start_cursor)
            except ValueError:
                start_idx = 0
        
        end_idx = min(start_idx + page_size, len(results))
        page_results = results[start_idx:end_idx]
        
        next_cursor = None
        if end_idx < len(results):
            next_cursor = str(end_idx)
        
        return {
            "results": page_results,
            "next_cursor": next_cursor,
            "has_more": end_idx < len(results)
        }

    def notion_list_all_users(self, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
        """List every user in the workspace with optional pagination."""
        users = list(self.users.values())
        
        start_idx = 0
        if start_cursor:
            try:
                start_idx = int(start_cursor)
            except ValueError:
                start_idx = 0
        
        end_idx = min(start_idx + page_size, len(users))
        page_users = users[start_idx:end_idx]
        
        results = []
        for user in page_users:
            results.append({
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email
            })
        
        next_cursor = None
        if end_idx < len(users):
            next_cursor = str(end_idx)
        
        return {
            "results": results,
            "next_cursor": next_cursor
        }

    def notion_retrieve_user(self, user_id: str, format: str = "markdown") -> dict:
        """Fetch detailed information about a specific user."""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "type": user.type
        }

    def notion_retrieve_bot_user(self, format: str = "markdown") -> dict:
        """Fetch information about the bot user associated with the current integration token."""
        bot_user_id = "bot_user_001"
        if bot_user_id not in self.users:
            self.users[bot_user_id] = User(
                user_id=bot_user_id,
                name="Notion Bot",
                type="bot"
            )
        
        bot = self.users[bot_user_id]
        return {
            "user_id": bot.user_id,
            "name": bot.name,
            "owner": {"type": "integration", "id": "integration_001"}
        }

    def notion_create_comment(self, rich_text: List[Dict[str, Any]], parent: Optional[Dict[str, Any]] = None, discussion_id: Optional[str] = None, format: str = "markdown") -> dict:
        """Add a new comment to a page or an existing discussion thread."""
        comment_id = self._generate_id()
        timestamp = self._generate_timestamp()
        
        parent_id = None
        if parent and "page_id" in parent:
            parent_id = parent["page_id"]
        elif discussion_id:
            # Find parent from existing discussion
            for comment in self.comments.values():
                if comment.discussion_id == discussion_id:
                    parent_id = comment.parent_id
                    break
        
        if not parent_id:
            raise ValueError("Parent page_id or discussion_id required")
        
        comment = Comment(
            comment_id=comment_id,
            rich_text=rich_text,
            created_time=timestamp,
            last_edited_time=timestamp,
            parent_id=parent_id,
            discussion_id=discussion_id or self._generate_id()
        )
        self.comments[comment_id] = comment
        
        if parent_id not in self.commentThreads:
            self.commentThreads[parent_id] = []
        self.commentThreads[parent_id].append(comment_id)
        
        return {
            "comment_id": comment_id,
            "rich_text": rich_text,
            "created_time": timestamp
        }

    def notion_retrieve_comments(self, block_id: str, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
        """Fetch unresolved comments attached to a page or block with optional pagination."""
        comments = []
        for comment in self.comments.values():
            if comment.parent_id == block_id and not comment.resolved:
                comments.append(comment)
        
        start_idx = 0
        if start_cursor:
            try:
                start_idx = int(start_cursor)
            except ValueError:
                start_idx = 0
        
        end_idx = min(start_idx + page_size, len(comments))
        page_comments = comments[start_idx:end_idx]
        
        results = []
        for comment in page_comments:
            results.append({
                "comment_id": comment.comment_id,
                "rich_text": comment.rich_text,
                "created_time": comment.created_time
            })
        
        next_cursor = None
        if end_idx < len(comments):
            next_cursor = str(end_idx)
        
        return {
            "results": results,
            "next_cursor": next_cursor
        }

    def notion_update_comment(self, comment_id: str, rich_text: List[Dict[str, Any]], format: str = "markdown") -> dict:
        """Modify the rich-text content of an existing comment."""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        comment.rich_text = rich_text
        comment.last_edited_time = self._generate_timestamp()
        
        return {
            "comment_id": comment_id,
            "rich_text": rich_text,
            "last_edited_time": comment.last_edited_time
        }

    def notion_delete_comment(self, comment_id: str, format: str = "markdown") -> dict:
        """Delete a specific comment."""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        del self.comments[comment_id]
        
        return {
            "comment_id": comment_id,
            "deleted": True
        }

    def notion_resolve_comment(self, comment_id: str, resolved: bool = True, format: str = "markdown") -> dict:
        """Mark a comment as resolved or unresolved."""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        comment.resolved = resolved
        if resolved:
            comment.resolved_time = self._generate_timestamp()
            comment.resolved_by = {"user_id": "current_user"}
        else:
            comment.resolved_time = None
            comment.resolved_by = None
        
        return {
            "comment_id": comment_id,
            "resolved": resolved,
            "resolved_time": comment.resolved_time,
            "resolved_by": comment.resolved_by
        }

# Section 3: MCP Tools
mcp = FastMCP(name="NotionAPI")
api = NotionAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Notion API.
    
    Args:
        scenario (dict): Scenario dictionary matching NotionScenario schema.
    
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
    """Save current Notion state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def notion_append_block_children(block_id: str, children: List[Dict[str, Any]], format: str = "markdown") -> dict:
    """Append one or more child blocks to an existing parent block.
    
    Args:
        block_id (str): The unique identifier of the parent block that will receive the children.
        children (List[Dict[str, Any]]): Array of block objects to append under the parent.
        format (str): Response format selector applied across all tools.
    
    Returns:
        block_id (str): The unique identifier of the parent block that now contains the new children.
        children_count (int): Total number of child blocks now present under the parent.
    """
    try:
        if not block_id or not isinstance(block_id, str):
            raise ValueError("Block ID must be a non-empty string")
        if not children or not isinstance(children, list):
            raise ValueError("Children must be a non-empty list")
        return api.notion_append_block_children(block_id, children, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_block_children(block_id: str, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
    """Fetch the child blocks contained within a given parent block with optional pagination.
    
    Args:
        block_id (str): The unique identifier of the parent block whose children are requested.
        start_cursor (str): Opaque cursor for retrieving the next page of results.
        page_size (int): Maximum number of child blocks to return in this page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        results (List[Dict[str, Any]]): List of child block objects each containing block_id, type, and content.
        next_cursor (str): Cursor for retrieving the next page of children; null when no more pages exist.
    """
    try:
        if not block_id or not isinstance(block_id, str):
            raise ValueError("Block ID must be a non-empty string")
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValueError("Page size must be an integer between 1 and 100")
        return api.notion_retrieve_block_children(block_id, start_cursor, page_size, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_create_block(parent_id: str, block_type: str, content: Dict[str, Any], format: str = "markdown") -> dict:
    """Create a single new block and attach it to the specified parent page or block.
    
    Args:
        parent_id (str): The unique identifier of the parent page or block that will contain the new block.
        block_type (str): Notion block type such as paragraph, heading_1, bulleted_list_item, etc.
        content (Dict[str, Any]): Structure matching the chosen block_type that defines the block's content.
        format (str): Response format selector applied across all tools.
    
    Returns:
        block_id (str): The unique identifier assigned to the newly created block.
        type (str): The block type as stored in Notion.
        content (Dict[str, Any]): The content payload persisted for this block.
        created_time (str): ISO 8601 timestamp marking block creation.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not parent_id or not isinstance(parent_id, str):
            raise ValueError("Parent ID must be a non-empty string")
        if not block_type or not isinstance(block_type, str):
            raise ValueError("Block type must be a non-empty string")
        if not content or not isinstance(content, dict):
            raise ValueError("Content must be a non-empty dictionary")
        return api.notion_create_block(parent_id, block_type, content, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_update_block(block_id: str, block_type: Optional[str] = None, content: Optional[Dict[str, Any]] = None, archived: Optional[bool] = None, format: str = "markdown") -> dict:
    """Modify the type, content, or archived status of an existing block.
    
    Args:
        block_id (str): The unique identifier of the block to update.
        block_type (str): New block type if changing the type.
        content (Dict[str, Any]): Updated content structure matching the block type.
        archived (bool): Whether to archive (true) or restore (false) the block.
        format (str): Response format selector applied across all tools.
    
    Returns:
        block_id (str): The unique identifier of the updated block.
        type (str): The block type after the update.
        content (Dict[str, Any]): The content payload after the update.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not block_id or not isinstance(block_id, str):
            raise ValueError("Block ID must be a non-empty string")
        return api.notion_update_block(block_id, block_type, content, archived, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_delete_block(block_id: str, format: str = "markdown") -> dict:
    """Delete (archive) a specific block.
    
    Args:
        block_id (str): The unique identifier of the block to delete.
        format (str): Response format selector applied across all tools.
    
    Returns:
        block_id (str): The unique identifier of the deleted block.
        deleted (bool): True if the block was successfully archived.
    """
    try:
        if not block_id or not isinstance(block_id, str):
            raise ValueError("Block ID must be a non-empty string")
        return api.notion_delete_block(block_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_page(page_id: str, format: str = "markdown") -> dict:
    """Fetch metadata and properties of a specific page.
    
    Args:
        page_id (str): The unique identifier of the page to retrieve.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier of the retrieved page.
        title (str): Plain-text title of the page.
        properties (Dict[str, Any]): Key-value property map as defined in the page's parent database.
        created_time (str): ISO 8601 timestamp marking page creation.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Page ID must be a non-empty string")
        return api.notion_retrieve_page(page_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_create_page(parent: Dict[str, Any], properties: Optional[Dict[str, Any]] = None, children: Optional[List[Dict[str, Any]]] = None, format: str = "markdown") -> dict:
    """Create a new page inside a specified parent page or database.
    
    Args:
        parent (Dict[str, Any]): Parent descriptor containing either page_id or database_id.
        properties (Dict[str, Any]): Initial property values when the parent is a database.
        children (List[Dict[str, Any]]): Optional blocks to populate the new page body.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier assigned to the newly created page.
        parent (Dict[str, Any]): Parent descriptor as stored in Notion.
        properties (Dict[str, Any]): Properties of the page after creation.
        created_time (str): ISO 8601 timestamp marking page creation.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not parent or not isinstance(parent, dict):
            raise ValueError("Parent must be a non-empty dictionary")
        return api.notion_create_page(parent, properties, children, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_delete_page(page_id: str, format: str = "markdown") -> dict:
    """Delete (archive) a specific page.
    
    Args:
        page_id (str): The unique identifier of the page to delete.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier of the deleted page.
        deleted (bool): True if the page was successfully archived.
        archived (bool): Mirrors deleted status; true when the page is in the archive.
    """
    try:
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Page ID must be a non-empty string")
        return api.notion_delete_page(page_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_update_page_properties(page_id: str, properties: Dict[str, Any], format: str = "markdown") -> dict:
    """Update property values of an existing page.
    
    Args:
        page_id (str): The unique identifier of the page whose properties will be updated.
        properties (Dict[str, Any]): Map of property names to updated values.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier of the updated page.
        updated_properties (List[str]): List of property keys that were modified.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Page ID must be a non-empty string")
        if not properties or not isinstance(properties, dict):
            raise ValueError("Properties must be a non-empty dictionary")
        return api.notion_update_page_properties(page_id, properties, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_update_page_content(page_id: str, children: List[Dict[str, Any]], format: str = "markdown") -> dict:
    """Append or replace content blocks within an existing page.
    
    Args:
        page_id (str): The unique identifier of the page whose content will be updated.
        children (List[Dict[str, Any]]): Array of block objects to append to the page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier of the updated page.
        children_count (int): Total number of child blocks now present on the page.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Page ID must be a non-empty string")
        if not children or not isinstance(children, list):
            raise ValueError("Children must be a non-empty list")
        return api.notion_update_page_content(page_id, children, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_create_database(parent: Dict[str, Any], title: List[Dict[str, Any]], properties: Dict[str, Any], format: str = "markdown") -> dict:
    """Create a new database inside a specified parent page or workspace.
    
    Args:
        parent (Dict[str, Any]): Parent descriptor containing either page_id or workspace flag.
        title (List[Dict[str, Any]]): Rich-text array representing the database title.
        properties (Dict[str, Any]): Schema definition for database properties.
        format (str): Response format selector applied across all tools.
    
    Returns:
        database_id (str): The unique identifier assigned to the newly created database.
        title (str): Plain-text title of the database.
        properties (Dict[str, Any]): Property schema as stored in Notion.
        created_time (str): ISO 8601 timestamp marking database creation.
    """
    try:
        if not parent or not isinstance(parent, dict):
            raise ValueError("Parent must be a non-empty dictionary")
        if not title or not isinstance(title, list):
            raise ValueError("Title must be a non-empty list")
        if not properties or not isinstance(properties, dict):
            raise ValueError("Properties must be a non-empty dictionary")
        return api.notion_create_database(parent, title, properties, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_query_database(database_id: str, filter: Optional[Dict[str, Any]] = None, sorts: Optional[List[Dict[str, Any]]] = None, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
    """Query a database and retrieve pages that match optional filter and sort criteria.
    
    Args:
        database_id (str): The unique identifier of the database to query.
        filter (Dict[str, Any]): Notion filter object to constrain results.
        sorts (List[Dict[str, Any]]): List of sort objects to order results.
        start_cursor (str): Opaque cursor for retrieving the next page of results.
        page_size (int): Maximum number of results to return in this page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        results (List[Dict[str, Any]]): List of page objects each containing page_id and properties.
        next_cursor (str): Cursor for retrieving the next page; null when no more pages exist.
        has_more (bool): True when additional result pages are available.
    """
    try:
        if not database_id or not isinstance(database_id, str):
            raise ValueError("Database ID must be a non-empty string")
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValueError("Page size must be an integer between 1 and 100")
        return api.notion_query_database(database_id, filter, sorts, start_cursor, page_size, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_database(database_id: str, format: str = "markdown") -> dict:
    """Fetch metadata and property schema of a specific database.
    
    Args:
        database_id (str): The unique identifier of the database to retrieve.
        format (str): Response format selector applied across all tools.
    
    Returns:
        database_id (str): The unique identifier of the retrieved database.
        title (str): Plain-text title of the database.
        properties (Dict[str, Any]): Property schema defining columns and types.
        created_time (str): ISO 8601 timestamp marking database creation.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not database_id or not isinstance(database_id, str):
            raise ValueError("Database ID must be a non-empty string")
        return api.notion_retrieve_database(database_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_update_database(database_id: str, title: Optional[List[Dict[str, Any]]] = None, description: Optional[List[Dict[str, Any]]] = None, properties: Optional[Dict[str, Any]] = None, format: str = "markdown") -> dict:
    """Modify title, description, or property schema of an existing database.
    
    Args:
        database_id (str): The unique identifier of the database to update.
        title (List[Dict[str, Any]]): New rich-text title for the database.
        description (List[Dict[str, Any]]): New rich-text description for the database.
        properties (Dict[str, Any]): Updated property schema.
        format (str): Response format selector applied across all tools.
    
    Returns:
        database_id (str): The unique identifier of the updated database.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not database_id or not isinstance(database_id, str):
            raise ValueError("Database ID must be a non-empty string")
        return api.notion_update_database(database_id, title, description, properties, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_delete_database(database_id: str, format: str = "markdown") -> dict:
    """Delete (archive) a specific database.
    
    Args:
        database_id (str): The unique identifier of the database to delete.
        format (str): Response format selector applied across all tools.
    
    Returns:
        database_id (str): The unique identifier of the deleted database.
        deleted (bool): True if the database was successfully archived.
        archived (bool): Mirrors deleted status; true when the database is in the archive.
    """
    try:
        if not database_id or not isinstance(database_id, str):
            raise ValueError("Database ID must be a non-empty string")
        return api.notion_delete_database(database_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_create_database_item(database_id: str, properties: Dict[str, Any], format: str = "markdown") -> dict:
    """Add a new row (page) to a database with the provided properties.
    
    Args:
        database_id (str): The unique identifier of the database that will contain the new item.
        properties (Dict[str, Any]): Property values matching the database schema.
        format (str): Response format selector applied across all tools.
    
    Returns:
        page_id (str): The unique identifier assigned to the newly created page (database row).
        database_id (str): The unique identifier of the database containing this item.
        properties (Dict[str, Any]): Property values as stored after creation.
        created_time (str): ISO 8601 timestamp marking item creation.
    """
    try:
        if not database_id or not isinstance(database_id, str):
            raise ValueError("Database ID must be a non-empty string")
        if not properties or not isinstance(properties, dict):
            raise ValueError("Properties must be a non-empty dictionary")
        return api.notion_create_database_item(database_id, properties, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_search(query: Optional[str] = None, filter: Optional[Dict[str, Any]] = None, sort: Optional[Dict[str, Any]] = None, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
    """Global search across pages and databases by title with optional filtering and sorting.
    
    Args:
        query (str): Text to search for within titles.
        filter (Dict[str, Any]): Restrict results to only pages or only databases.
        sort (Dict[str, Any]): Sort criteria for the returned list.
        start_cursor (str): Opaque cursor for retrieving the next page of results.
        page_size (int): Maximum number of results to return in this page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        results (List[Dict[str, Any]]): List of objects each containing object_id, object_type, and title.
        next_cursor (str): Cursor for retrieving the next page; null when no more pages exist.
        has_more (bool): True when additional result pages are available.
    """
    try:
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValueError("Page size must be an integer between 1 and 100")
        return api.notion_search(query, filter, sort, start_cursor, page_size, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_list_all_users(start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
    """List every user in the workspace with optional pagination.
    
    Args:
        start_cursor (str): Opaque cursor for retrieving the next page of users.
        page_size (int): Maximum number of users to return in this page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        results (List[Dict[str, Any]]): List of user objects each containing user_id, name, and email.
        next_cursor (str): Cursor for retrieving the next page; null when no more pages exist.
    """
    try:
        if not isinstance(page_size, int) or page_size < 1:
            raise ValueError("Page size must be a positive integer")
        return api.notion_list_all_users(start_cursor, page_size, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_user(user_id: str, format: str = "markdown") -> dict:
    """Fetch detailed information about a specific user.
    
    Args:
        user_id (str): The unique identifier of the user to retrieve.
        format (str): Response format selector applied across all tools.
    
    Returns:
        user_id (str): The unique identifier of the retrieved user.
        name (str): Display name of the user.
        email (str): Email address associated with the user account.
        type (str): User type such as person or bot.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        return api.notion_retrieve_user(user_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_bot_user(format: str = "markdown") -> dict:
    """Fetch information about the bot user associated with the current integration token.
    
    Args:
        format (str): Response format selector applied across all tools.
    
    Returns:
        user_id (str): The unique identifier of the bot user.
        name (str): Display name of the bot.
        owner (Dict[str, Any]): Owner information for this bot integration.
    """
    try:
        return api.notion_retrieve_bot_user(format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_create_comment(rich_text: List[Dict[str, Any]], parent: Optional[Dict[str, Any]] = None, discussion_id: Optional[str] = None, format: str = "markdown") -> dict:
    """Add a new comment to a page or an existing discussion thread.
    
    Args:
        rich_text (List[Dict[str, Any]]): Rich-text array representing the body of the comment.
        parent (Dict[str, Any]): Must contain page_id when starting a new thread.
        discussion_id (str): Existing discussion thread ID when replying to a thread.
        format (str): Response format selector applied across all tools.
    
    Returns:
        comment_id (str): The unique identifier assigned to the newly created comment.
        rich_text (List[Dict[str, Any]]): The rich-text content as stored after creation.
        created_time (str): ISO 8601 timestamp marking comment creation.
    """
    try:
        if not rich_text or not isinstance(rich_text, list):
            raise ValueError("Rich text must be a non-empty list")
        return api.notion_create_comment(rich_text, parent, discussion_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_retrieve_comments(block_id: str, start_cursor: Optional[str] = None, page_size: int = 100, format: str = "markdown") -> dict:
    """Fetch unresolved comments attached to a page or block with optional pagination.
    
    Args:
        block_id (str): The unique identifier of the page or block whose comments are requested.
        start_cursor (str): Opaque cursor for retrieving the next page of comments.
        page_size (int): Maximum number of comments to return in this page.
        format (str): Response format selector applied across all tools.
    
    Returns:
        results (List[Dict[str, Any]]): List of comment objects each containing comment_id, rich_text, and created_time.
        next_cursor (str): Cursor for retrieving the next page; null when no more pages exist.
    """
    try:
        if not block_id or not isinstance(block_id, str):
            raise ValueError("Block ID must be a non-empty string")
        if not isinstance(page_size, int) or page_size < 1:
            raise ValueError("Page size must be a positive integer")
        return api.notion_retrieve_comments(block_id, start_cursor, page_size, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_update_comment(comment_id: str, rich_text: List[Dict[str, Any]], format: str = "markdown") -> dict:
    """Modify the rich-text content of an existing comment.
    
    Args:
        comment_id (str): The unique identifier of the comment to update.
        rich_text (List[Dict[str, Any]]): New rich-text array replacing the previous content.
        format (str): Response format selector applied across all tools.
    
    Returns:
        comment_id (str): The unique identifier of the updated comment.
        rich_text (List[Dict[str, Any]]): The rich-text content after the update.
        last_edited_time (str): ISO 8601 timestamp of the most recent edit.
    """
    try:
        if not comment_id or not isinstance(comment_id, str):
            raise ValueError("Comment ID must be a non-empty string")
        if not rich_text or not isinstance(rich_text, list):
            raise ValueError("Rich text must be a non-empty list")
        return api.notion_update_comment(comment_id, rich_text, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_delete_comment(comment_id: str, format: str = "markdown") -> dict:
    """Delete a specific comment.
    
    Args:
        comment_id (str): The unique identifier of the comment to delete.
        format (str): Response format selector applied across all tools.
    
    Returns:
        comment_id (str): The unique identifier of the deleted comment.
        deleted (bool): True if the comment was successfully removed.
    """
    try:
        if not comment_id or not isinstance(comment_id, str):
            raise ValueError("Comment ID must be a non-empty string")
        return api.notion_delete_comment(comment_id, format)
    except Exception as e:
        raise e

@mcp.tool()
def notion_resolve_comment(comment_id: str, resolved: bool = True, format: str = "markdown") -> dict:
    """Mark a comment as resolved or unresolved.
    
    Args:
        comment_id (str): The unique identifier of the comment to resolve or unresolve.
        resolved (bool): True to mark as resolved; false to reopen.
        format (str): Response format selector applied across all tools.
    
    Returns:
        comment_id (str): The unique identifier of the resolved comment.
        resolved (bool): Resolution status after the operation.
        resolved_time (str): ISO 8601 timestamp when the comment was resolved; absent when unresolved.
        resolved_by (Dict[str, Any]): User who resolved the comment; absent when unresolved.
    """
    try:
        if not comment_id or not isinstance(comment_id, str):
            raise ValueError("Comment ID must be a non-empty string")
        if not isinstance(resolved, bool):
            raise ValueError("Resolved must be a boolean value")
        return api.notion_resolve_comment(comment_id, resolved, format)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()