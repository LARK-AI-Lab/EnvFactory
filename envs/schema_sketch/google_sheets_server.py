# Server: GoogleSheets

def list_spreadsheets() -> list:
    """
    List all spreadsheets in the configured Google Drive folder.
    
    Returns:
        list: Each spreadsheet contains {
            "spreadsheet_id": str,
            "title": str
        }
    """
    pass

def get_spreadsheet_info(spreadsheet_id: str) -> dict:
    """
    Get basic information about a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        
    Returns:
        dict: {
            "spreadsheet_id": str,
            "title": str,
            "sheets": list,
            "created_time": str,
            "modified_time": str
        }
    """
    pass

def list_sheets(spreadsheet_id: str) -> list:
    """
    List all sheets in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        
    Returns:
        list: List of sheet names
    """
    pass

def get_sheet_data(spreadsheet_id: str, sheet: str, range: str = None) -> list:
    """
    Get data from a specific sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        range (str): [Optional] Cell range in A1 notation (e.g., 'A1:C10')
        
    Returns:
        list: 2D array of the sheet data
    """
    pass

def create_spreadsheet(title: str) -> dict:
    """
    Create a new Google Spreadsheet.
    
    Args:
        title (str): The title of the new spreadsheet
        
    Returns:
        dict: {
            "spreadsheet_id": str,
            "title": str,
            "url": str
        }
    """
    pass

def create_sheet(spreadsheet_id: str, title: str) -> dict:
    """
    Create a new sheet tab in an existing Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        title (str): The title for the new sheet
        
    Returns:
        dict: {
            "sheet_id": int,
            "title": str,
            "spreadsheet_id": str
        }
    """
    pass

def batch_update_cells(spreadsheet_id: str, sheet: str, ranges: dict = None, range: str = None, data: list = None) -> dict:
    """
    Update cells in a Google Spreadsheet. Can update a single range or multiple ranges.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        ranges (dict): [Optional] Dictionary mapping range strings to 2D arrays of values for batch updates
        range (str): [Optional] Single cell range in A1 notation (e.g., 'A1:C10') for single update
        data (list): [Optional] 2D array of values for single range update (required if range is provided)
        
    Returns:
        dict: {
            "updated_ranges": list,
            "total_updated_cells": int,
            "spreadsheet_id": str
        }
    """
    pass

def add_rows(spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
    """
    Add rows to a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        count (int): [Optional] Number of rows to add (default 1)
        
    Returns:
        dict: {
            "added_rows": int,
            "sheet": str,
            "spreadsheet_id": str
        }
    """
    pass

def add_columns(spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
    """
    Add columns to a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        count (int): [Optional] Number of columns to add (default 1)
        
    Returns:
        dict: {
            "added_columns": int,
            "sheet": str,
            "spreadsheet_id": str
        }
    """
    pass

def delete_rows(spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
    """
    Delete rows from a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        start_index (int): The 0-based index of the first row to delete
        count (int): [Optional] Number of rows to delete (default 1)
        
    Returns:
        dict: {
            "deleted_rows": int,
            "sheet": str,
            "spreadsheet_id": str
        }
    """
    pass

def delete_columns(spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
    """
    Delete columns from a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet
        start_index (int): The 0-based index of the first column to delete
        count (int): [Optional] Number of columns to delete (default 1)
        
    Returns:
        dict: {
            "deleted_columns": int,
            "sheet": str,
            "spreadsheet_id": str
        }
    """
    pass

def copy_sheet(spreadsheet_id: str, sheet: str, new_sheet_name: str) -> dict:
    """
    Copy a sheet within a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet to copy
        new_sheet_name (str): The name for the new copied sheet
        
    Returns:
        dict: {
            "sheet_id": int,
            "title": str,
            "spreadsheet_id": str
        }
    """
    pass

def rename_sheet(spreadsheet_id: str, sheet: str, new_name: str) -> dict:
    """
    Rename a sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in the URL)
        sheet (str): The name of the sheet to rename
        new_name (str): The new name for the sheet
        
    Returns:
        dict: {
            "old_name": str,
            "new_name": str,
            "spreadsheet_id": str
        }
    """
    pass

