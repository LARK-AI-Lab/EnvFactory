# Dictionary Research Notes

## Data Source
- Official Docs: https://dictionaryapi.dev/
- API Reference: https://dictionaryapi.dev/
- Base URL: https://api.dictionaryapi.dev/api/v2

## API Overview
- **Purpose**: Free dictionary API providing word definitions, phonetics, synonyms, antonyms, and usage examples
- **Category**: Language Learning / Reference
- **Target users**: Language learners, developers building vocabulary apps, writers, students

## Authentication
- **Type**: None required
- **Rate limits**: No explicit limits, but be respectful
- **Cost**: 100% free, open source

## Core Endpoints & Design

### 1. Get Word Definition
- **Method & path**: `GET /entries/{language}/{word}`
- **Purpose**: Retrieve complete dictionary entry for a word
- **Request params**:
  - `language` (str): Language code (en, es, fr, de, etc.)
  - `word` (str): The word to look up
- **Response structure**: Array of entries containing:
  - `word` (str): The word
  - `phonetic` (str): IPA pronunciation
  - `phonetics` (list): Audio links and text pronunciations
  - `origin` (str): Etymology
  - `meanings` (list): Definitions by part of speech
    - `partOfSpeech` (str): Noun, verb, etc.
    - `definitions` (list): Actual definitions
      - `definition` (str): The definition text
      - `example` (str): Usage example
      - `synonyms` (list): Synonymous words
      - `antonyms` (list): Antonymous words

### 2. Get Word Definition (Simplified)
- **Method & path**: `GET /api/v2/entries/en/{word}`
- **Purpose**: Quick lookup for English words
- **Same structure as above**

## Data Models
- **Entry**: word, phonetic, phonetics[], origin, meanings[]
- **Meaning**: partOfSpeech, definitions[]
- **Definition**: definition, example, synonyms[], antonyms[]
- **Phonetic**: text, audio (optional)

## Use Cases
- Vocabulary building applications
- Language learning tools
- Writing assistance software
- Thesaurus functionality
- Pronunciation guides
- Etymology exploration

## Response Example
```json
[
  {
    "word": "hello",
    "phonetic": "həˈləʊ",
    "phonetics": [
      {
        "text": "həˈləʊ",
        "audio": "//ssl.gstatic.com/dictionary/static/sounds/20200429/hello--_gb_1.mp3"
      }
    ],
    "origin": "early 19th century: variant of earlier hollo",
    "meanings": [
      {
        "partOfSpeech": "exclamation",
        "definitions": [
          {
            "definition": "used as a greeting",
            "example": "hello there, Katie!",
            "synonyms": [],
            "antonyms": []
          }
        ]
      }
    ]
  }
]
```

## Supported Languages
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- And more...
