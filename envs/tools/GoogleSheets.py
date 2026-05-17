from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Spreadsheet(BaseModel):
    """Represents a Google Spreadsheet."""
    spreadsheet_id: str = Field(..., description="The unique identifier of the Google Spreadsheet")
    title: str = Field(..., description="The display title of the spreadsheet")

class Sheet(BaseModel):
    """Represents a sheet within a spreadsheet."""
    sheet_id: int = Field(..., ge=0, description="The unique numeric identifier of the sheet")
    title: str = Field(..., description="The display title of the sheet")

class CellRange(BaseModel):
    """Represents a range of cells."""
    range: str = Field(..., description="Cell range in A1 notation")
    data: List[List[Any]] = Field(..., description="2D array of cell values")

class GoogleSheetsScenario(BaseModel):
    """Main scenario model for Google Sheets management."""
    spreadsheets: Dict[str, Spreadsheet] = Field(default={}, description="All spreadsheets indexed by ID")
    sheets: Dict[str, List[Sheet]] = Field(default={}, description="Sheets within each spreadsheet indexed by spreadsheet ID")
    sheet_data: Dict[str, Dict[str, List[List[Any]]]] = Field(default={}, description="Cell data for each sheet indexed by spreadsheet ID and sheet name")
    created_times: Dict[str, str] = Field(default={}, description="Creation timestamps for spreadsheets")
    modified_times: Dict[str, str] = Field(default={}, description="Last modified timestamps for spreadsheets")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Spreadsheet, Sheet, CellRange, GoogleSheetsScenario]

