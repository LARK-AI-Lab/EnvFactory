from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
import platform
import tempfile

# Section 1: Schema
class SheetInfo(BaseModel):
    """Information about an Excel sheet."""
    name: str = Field(..., description="The name of the sheet as displayed in Excel")
    index: int = Field(..., ge=0, description="The zero-based index position of the sheet within the workbook")
    visibility: str = Field(..., description="The visibility state of the sheet (e.g., 'visible', 'hidden', 'veryHidden')")

class CellStyle(BaseModel):
    """Style information for a cell."""
    border: Optional[Dict[str, Any]] = Field(default=None, description="Border style configuration")
    font: Optional[Dict[str, Any]] = Field(default=None, description="Font style configuration")
    fill: Optional[Dict[str, Any]] = Field(default=None, description="Fill style configuration")
    numFmt: Optional[str] = Field(default=None, description="Number format string")
    decimalPlaces: Optional[int] = Field(default=None, ge=0, le=10, description="Number of decimal places for numeric formatting")

class ExcelScenario(BaseModel):
    """Main scenario model for Excel file operations."""
    file_path: str = Field(..., description="Absolute path to the Excel file")
    sheets: Dict[str, Dict[str, Any]] = Field(default={}, description="Sheet data storage")
    tables: Dict[str, str] = Field(default={}, description="Table name to range mapping")
    formats: Dict[str, Any] = Field(default={}, description="Stored formatting information")
    screen_captures: Dict[str, str] = Field(default={}, description="Screen capture file paths")
    supported_formats: Dict[str, List[str]] = Field(default={
        "excel_formats": [".xlsx", ".xlsm", ".xls", ".xlsb"],
        "image_formats": [".png", ".jpg", ".jpeg", ".bmp"],
        "csv_formats": [".csv"]
    }, description="Supported file formats")
    max_file_size: int = Field(default=50, ge=1, le=500, description="Maximum file size in MB")
    temp_dir: str = Field(default=tempfile.gettempdir(), description="Temporary directory for operations")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [SheetInfo, CellStyle, ExcelScenario]

