# Data Source: https://developers.deepl.com/
# Server: Translator
# Category: Language Translation


def translate_text(text: str, target_language: str, source_language: str = None,
                  formality: str = "default", context: str = None) -> dict:
    """
    Translate text from source language to target language.
    
    Args:
        text (str): Text to translate (max 150,000 characters per request)
        target_language (str): Target language code (e.g., "DE", "FR", "ZH", "JA")
        source_language (str): [Optional] Source language code (auto-detected if not provided)
        formality (str): [Optional] Formality level - "default", "more", "less", 
                        "prefer_more", "prefer_less"
        context (str): [Optional] Additional context to improve translation quality
        
    Returns:
        dict: {
            "translated_text": str,
            "detected_source_language": str,
            "source_language": str,
            "target_language": str
        }
    """
    pass


def translate_multiple(texts: list, target_language: str, source_language: str = None,
                      formality: str = "default") -> list:
    """
    Translate multiple text strings in a single request.
    
    Args:
        texts (list): Array of text strings to translate (max 50 texts)
        target_language (str): Target language code
        source_language (str): [Optional] Source language code
        formality (str): [Optional] Formality preference
        
    Returns:
        list: Array of translation results, each containing:
        {
            "original_text": str,
            "translated_text": str,
            "detected_source_language": str
        }
    """
    pass


def get_supported_languages(language_type: str = "target") -> list:
    """
    Get list of supported languages for translation.
    
    Args:
        language_type (str): [Optional] "source" or "target" (default: "target")
        
    Returns:
        list: Array of language objects:
        {
            "language": str,
            "name": str,
            "supports_formality": bool
        }
    """
    pass


def translate_document(file_path: str, target_language: str, 
                      source_language: str = None, formality: str = "default") -> dict:
    """
    Translate an entire document file.
    
    Args:
        file_path (str): Path to document file (PDF, DOCX, PPTX, TXT, HTML)
        target_language (str): Target language code
        source_language (str): [Optional] Source language code
        formality (str): [Optional] Formality preference
        
    Returns:
        dict: {
            "document_id": str,
            "document_key": str,
            "status": str,
            "message": str
        }
    """
    pass


def check_document_status(document_id: str, document_key: str) -> dict:
    """
    Check the status of a document translation.
    
    Args:
        document_id (str): Document ID from upload
        document_key (str): Document key from upload
        
    Returns:
        dict: {
            "document_id": str,
            "status": str,
            "seconds_remaining": int,
            "billed_characters": int,
            "error_message": str
        }
    """
    pass