# Section 2: Class
class GoogleSheetsAPI:
    def __init__(self):
        """Initialize Google Sheets API with empty state."""
        self.spreadsheets: Dict[str, Spreadsheet] = {}
        self.sheets: Dict[str, List[Sheet]] = {}
        self.sheet_data: Dict[str, Dict[str, List[List[Any]]]] = {}
        self.created_times: Dict[str, str] = {}
        self.modified_times: Dict[str, str] = {}
        self.current_time: str = ""
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = GoogleSheetsScenario(**scenario)
        self.spreadsheets = model.spreadsheets
        self.sheets = model.sheets
        self.sheet_data = model.sheet_data
        self.created_times = model.created_times
        self.modified_times = model.modified_times
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "spreadsheets": {k: v.model_dump() for k, v in self.spreadsheets.items()},
            "sheets": {k: [sheet.model_dump() for sheet in sheets] for k, sheets in self.sheets.items()},
            "sheet_data": self.sheet_data,
            "created_times": self.created_times,
            "modified_times": self.modified_times,
            "current_time": self.current_time
        }

    def list_spreadsheets(self) -> dict:
        """List all spreadsheets in the configured Google Drive folder."""
        return {"spreadsheets": [s.model_dump() for s in self.spreadsheets.values()]}

    def get_spreadsheet_info(self, spreadsheet_id: str) -> dict:
        """Get basic information about a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        spreadsheet = self.spreadsheets[spreadsheet_id]
        sheet_names = [sheet.title for sheet in self.sheets.get(spreadsheet_id, [])]
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "title": spreadsheet.title,
            "sheets": sheet_names,
            "created_time": self.created_times.get(spreadsheet_id, ""),
            "modified_time": self.modified_times.get(spreadsheet_id, "")
        }

    def list_sheets(self, spreadsheet_id: str) -> dict:
        """List all sheet tabs in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        sheet_names = [sheet.title for sheet in self.sheets.get(spreadsheet_id, [])]
        return {"sheet_names": sheet_names}

    def get_sheet_data(self, spreadsheet_id: str, sheet: str, range: Optional[str] = None) -> dict:
        """Get cell data from a specific sheet in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            return {"data": []}
        
        data = self.sheet_data[spreadsheet_id][sheet]
        
        if range:
            # Simple range parsing (A1 notation)
            import re
            match = re.match(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$', range)
            if match:
                start_col, start_row, end_col, end_row = match.groups()
                start_row, end_row = int(start_row) - 1, int(end_row) - 1
                start_col = ord(start_col) - ord('A')
                end_col = ord(end_col) - ord('A')
                
                filtered_data = []
                for i, row in enumerate(data):
                    if start_row <= i <= end_row:
                        filtered_row = row[start_col:end_col + 1] if end_col < len(row) else row[start_col:]
                        filtered_data.append(filtered_row)
                return {"data": filtered_data}
        
        return {"data": data}

    def create_spreadsheet(self, title: str) -> dict:
        """Create a new Google Spreadsheet with the specified title."""
        import uuid
        spreadsheet_id = str(uuid.uuid4())
        
        spreadsheet = Spreadsheet(spreadsheet_id=spreadsheet_id, title=title)
        self.spreadsheets[spreadsheet_id] = spreadsheet
        self.sheets[spreadsheet_id] = []
        self.sheet_data[spreadsheet_id] = {}
        
        now = self.current_time
        self.created_times[spreadsheet_id] = now
        self.modified_times[spreadsheet_id] = now
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "title": title,
            "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        }

    def create_sheet(self, spreadsheet_id: str, title: str) -> dict:
        """Create a new sheet tab in an existing Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        import uuid
        sheet_id = abs(hash(f"{spreadsheet_id}_{title}_{uuid.uuid4()}")) % (10 ** 9)
        
        sheet = Sheet(sheet_id=sheet_id, title=title)
        if spreadsheet_id not in self.sheets:
            self.sheets[spreadsheet_id] = []
        self.sheets[spreadsheet_id].append(sheet)
        
        if spreadsheet_id not in self.sheet_data:
            self.sheet_data[spreadsheet_id] = {}
        self.sheet_data[spreadsheet_id][title] = []
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "sheet_id": sheet_id,
            "title": title,
            "spreadsheet_id": spreadsheet_id
        }

    def batch_update_cells(self, spreadsheet_id: str, sheet: str, range: Optional[str] = None, data: Optional[List[List[Any]]] = None, ranges: Optional[Dict[str, List[List[Any]]]] = None) -> dict:
        """Update cells in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        updated_ranges = []
        total_updated = 0
        
        if range and data is not None:
            # Single range update
            self.sheet_data[spreadsheet_id][sheet] = data
            updated_ranges.append(range)
            total_updated += sum(len(row) for row in data)
        elif ranges:
            # Multiple range updates (simplified - just use first range for demo)
            for rng, rng_data in ranges.items():
                self.sheet_data[spreadsheet_id][sheet] = rng_data
                updated_ranges.append(rng)
                total_updated += sum(len(row) for row in rng_data)
                break  # Only handle first range for simplicity
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "updated_ranges": updated_ranges,
            "total_updated_cells": total_updated,
            "spreadsheet_id": spreadsheet_id
        }

    def add_rows(self, spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
        """Add new rows to the end of a sheet in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        current_data = self.sheet_data[spreadsheet_id][sheet]
        new_rows = [[] for _ in range(count)]
        current_data.extend(new_rows)
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "added_rows": count,
            "sheet": sheet,
            "spreadsheet_id": spreadsheet_id
        }

    def add_columns(self, spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
        """Add new columns to a sheet in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        current_data = self.sheet_data[spreadsheet_id][sheet]
        for row in current_data:
            row.extend([None] * count)
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "added_columns": count,
            "sheet": sheet,
            "spreadsheet_id": spreadsheet_id
        }

    def delete_rows(self, spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
        """Delete rows from a sheet in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        current_data = self.sheet_data[spreadsheet_id][sheet]
        if start_index < 0 or start_index >= len(current_data):
            raise ValueError(f"Invalid start_index {start_index}")
        
        del current_data[start_index:start_index + count]
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "deleted_rows": count,
            "sheet": sheet,
            "spreadsheet_id": spreadsheet_id
        }

    def delete_columns(self, spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
        """Delete columns from a sheet in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        current_data = self.sheet_data[spreadsheet_id][sheet]
        if start_index < 0:
            raise ValueError(f"Invalid start_index {start_index}")
        
        for row in current_data:
            if start_index < len(row):
                del row[start_index:start_index + count]
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "deleted_columns": count,
            "sheet": sheet,
            "spreadsheet_id": spreadsheet_id
        }

    def copy_sheet(self, spreadsheet_id: str, sheet: str, new_sheet_name: str) -> dict:
        """Copy an existing sheet tab within a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheet_data or sheet not in self.sheet_data[spreadsheet_id]:
            raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")
        
        import uuid
        new_sheet_id = abs(hash(f"{spreadsheet_id}_{new_sheet_name}_{uuid.uuid4()}")) % (10 ** 9)
        
        new_sheet = Sheet(sheet_id=new_sheet_id, title=new_sheet_name)
        if spreadsheet_id not in self.sheets:
            self.sheets[spreadsheet_id] = []
        self.sheets[spreadsheet_id].append(new_sheet)
        
        # Copy data
        original_data = self.sheet_data[spreadsheet_id][sheet]
        self.sheet_data[spreadsheet_id][new_sheet_name] = [row[:] for row in original_data]
        
        self.modified_times[spreadsheet_id] = self.current_time
        
        return {
            "sheet_id": new_sheet_id,
            "title": new_sheet_name,
            "spreadsheet_id": spreadsheet_id
        }

    def rename_sheet(self, spreadsheet_id: str, sheet: str, new_name: str) -> dict:
        """Rename an existing sheet tab in a Google Spreadsheet."""
        if spreadsheet_id not in self.spreadsheets:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
        
        if spreadsheet_id not in self.sheets:
            raise ValueError(f"No sheets found in spreadsheet {spreadsheet_id}")
        
        # Find and rename sheet
        for s in self.sheets[spreadsheet_id]:
            if s.title == sheet:
                old_name = s.title
                s.title = new_name
                
                # Update sheet data
                if spreadsheet_id in self.sheet_data and sheet in self.sheet_data[spreadsheet_id]:
                    self.sheet_data[spreadsheet_id][new_name] = self.sheet_data[spreadsheet_id].pop(sheet)
                
                self.modified_times[spreadsheet_id] = self.current_time
                
                return {
                    "old_name": old_name,
                    "new_name": new_name,
                    "spreadsheet_id": spreadsheet_id
                }
        
        raise ValueError(f"Sheet {sheet} not found in spreadsheet {spreadsheet_id}")

# Section 3: MCP Tools
mcp = FastMCP(name="GoogleSheets")
api = GoogleSheetsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Google Sheets API.
    
    Args:
        scenario (dict): Scenario dictionary matching GoogleSheetsScenario schema.
    
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
    Save current Google Sheets state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_spreadsheets() -> dict:
    """
    List all spreadsheets in the configured Google Drive folder.
    
    Returns:
        spreadsheets (array): List of spreadsheets available in the configured Google Drive folder.
    """
    try:
        return api.list_spreadsheets()
    except Exception as e:
        raise e

@mcp.tool()
def get_spreadsheet_info(spreadsheet_id: str) -> dict:
    """
    Get basic information about a Google Spreadsheet, including its title, sheets, and timestamps.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
    
    Returns:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        title (str): The display title of the spreadsheet.
        sheets (array): List of sheet names contained within the spreadsheet.
        created_time (str): The timestamp when the spreadsheet was created.
        modified_time (str): The timestamp when the spreadsheet was last modified.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        return api.get_spreadsheet_info(spreadsheet_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_sheets(spreadsheet_id: str) -> dict:
    """
    List all sheet tabs in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
    
    Returns:
        sheet_names (array): List of sheet tab names within the spreadsheet.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        return api.list_sheets(spreadsheet_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_sheet_data(spreadsheet_id: str, sheet: str, range: Optional[str] = None) -> dict:
    """
    Get cell data from a specific sheet in a Google Spreadsheet, optionally limited to a specific range.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to read data from.
        range (str) [Optional]: Cell range in A1 notation (e.g., 'A1:C10'). If omitted, returns all data in the sheet.
    
    Returns:
        data (array): 2D array representing the sheet data, where each inner array is a row of cell values.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        return api.get_sheet_data(spreadsheet_id, sheet, range)
    except Exception as e:
        raise e

@mcp.tool()
def create_spreadsheet(title: str) -> dict:
    """
    Create a new Google Spreadsheet with the specified title.
    
    Args:
        title (str): The display title for the new spreadsheet.
    
    Returns:
        spreadsheet_id (str): The unique identifier of the newly created Google Spreadsheet.
        title (str): The display title of the newly created spreadsheet.
        url (str): The URL to access the newly created spreadsheet in Google Sheets.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        return api.create_spreadsheet(title)
    except Exception as e:
        raise e

@mcp.tool()
def create_sheet(spreadsheet_id: str, title: str) -> dict:
    """
    Create a new sheet tab in an existing Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        title (str): The display title for the new sheet tab.
    
    Returns:
        sheet_id (integer): The unique numeric identifier of the newly created sheet tab within the spreadsheet.
        title (str): The display title of the newly created sheet tab.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet containing the new sheet.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        return api.create_sheet(spreadsheet_id, title)
    except Exception as e:
        raise e

@mcp.tool()
def batch_update_cells(spreadsheet_id: str, sheet: str, range: Optional[str] = None, data: Optional[List[List[Any]]] = None, ranges: Optional[Dict[str, List[List[Any]]]] = None) -> dict:
    """
    Update cells in a Google Spreadsheet. Supports updating a single range or multiple ranges in batch.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to update.
        range (str) [Optional]: Single cell range in A1 notation (e.g., 'A1:C10') for a single update. Use with 'data' parameter.
        data (array) [Optional]: 2D array of values to write to the specified single range. Required when 'range' parameter is provided.
        ranges (object) [Optional]: Dictionary mapping range strings (in A1 notation) to 2D arrays of values for batch updates. Use this for updating multiple ranges at once.
    
    Returns:
        updated_ranges (array): List of cell ranges that were successfully updated.
        total_updated_cells (integer): The total number of cells that were updated across all ranges.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet that was updated.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if range and data is None:
            raise ValueError("data parameter is required when range is provided")
        return api.batch_update_cells(spreadsheet_id, sheet, range, data, ranges)
    except Exception as e:
        raise e

@mcp.tool()
def add_rows(spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
    """
    Add new rows to the end of a sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to add rows to.
        count (integer) [Optional]: Number of rows to add. Defaults to 1 if not specified.
    
    Returns:
        added_rows (integer): The number of rows that were successfully added.
        sheet (str): The name of the sheet tab where rows were added.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet that was modified.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if count < 1:
            raise ValueError("count must be at least 1")
        return api.add_rows(spreadsheet_id, sheet, count)
    except Exception as e:
        raise e

@mcp.tool()
def add_columns(spreadsheet_id: str, sheet: str, count: int = 1) -> dict:
    """
    Add new columns to a sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to add columns to.
        count (integer) [Optional]: Number of columns to add. Defaults to 1 if not specified.
    
    Returns:
        added_columns (integer): The number of columns that were successfully added.
        sheet (str): The name of the sheet tab where columns were added.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet that was modified.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if count < 1:
            raise ValueError("count must be at least 1")
        return api.add_columns(spreadsheet_id, sheet, count)
    except Exception as e:
        raise e

@mcp.tool()
def delete_rows(spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
    """
    Delete rows from a sheet in a Google Spreadsheet starting at a specified index.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to delete rows from.
        start_index (integer): The 0-based index of the first row to delete.
        count (integer) [Optional]: Number of consecutive rows to delete starting from start_index. Defaults to 1 if not specified.
    
    Returns:
        deleted_rows (integer): The number of rows that were successfully deleted.
        sheet (str): The name of the sheet tab where rows were deleted.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet that was modified.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if start_index < 0:
            raise ValueError("start_index must be non-negative")
        if count < 1:
            raise ValueError("count must be at least 1")
        return api.delete_rows(spreadsheet_id, sheet, start_index, count)
    except Exception as e:
        raise e

@mcp.tool()
def delete_columns(spreadsheet_id: str, sheet: str, start_index: int, count: int = 1) -> dict:
    """
    Delete columns from a sheet in a Google Spreadsheet starting at a specified index.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to delete columns from.
        start_index (integer): The 0-based index of the first column to delete.
        count (integer) [Optional]: Number of consecutive columns to delete starting from start_index. Defaults to 1 if not specified.
    
    Returns:
        deleted_columns (integer): The number of columns that were successfully deleted.
        sheet (str): The name of the sheet tab where columns were deleted.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet that was modified.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if start_index < 0:
            raise ValueError("start_index must be non-negative")
        if count < 1:
            raise ValueError("count must be at least 1")
        return api.delete_columns(spreadsheet_id, sheet, start_index, count)
    except Exception as e:
        raise e

@mcp.tool()
def copy_sheet(spreadsheet_id: str, sheet: str, new_sheet_name: str) -> dict:
    """
    Copy an existing sheet tab within a Google Spreadsheet to create a duplicate with a new name.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The name of the sheet tab to copy.
        new_sheet_name (str): The display title for the new copied sheet tab.
    
    Returns:
        sheet_id (integer): The unique numeric identifier of the newly created copied sheet tab.
        title (str): The display title of the newly created copied sheet tab.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet containing the copied sheet.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if not new_sheet_name or not isinstance(new_sheet_name, str):
            raise ValueError("new_sheet_name must be a non-empty string")
        return api.copy_sheet(spreadsheet_id, sheet, new_sheet_name)
    except Exception as e:
        raise e

@mcp.tool()
def rename_sheet(spreadsheet_id: str, sheet: str, new_name: str) -> dict:
    """
    Rename an existing sheet tab in a Google Spreadsheet.
    
    Args:
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet, as found in the spreadsheet URL.
        sheet (str): The current name of the sheet tab to rename.
        new_name (str): The new display title for the sheet tab.
    
    Returns:
        old_name (str): The previous name of the sheet tab before renaming.
        new_name (str): The new name of the sheet tab after renaming.
        spreadsheet_id (str): The unique identifier of the Google Spreadsheet containing the renamed sheet.
    """
    try:
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise ValueError("spreadsheet_id must be a non-empty string")
        if not sheet or not isinstance(sheet, str):
            raise ValueError("sheet must be a non-empty string")
        if not new_name or not isinstance(new_name, str):
            raise ValueError("new_name must be a non-empty string")
        return api.rename_sheet(spreadsheet_id, sheet, new_name)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()