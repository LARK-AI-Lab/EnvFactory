# Data Source: https://dictionaryapi.dev/
# Server: Dictionary
# Category: Language Learning


def get_definition(word: str, language: str = "en") -> list:
    """
    Retrieve comprehensive dictionary definitions for a word.
    
    Args:
        word (str): The word to look up
        language (str): [Optional] Language code (default: "en" for English)
        
    Returns:
        list: Array of dictionary entries, each containing:
        {
            "word": str,
            "phonetic": str,
            "phonetics": list[{
                "text": str,
                "audio": str
            }],
            "origin": str,
            "meanings": list[{
                "partOfSpeech": str,
                "definitions": list[{
                    "definition": str,
                    "example": str,
                    "synonyms": list[str],
                    "antonyms": list[str]
                }]
            }]
        }
    """
    pass


def get_synonyms(word: str, language: str = "en") -> list:
    """
    Get synonyms for a given word across all its meanings.
    
    Args:
        word (str): The word to find synonyms for
        language (str): [Optional] Language code (default: "en")
        
    Returns:
        list: List of synonym strings grouped by meaning/part of speech
    """
    pass


def get_antonyms(word: str, language: str = "en") -> list:
    """
    Get antonyms (opposite words) for a given word.
    
    Args:
        word (str): The word to find antonyms for
        language (str): [Optional] Language code (default: "en")
        
    Returns:
        list: List of antonym strings grouped by meaning/part of speech
    """
    pass


def get_pronunciation(word: str, language: str = "en") -> dict:
    """
    Get phonetic pronunciation and audio links for a word.
    
    Args:
        word (str): The word to get pronunciation for
        language (str): [Optional] Language code (default: "en")
        
    Returns:
        dict: {
            "word": str,
            "phonetic": str,
            "audio_url": str,
            "alternative_pronunciations": list[str]
        }
    """
    pass


def get_etymology(word: str, language: str = "en") -> str:
    """
    Retrieve the etymology (word origin and history) of a word.
    
    Args:
        word (str): The word to get etymology for
        language (str): [Optional] Language code (default: "en")
        
    Returns:
        str: Etymology/origin description of the word
    """
    pass
