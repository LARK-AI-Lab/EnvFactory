# Server: Notion

def notion_append_block_children(block_id: str, children: list, format: str = "markdown") -> dict:
    """
    Append child blocks to a parent block.
    
    Args:
        block_id (str): The ID of the parent block
        children (list): Array of block objects to append
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "block_id": str,
            "children_count": int
        }
    """
    pass

def notion_retrieve_block_children(block_id: str, start_cursor: str = None, page_size: int = 100, format: str = "markdown") -> dict:
    """
    Retrieve the children of a specific block.
    
    Args:
        block_id (str): The ID of the parent block
        start_cursor (str): [Optional] Cursor for the next page of results
        page_size (int): [Optional] Number of blocks to retrieve (default: 100, max: 100)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "results": list of dicts with block_id, type, content,
            "next_cursor": str
        }
    """
    pass

def notion_create_block(parent_id: str, block_type: str, content: dict, format: str = "markdown") -> dict:
    """
    Create a new block in Notion.
    
    Args:
        parent_id (str): The ID of the parent block or page
        block_type (str): Type of block to create (e.g., "paragraph", "heading_1", "bulleted_list_item", etc.)
        content (dict): Content of the block matching the block type structure
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "block_id": str,
            "type": str,
            "content": dict,
            "created_time": str (ISO 8601),
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_update_block(block_id: str, block_type: str = None, content: dict = None, archived: bool = None, format: str = "markdown") -> dict:
    """
    Update a specific block in Notion.
    
    Args:
        block_id (str): The ID of the block to update
        block_type (str): [Optional] Type of block (required if changing type)
        content (dict): [Optional] Updated content of the block
        archived (bool): [Optional] Whether to archive the block
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "block_id": str,
            "type": str,
            "content": dict,
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_delete_block(block_id: str, format: str = "markdown") -> dict:
    """
    Delete a specific block.
    
    Args:
        block_id (str): The ID of the block to delete
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "block_id": str,
            "deleted": bool
        }
    """
    pass

def notion_retrieve_page(page_id: str, format: str = "markdown") -> dict:
    """
    Retrieve information about a specific page.
    
    Args:
        page_id (str): The ID of the page to retrieve
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "title": str,
            "properties": dict,
            "created_time": str (ISO 8601),
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_create_page(parent: dict, properties: dict = None, children: list = None, format: str = "markdown") -> dict:
    """
    Create a new page in Notion.
    
    Args:
        parent (dict): Parent object of the page (must include page_id or database_id)
        properties (dict): [Optional] Properties of the page
        children (list): [Optional] Array of block objects to add as children
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "parent": dict,
            "properties": dict,
            "created_time": str (ISO 8601),
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_delete_page(page_id: str, format: str = "markdown") -> dict:
    """
    Delete a specific page in Notion.
    
    Args:
        page_id (str): The ID of the page to delete
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "deleted": bool,
            "archived": bool
        }
    """
    pass

def notion_update_page_properties(page_id: str, properties: dict, format: str = "markdown") -> dict:
    """
    Update properties of a page.
    
    Args:
        page_id (str): The ID of the page to update
        properties (dict): Properties to update
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "updated_properties": list,
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_update_page_content(page_id: str, children: list, format: str = "markdown") -> dict:
    """
    Update the content of a page by appending or replacing blocks.
    
    Args:
        page_id (str): The ID of the page to update
        children (list): Array of block objects to append to the page
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "children_count": int,
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_create_database(parent: dict, title: list, properties: dict, format: str = "markdown") -> dict:
    """
    Create a new database.
    
    Args:
        parent (dict): Parent object of the database
        title (list): Title of the database as a rich text array
        properties (dict): Property schema of the database
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "database_id": str,
            "title": str,
            "properties": dict,
            "created_time": str (ISO 8601)
        }
    """
    pass

def notion_query_database(database_id: str, filter: dict = None, sorts: list = None, start_cursor: str = None, page_size: int = 100, format: str = "markdown") -> dict:
    """
    Query a database.
    
    Args:
        database_id (str): The ID of the database to query
        filter (dict): [Optional] Filter conditions
        sorts (list): [Optional] Sorting conditions
        start_cursor (str): [Optional] Cursor for the next page of results
        page_size (int): [Optional] Number of results to retrieve (default: 100, max: 100)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "results": list of dicts with page_id, properties,
            "next_cursor": str,
            "has_more": bool
        }
    """
    pass

