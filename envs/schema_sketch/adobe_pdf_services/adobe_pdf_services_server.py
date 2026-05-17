# Data Source: https://developer.adobe.com/document-services/apis/pdf-services/
# Server: AdobePDFServices
# Category: document


def create_pdf_from_html(html_content: str, output_filename: str = None, page_size: str = "A4") -> dict:
    """
    Create a PDF document from HTML content.

    Args:
        html_content (str): The HTML content to convert to PDF
        output_filename (str): [Optional] Name for the output PDF file
        page_size (str): [Optional] Page size (A4, Letter, Legal), defaults to A4

    Returns:
        dict: {
            "pdf_url": str,  # URL to download the generated PDF
            "page_count": int,
            "file_size": int  # Size in bytes
        }
    """
    pass


def export_pdf_to_format(pdf_url: str, target_format: str, output_filename: str = None) -> dict:
    """
    Export a PDF to another format (Word, Excel, PPTX, images).

    Args:
        pdf_url (str): URL of the PDF file to export
        target_format (str): Target format - "docx", "xlsx", "pptx", "jpeg", "png"
        output_filename (str): [Optional] Name for the output file

    Returns:
        dict: {
            "export_url": str,  # URL to download the exported file
            "format": str,
            "page_count": int
        }
    """
    pass


def ocr_pdf(pdf_url: str, language: str = "en-US", output_type: str = "searchable_pdf") -> dict:
    """
    Perform OCR on a PDF to make it searchable or extract text.

    Args:
        pdf_url (str): URL of the PDF file to process
        language (str): [Optional] Document language, defaults to en-US
        output_type (str): [Optional] "searchable_pdf" or "text_extraction"

    Returns:
        dict: {
            "output_url": str,  # URL to download processed PDF or text file
            "extracted_text": str,  # Only if output_type is "text_extraction"
            "confidence_score": float  # OCR confidence (0-100)
        }
    """
    pass


def combine_pdfs(pdf_urls: list, output_filename: str = None) -> dict:
    """
    Combine multiple PDFs into a single document.

    Args:
        pdf_urls (list): List of PDF URLs to combine
        output_filename (str): [Optional] Name for the output PDF

    Returns:
        dict: {
            "combined_pdf_url": str,
            "total_pages": int,
            "source_count": int
        }
    """
    pass


def protect_pdf(pdf_url: str, password: str, permissions: dict = None) -> dict:
    """
    Add password protection and permissions to a PDF.

    Args:
        pdf_url (str): URL of the PDF file to protect
        password (str): Password to protect the PDF
        permissions (dict): [Optional] Permissions dict with keys:
            - printing (bool): Allow printing
            - copying (bool): Allow copying content
            - editing (bool): Allow editing
            - commenting (bool): Allow commenting

    Returns:
        dict: {
            "protected_pdf_url": str,
            "encryption_level": str,
            "permissions_applied": dict
        }
    """
    pass