# Section 2: Class
class ExcelServer:
    def __init__(self):
        """Initialize Excel server with empty state."""
        self.file_path: str = ""
        self.sheets: Dict[str, Dict[str, Any]] = {}
        self.tables: Dict[str, str] = {}
        self.formats: Dict[str, Any] = {}
        self.screen_captures: Dict[str, str] = {}
        self.supported_formats: Dict[str, List[str]] = {}
        self.max_file_size: int = 50
        self.temp_dir: str = tempfile.gettempdir()
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server instance."""
        model = ExcelScenario(**scenario)
        self.file_path = model.file_path
        self.sheets = model.sheets
        self.tables = model.tables
        self.formats = model.formats
        self.screen_captures = model.screen_captures
        self.supported_formats = model.supported_formats
        self.max_file_size = model.max_file_size
        self.temp_dir = model.temp_dir
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "file_path": self.file_path,
            "sheets": self.sheets,
            "tables": self.tables,
            "formats": self.formats,
            "screen_captures": self.screen_captures,
            "supported_formats": self.supported_formats,
            "max_file_size": self.max_file_size,
            "temp_dir": self.temp_dir,
            "current_time": self.current_time
        }

    def excel_describe_sheets(self, file_absolute_path: str) -> dict:
        """List all sheet information of a specified Excel file."""
        # Mock sheet data based on stored state
        sheets = []
        for sheet_name, sheet_data in self.sheets.items():
            sheets.append({
                "name": sheet_name,
                "index": len(sheets),
                "visibility": sheet_data.get("visibility", "visible")
            })
        return {"sheets": sheets}

    def excel_read_sheet(self, file_absolute_path: str, sheet_name: str, cell_range: Optional[str] = None, show_formula: bool = False, show_style: bool = False) -> dict:
        """Read cell values from a specified Excel sheet."""
        if sheet_name not in self.sheets:
            return {"values": [], "cellRange": cell_range or "A1:Z100", "sheetName": sheet_name}

        sheet_data = self.sheets[sheet_name]
        values = sheet_data.get("values", [])

        # Filter by range if specified
        if cell_range:
            # Simple range parsing (mock implementation)
            pass

        return {
            "values": values,
            "cellRange": cell_range or "A1:Z100",
            "sheetName": sheet_name
        }

    def excel_screen_capture(self, file_absolute_path: str, sheet_name: str, cell_range: Optional[str] = None) -> dict:
        """Capture a screenshot image of a specified Excel sheet or cell range."""
        # Platform check is now only in the wrapper function, not duplicated here
        capture_key = f"{sheet_name}_{cell_range or 'full'}"
        timestamp_str = self.current_time.replace(":", "").replace("-", "")[:15]
        image_path = f"{self.temp_dir}/excel_capture_{timestamp_str}.png"

        # Mock screen capture
        self.screen_captures[capture_key] = image_path

        return {
            "imagePath": image_path,
            "sheetName": sheet_name,
            "cellRange": cell_range or "full_sheet"
        }

    def excel_write_to_sheet(self, file_absolute_path: str, sheet_name: str, new_sheet: bool, cell_range: str, values: List[List[Any]]) -> dict:
        """Write values to a specified range in an Excel sheet."""
        if new_sheet or sheet_name not in self.sheets:
            self.sheets[sheet_name] = {
                "values": values,
                "visibility": "visible",
                "created": self.current_time
            }
        else:
            # Update existing sheet
            existing_values = self.sheets[sheet_name].get("values", [])
            # Merge values (mock implementation)
            self.sheets[sheet_name]["values"] = values

        return {
            "status": "success",
            "fileAbsolutePath": file_absolute_path,
            "sheetName": sheet_name
        }

    def excel_create_table(self, file_absolute_path: str, sheet_name: str, cell_range: str, table_name: str) -> dict:
        """Create a formatted Excel table from a specified cell range."""
        self.tables[table_name] = f"{sheet_name}!{cell_range}"

        return {
            "tableName": table_name,
            "cellRange": cell_range,
            "sheetName": sheet_name
        }

    def excel_copy_sheet(self, file_absolute_path: str, src_sheet_name: str, dst_sheet_name: str) -> dict:
        """Copy an existing sheet to create a new sheet within the same Excel workbook."""
        if src_sheet_name not in self.sheets:
            raise ValueError(f"Source sheet '{src_sheet_name}' not found")

        # Copy sheet data
        self.sheets[dst_sheet_name] = self.sheets[src_sheet_name].copy()

        return {
            "srcSheetName": src_sheet_name,
            "dstSheetName": dst_sheet_name,
            "fileAbsolutePath": file_absolute_path
        }

    def excel_format_range(self, file_absolute_path: str, sheet_name: str, cell_range: str, styles: List[List[Dict[str, Any]]]) -> dict:
        """Apply formatting styles to a specified range of cells in an Excel sheet."""
        format_key = f"{sheet_name}_{cell_range}"
        self.formats[format_key] = {
            "styles": styles,
            "applied_at": self.current_time
        }

        return {
            "status": "success",
            "formattedRange": cell_range,
            "sheetName": sheet_name
        }

# Section 3: MCP Tools
mcp = FastMCP(name="ExcelServer")
server = ExcelServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Excel server.

    Args:
        scenario (dict): Scenario dictionary matching ExcelScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Excel server state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def excel_describe_sheets(file_absolute_path: str) -> dict:
    """
    List all sheet information of a specified Excel file.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.

    Returns:
        sheets (list): List of all sheets contained in the Excel file.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not file_absolute_path.startswith("/") and ":" not in file_absolute_path[:2]:
            raise ValueError("File path must be absolute")
        return server.excel_describe_sheets(file_absolute_path)
    except Exception as e:
        raise e

@mcp.tool()
def excel_read_sheet(file_absolute_path: str, sheet_name: str, cell_range: Optional[str] = None, show_formula: bool = False, show_style: bool = False) -> dict:
    """
    Read cell values from a specified Excel sheet.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        sheet_name (str): The name of the sheet within the Excel file to operate on.
        cell_range (str) [Optional]: The range of cells to read in Excel A1 notation.
        show_formula (bool) [Optional]: When true, returns cell formulas instead of calculated values.
        show_style (bool) [Optional]: When true, includes style information for each cell.

    Returns:
        values (list): 2D array containing the cell values read from the specified range.
        cell_range (str): The actual cell range that was read.
        sheet_name (str): The name of the sheet from which data was read.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("Sheet name must be a non-empty string")
        return server.excel_read_sheet(file_absolute_path, sheet_name, cell_range, show_formula, show_style)
    except Exception as e:
        raise e

@mcp.tool()
def excel_screen_capture(file_absolute_path: str, sheet_name: str, cell_range: Optional[str] = None) -> dict:
    """
    Capture a screenshot image of a specified Excel sheet or cell range.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        sheet_name (str): The name of the sheet within the Excel file to operate on.
        cell_range (str) [Optional]: The range of cells to capture in Excel A1 notation.

    Returns:
        image_path (str): The absolute file path where the captured screenshot was saved.
        sheet_name (str): The name of the sheet that was captured.
        cell_range (str): The cell range that was captured.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("Sheet name must be a non-empty string")
        # Platform validation is done only here in the wrapper, not duplicated in the class method
        if platform.system() != "Windows":
            raise ValueError("Screen capture is only available on Windows")
        return server.excel_screen_capture(file_absolute_path, sheet_name, cell_range)
    except Exception as e:
        raise e

