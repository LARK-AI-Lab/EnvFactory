# Server: Excel

def excel_describe_sheets(fileAbsolutePath: str) -> dict:
    """
    List all sheet information of specified Excel file.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        
    Returns:
        dict: {
            "sheets": list[dict] - Each sheet contains {
                "name": str,
                "index": int,
                "visibility": str
            }
        }
    """
    pass

def excel_read_sheet(
    fileAbsolutePath: str, 
    sheetName: str, 
    cellRange: str = None, 
    showFormula: bool = False, 
    showStyle: bool = False
) -> dict:
    """
    Read values from Excel sheet.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        sheetName (str): Sheet name in the Excel file
        cellRange (str): [Optional] Range of cells to read (e.g., "A1:C10")
        showFormula (bool): [Optional] Show formula instead of value
        showStyle (bool): [Optional] Show style information for cells
        
    Returns:
        dict: {
            "values": list[list],
            "cellRange": str,
            "sheetName": str
        }
    """
    pass

def excel_screen_capture(
    fileAbsolutePath: str, 
    sheetName: str, 
    cellRange: str = None
) -> dict:
    """
    Take a screenshot of the Excel sheet with pagination. [Windows only]
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        sheetName (str): Sheet name in the Excel file
        cellRange (str): [Optional] Range of cells to capture (e.g., "A1:C10")
        
    Returns:
        dict: {
            "imagePath": str,
            "sheetName": str,
            "cellRange": str
        }
    """
    pass

def excel_write_to_sheet(
    fileAbsolutePath: str, 
    sheetName: str, 
    newSheet: bool, 
    cellRange: str, 
    values: list
) -> dict:
    """
    Write values to the Excel sheet.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        sheetName (str): Sheet name in the Excel file
        newSheet (bool): Create a new sheet if true, otherwise write to the existing sheet
        cellRange (str): Range of cells to write (e.g., "A1:C10")
        values (list): 2D array of values to write. Formulas should start with "="
        
    Returns:
        dict: {
            "status": str,
            "fileAbsolutePath": str,
            "sheetName": str
        }
    """
    pass

def excel_create_table(
    fileAbsolutePath: str, 
    sheetName: str, 
    cellRange: str, 
    tableName: str
) -> dict:
    """
    Create a table in the Excel sheet.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        sheetName (str): Sheet name where the table is created
        cellRange (str): Range to be a table (e.g., "A1:C10")
        tableName (str): Table name to be created
        
    Returns:
        dict: {
            "tableName": str,
            "cellRange": str,
            "sheetName": str
        }
    """
    pass

def excel_copy_sheet(
    fileAbsolutePath: str, 
    srcSheetName: str, 
    dstSheetName: str
) -> dict:
    """
    Copy existing sheet to a new sheet.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        srcSheetName (str): Source sheet name in the Excel file
        dstSheetName (str): Target sheet name to be copied to
        
    Returns:
        dict: {
            "srcSheetName": str,
            "dstSheetName": str,
            "fileAbsolutePath": str
        }
    """
    pass

def excel_format_range(
    fileAbsolutePath: str, 
    sheetName: str, 
    cellRange: str, 
    styles: list
) -> dict:
    """
    Format cells in the Excel sheet with style information.
    
    Args:
        fileAbsolutePath (str): Absolute path to the Excel file
        sheetName (str): Sheet name in the Excel file
        cellRange (str): Range of cells in the Excel sheet (e.g., "A1:C3")
        styles (list): 2D array of style objects (border, font, fill, numFmt, decimalPlaces)
        
    Returns:
        dict: {
            "status": str,
            "formattedRange": str,
            "sheetName": str
        }
    """
    pass