def notion_retrieve_database(database_id: str, format: str = "markdown") -> dict:
    """
    Retrieve information about a specific database.
    
    Args:
        database_id (str): The ID of the database to retrieve
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "database_id": str,
            "title": str,
            "properties": dict,
            "created_time": str (ISO 8601),
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_update_database(database_id: str, title: list = None, description: list = None, properties: dict = None, format: str = "markdown") -> dict:
    """
    Update information about a database.
    
    Args:
        database_id (str): The ID of the database to update
        title (list): [Optional] New title for the database
        description (list): [Optional] New description for the database
        properties (dict): [Optional] Updated property schema
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "database_id": str,
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_delete_database(database_id: str, format: str = "markdown") -> dict:
    """
    Delete a specific database in Notion.
    
    Args:
        database_id (str): The ID of the database to delete
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "database_id": str,
            "deleted": bool,
            "archived": bool
        }
    """
    pass

def notion_create_database_item(database_id: str, properties: dict, format: str = "markdown") -> dict:
    """
    Create a new item in a Notion database.
    
    Args:
        database_id (str): The ID of the database to add the item to
        properties (dict): The properties of the new item matching the database schema
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "page_id": str,
            "database_id": str,
            "properties": dict,
            "created_time": str (ISO 8601)
        }
    """
    pass

def notion_search(query: str = None, filter: dict = None, sort: dict = None, start_cursor: str = None, page_size: int = 100, format: str = "markdown") -> dict:
    """
    Search pages or databases by title.
    
    Args:
        query (str): [Optional] Text to search for in page or database titles
        filter (dict): [Optional] Criteria to limit results to either only pages or only databases
        sort (dict): [Optional] Criteria to sort the results
        start_cursor (str): [Optional] Pagination start cursor
        page_size (int): [Optional] Number of results to retrieve (default: 100, max: 100)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "results": list of dicts with object_id, object_type, title,
            "next_cursor": str,
            "has_more": bool
        }
    """
    pass

def notion_list_all_users(start_cursor: str = None, page_size: int = None, format: str = "markdown") -> dict:
    """
    List all users in the Notion workspace.
    
    Args:
        start_cursor (str): [Optional] Pagination start cursor for listing users
        page_size (int): [Optional] Number of users to retrieve (max: 100)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "results": list of dicts with user_id, name, email,
            "next_cursor": str
        }
    """
    pass

def notion_retrieve_user(user_id: str, format: str = "markdown") -> dict:
    """
    Retrieve a specific user by user_id in Notion.
    
    Args:
        user_id (str): The ID of the user to retrieve
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "user_id": str,
            "name": str,
            "email": str,
            "type": str
        }
    """
    pass

def notion_retrieve_bot_user(format: str = "markdown") -> dict:
    """
    Retrieve the bot user associated with the current token in Notion.
    
    Args:
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "user_id": str,
            "name": str,
            "owner": dict
        }
    """
    pass

def notion_create_comment(rich_text: list, parent: dict = None, discussion_id: str = None, format: str = "markdown") -> dict:
    """
    Create a comment in Notion.
    
    Args:
        rich_text (list): Array of rich text objects representing the comment content
        parent (dict): [Optional] Must include page_id if used
        discussion_id (str): [Optional] An existing discussion thread ID
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "comment_id": str,
            "rich_text": list,
            "created_time": str (ISO 8601)
        }
    """
    pass

def notion_retrieve_comments(block_id: str, start_cursor: str = None, page_size: int = None, format: str = "markdown") -> dict:
    """
    Retrieve a list of unresolved comments from a Notion page or block.
    
    Args:
        block_id (str): The ID of the block or page whose comments you want to retrieve
        start_cursor (str): [Optional] Pagination start cursor
        page_size (int): [Optional] Number of comments to retrieve (max: 100)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "results": list of dicts with comment_id, rich_text, created_time,
            "next_cursor": str
        }
    """
    pass

def notion_update_comment(comment_id: str, rich_text: list, format: str = "markdown") -> dict:
    """
    Update a comment in Notion.
    
    Args:
        comment_id (str): The ID of the comment to update
        rich_text (list): Array of rich text objects representing the updated comment content
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "comment_id": str,
            "rich_text": list,
            "last_edited_time": str (ISO 8601)
        }
    """
    pass

def notion_delete_comment(comment_id: str, format: str = "markdown") -> dict:
    """
    Delete a comment in Notion.
    
    Args:
        comment_id (str): The ID of the comment to delete
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "comment_id": str,
            "deleted": bool
        }
    """
    pass

def notion_resolve_comment(comment_id: str, resolved: bool = True, format: str = "markdown") -> dict:
    """
    Mark a comment as resolved or unresolved in Notion.
    
    Args:
        comment_id (str): The ID of the comment to resolve or unresolve
        resolved (bool): [Optional] Whether to mark as resolved (default: True)
        format (str): [Optional] Response format: "json" or "markdown" (default: "markdown")
        
    Returns:
        dict: {
            "comment_id": str,
            "resolved": bool,
            "resolved_time": str (ISO 8601) if resolved,
            "resolved_by": dict if resolved
        }
    """
    pass