@mcp.tool()
def excel_write_to_sheet(file_absolute_path: str, sheet_name: str, new_sheet: bool, cell_range: str, values: List[List[Any]]) -> dict:
    """
    Write values to a specified range in an Excel sheet.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        sheet_name (str): The name of the sheet within the Excel file to operate on.
        new_sheet (bool): When true, creates a new sheet with the specified name.
        cell_range (str): The target range of cells to write to in Excel A1 notation.
        values (list): 2D array of values to write to the cells.

    Returns:
        status (str): The result status of the write operation.
        file_absolute_path (str): The absolute file path of the Excel file that was modified.
        sheet_name (str): The name of the sheet where data was written.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("Sheet name must be a non-empty string")
        if not cell_range or not isinstance(cell_range, str):
            raise ValueError("Cell range must be a non-empty string")
        if not isinstance(values, list):
            raise ValueError("Values must be a 2D array")
        return server.excel_write_to_sheet(file_absolute_path, sheet_name, new_sheet, cell_range, values)
    except Exception as e:
        raise e

@mcp.tool()
def excel_create_table(file_absolute_path: str, sheet_name: str, cell_range: str, table_name: str) -> dict:
    """
    Create a formatted Excel table from a specified cell range within a sheet.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        sheet_name (str): The name of the sheet within the Excel file to operate on.
        cell_range (str): The range of cells to convert into a table in Excel A1 notation.
        table_name (str): The unique name to assign to the newly created table.

    Returns:
        table_name (str): The name of the table that was created.
        cell_range (str): The cell range that the table occupies.
        sheet_name (str): The name of the sheet containing the created table.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("Sheet name must be a non-empty string")
        if not cell_range or not isinstance(cell_range, str):
            raise ValueError("Cell range must be a non-empty string")
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        return server.excel_create_table(file_absolute_path, sheet_name, cell_range, table_name)
    except Exception as e:
        raise e

@mcp.tool()
def excel_copy_sheet(file_absolute_path: str, src_sheet_name: str, dst_sheet_name: str) -> dict:
    """
    Copy an existing sheet to create a new sheet within the same Excel workbook.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        src_sheet_name (str): The name of the source sheet to copy from.
        dst_sheet_name (str): The name for the new destination sheet to be created.

    Returns:
        src_sheet_name (str): The name of the source sheet that was copied.
        dst_sheet_name (str): The name of the newly created destination sheet.
        file_absolute_path (str): The absolute file path of the Excel file containing the copied sheet.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not src_sheet_name or not isinstance(src_sheet_name, str):
            raise ValueError("Source sheet name must be a non-empty string")
        if not dst_sheet_name or not isinstance(dst_sheet_name, str):
            raise ValueError("Destination sheet name must be a non-empty string")
        return server.excel_copy_sheet(file_absolute_path, src_sheet_name, dst_sheet_name)
    except Exception as e:
        raise e

@mcp.tool()
def excel_format_range(file_absolute_path: str, sheet_name: str, cell_range: str, styles: List[List[Dict[str, Any]]]) -> dict:
    """
    Apply formatting styles to a specified range of cells in an Excel sheet.

    Args:
        file_absolute_path (str): The absolute file system path to the Excel file to be processed.
        sheet_name (str): The name of the sheet within the Excel file to operate on.
        cell_range (str): The range of cells to format in Excel A1 notation.
        styles (list): 2D array of style objects corresponding to each cell in the range.

    Returns:
        status (str): The result status of the formatting operation.
        formatted_range (str): The cell range that was formatted.
        sheet_name (str): The name of the sheet where formatting was applied.
    """
    try:
        if not file_absolute_path or not isinstance(file_absolute_path, str):
            raise ValueError("File path must be a non-empty string")
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("Sheet name must be a non-empty string")
        if not cell_range or not isinstance(cell_range, str):
            raise ValueError("Cell range must be a non-empty string")
        if not isinstance(styles, list):
            raise ValueError("Styles must be a 2D array")
        return server.excel_format_range(file_absolute_path, sheet_name, cell_range, styles)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
