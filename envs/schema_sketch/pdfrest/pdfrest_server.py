# Data Source: https://pdfrest.com/
# Server: PDFRest
# Category: document


def compress_pdf(pdf_file: str, compression_level: str = "medium") -> dict:
    """
    Compress a PDF file to reduce its file size.

    Args:
        pdf_file (str): PDF file to compress (URL, base64, or file path)
        compression_level (str): [Optional] "low", "medium", "high", or "lossless"

    Returns:
        dict: {
            "output_url": str,  # URL to download compressed PDF
            "original_size": int,  # Size in bytes
            "compressed_size": int,
            "compression_ratio": float  # Percentage reduced
        }
    """
    pass


def convert_to_pdf(input_file: str, file_type: str) -> dict:
    """
    Convert various file types (Word, Excel, PowerPoint, images) to PDF.

    Args:
        input_file (str): Input file to convert
        file_type (str): Type of input file - "word", "excel", "powerpoint", "image"

    Returns:
        dict: {
            "output_url": str,
            "page_count": int,
            "file_size": int
        }
    """
    pass


def split_pdf(pdf_file: str, page_ranges: list) -> dict:
    """
    Split a PDF into multiple files based on page ranges.

    Args:
        pdf_file (str): PDF file to split
        page_ranges (list): List of page ranges, e.g., ["1-3", "4-6", "7-10"]

    Returns:
        dict: {
            "output_files": list,  # List of download URLs
            "split_count": int,
            "total_pages": int
        }
    """
    pass


def watermark_pdf(pdf_file: str, watermark_text: str = None, watermark_image: str = None, 
                  pages: str = "all", opacity: float = 0.5) -> dict:
    """
    Add text or image watermark to PDF pages.

    Args:
        pdf_file (str): PDF file to watermark
        watermark_text (str): [Optional] Text to use as watermark
        watermark_image (str): [Optional] Image file to use as watermark
        pages (str): [Optional] Page range or "all", defaults to "all"
        opacity (float): [Optional] Watermark opacity (0.0-1.0), defaults to 0.5

    Returns:
        dict: {
            "output_url": str,
            "watermark_type": str,  # "text" or "image"
            "pages_affected": int
        }
    """
    pass


def pdf_to_images(pdf_file: str, image_format: str = "png", dpi: int = 150, 
                  page_range: str = "all") -> dict:
    """
    Convert PDF pages to image files.

    Args:
        pdf_file (str): PDF file to convert
        image_format (str): [Optional] "png", "jpeg", or "tiff", defaults to "png"
        dpi (int): [Optional] Resolution in DPI, defaults to 150
        page_range (str): [Optional] Page range or "all", defaults to "all"

    Returns:
        dict: {
            "image_urls": list,  # List of image download URLs
            "total_images": int,
            "format": str,
            "dpi": int
        }
    """
    pass
