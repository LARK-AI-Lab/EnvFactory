# Data Source: https://developers.convertio.co/
# Server: Convertio
# Category: document


def convert_file(input_file: str, output_format: str, input_format: str = None) -> dict:
    """
    Convert a file from one format to another (300+ formats supported).

    Args:
        input_file (str): File URL, base64 content, or file path
        output_format (str): Target format extension (e.g., "pdf", "docx", "png")
        input_format (str): [Optional] Source format if not auto-detectable

    Returns:
        dict: {
            "conversion_id": str,  # ID to track/check conversion status
            "status": str,  # "ok", "wait", "error"
            "output_url": str,  # Download URL when complete
            "minutes_used": float  # API minutes consumed
        }
    """
    pass


def convert_multiple_files(files: list, output_format: str) -> dict:
    """
    Convert multiple files to the same output format in one request.

    Args:
        files (list): List of input files (URLs, base64, or file paths)
        output_format (str): Target format for all files

    Returns:
        dict: {
            "conversion_ids": list,  # List of conversion IDs
            "status": str,
            "total_minutes": float
        }
    """
    pass


def check_conversion_status(conversion_id: str) -> dict:
    """
    Check the status of an ongoing or completed file conversion.

    Args:
        conversion_id (str): The conversion ID returned by convert_file

    Returns:
        dict: {
            "status": str,  # "ok", "wait", "error", "convert"
            "step": str,  # "finish", "load", "convert"
            "progress": int,  # Percentage complete
            "output_url": str,  # Available when status is "ok"
            "minutes_used": float,
            "error_message": str  # If status is "error"
        }
    """
    pass


def convert_document_to_pdf(document_file: str, document_type: str = "auto") -> dict:
    """
    Convert office documents (Word, Excel, PowerPoint) to PDF.

    Args:
        document_file (str): Document file to convert
        document_type (str): [Optional] "word", "excel", "powerpoint", or "auto"

    Returns:
        dict: {
            "pdf_url": str,
            "original_format": str,
            "page_count": int,
            "file_size": int
        }
    """
    pass


def convert_media_file(media_file: str, output_format: str, 
                       quality_options: dict = None) -> dict:
    """
    Convert audio/video files between formats with optional quality settings.

    Args:
        media_file (str): Media file to convert
        output_format (str): Target format (mp3, mp4, avi, etc.)
        quality_options (dict): [Optional] Quality settings like:
            - bitrate (str): e.g., "128k"
            - resolution (str): e.g., "720p"
            - codec (str): e.g., "h264"

    Returns:
        dict: {
            "output_url": str,
            "duration": int,  # Duration in seconds
            "file_size": int,
            "format": str
        }
    """
    pass
