# Data Source: https://ocr.space/ocrapi
# Server: OCRSpace
# Category: document


def parse_image(image_source: str, language: str = "eng", detect_orientation: bool = True) -> dict:
    """
    Extract text from an image using OCR.

    Args:
        image_source (str): Image URL, file path, or base64 encoded image
        language (str): [Optional] 3-letter language code, defaults to "eng"
        detect_orientation (bool): [Optional] Auto-rotate image if needed, defaults to True

    Returns:
        dict: {
            "parsed_text": str,  # Extracted text content
            "confidence": float,  # OCR confidence score (0-100)
            "text_overlay": list,  # Word-level position data
            "processing_time_ms": int
        }
    """
    pass


def parse_pdf(pdf_url: str, language: str = "eng", ocr_engine: int = 1) -> dict:
    """
    Extract text from a PDF document using OCR.

    Args:
        pdf_url (str): URL of the PDF file to process
        language (str): [Optional] 3-letter language code, defaults to "eng"
        ocr_engine (int): [Optional] OCR engine: 1 (fast), 2 (accurate), or 3 (markdown/structured)

    Returns:
        dict: {
            "parsed_results": list,  # Per-page results
            "total_pages": int,
            "ocr_exit_code": int,  # 1=success, 2=partial, 3=failed
            "processing_time_ms": int
        }
    """
    pass


def create_searchable_pdf(pdf_url: str, language: str = "eng", 
                          hide_text_layer: bool = False) -> dict:
    """
    Convert a scanned PDF to a searchable PDF with embedded text layer.

    Args:
        pdf_url (str): URL of the scanned PDF
        language (str): [Optional] Document language code, defaults to "eng"
        hide_text_layer (bool): [Optional] Make text layer invisible, defaults to False

    Returns:
        dict: {
            "searchable_pdf_url": str,  # Download URL (valid for 1 hour)
            "page_count": int,
            "text_content": str  # Full extracted text
        }
    """
    pass


def parse_receipt(receipt_image: str, language: str = "eng") -> dict:
    """
    Extract structured data from receipt images with table recognition.

    Args:
        receipt_image (str): Receipt image URL, file, or base64
        language (str): [Optional] Language code, defaults to "eng"

    Returns:
        dict: {
            "merchant_name": str,
            "date": str,
            "total_amount": str,
            "items": list,  # List of line items
            "tax_amount": str,
            "raw_text": str
        }
    """
    pass


def parse_table(table_image: str, language: str = "eng", ocr_engine: int = 3) -> dict:
    """
    Extract table data from images, preserving row/column structure.

    Args:
        table_image (str): Image containing table to extract
        language (str): [Optional] Language code, defaults to "eng"
        ocr_engine (int): [Optional] Engine 3 recommended for tables

    Returns:
        dict: {
            "table_data": list,  # 2D array of table cells
            "row_count": int,
            "column_count": int,
            "markdown_table": str  # Markdown formatted table
        }
    """
    pass
