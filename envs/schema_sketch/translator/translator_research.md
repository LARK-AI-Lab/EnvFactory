# Translator (DeepL) Research Notes

## Data Source
- Official Docs: https://developers.deepl.com/
- API Reference: https://developers.deepl.com/docs/api-reference/translate
- Base URL: 
  - Free tier: https://api-free.deepl.com/v2
  - Pro: https://api.deepl.com/v2

## API Overview
- **Purpose**: High-quality neural machine translation API supporting text and document translation
- **Category**: Language Translation / Education
- **Target users**: Language learners, content creators, international businesses, educational platforms

## Authentication
- **Type**: API Key (DeepL-Auth-Key header)
- **Free tier**: 500,000 characters/month free
- **Rate limits**: Varies by plan; monitor usage via API
- **How to obtain**: Sign up at DeepL website to get API key

## Core Endpoints & Design

### 1. Translate Text
- **Method & path**: `POST /translate`
- **Purpose**: Translate text from source to target language
- **Request body**:
  - `text` (list[str]): Array of text strings to translate (max 50 texts)
  - `target_lang` (str): Target language code (e.g., "DE", "FR", "ZH")
  - `source_lang` (str): [Optional] Source language (auto-detected if not provided)
  - `context` (str): [Optional] Additional context to improve translation
  - `split_sentences` (str): [Optional] "0" (off), "1" (default), "nonewlines"
  - `preserve_formatting` (bool): [Optional] Keep original formatting
  - `formality` (str): [Optional] "default", "more", "less", "prefer_more", "prefer_less"
  - `glossary_id` (str): [Optional] Use custom glossary
- **Response structure**:
  - `translations` (list): Array of translation results
    - `detected_source_language` (str): Auto-detected source language
    - `text` (str): Translated text

### 2. Get Supported Languages
- **Method & path**: `GET /languages`
- **Purpose**: List all supported source and target languages
- **Query params**:
  - `type` (str): "source" or "target"
- **Response structure**:
  - Array of language objects:
    - `language` (str): Language code
    - `name` (str): Language name
    - `supports_formality` (bool): Whether formality options available

### 3. Translate Document
- **Method & path**: `POST /document`
- **Purpose**: Translate entire documents (PDF, DOCX, PPTX, etc.)
- **Request body**: multipart/form-data
  - `file` (file): Document file to translate
  - `target_lang` (str): Target language
  - `source_lang` (str): [Optional] Source language
  - `formality` (str): [Optional] Formality preference
- **Response structure**:
  - `document_id` (str): ID for checking status
  - `document_key` (str): Key for downloading result

### 4. Check Document Status
- **Method & path**: `POST /document/{document_id}`
- **Purpose**: Check translation progress
- **Request body**:
  - `document_key` (str): Document key from upload
- **Response structure**:
  - `document_id` (str)
  - `status` (str): "queued", "translating", "done", "error"
  - `seconds_remaining` (int): Estimated time remaining
  - `billed_characters` (int): Characters counted for billing

### 5. Download Translated Document
- **Method & path**: `POST /document/{document_id}/result`
- **Purpose**: Download completed translation
- **Request body**:
  - `document_key` (str): Document key

## Data Models
- **Translation**: detected_source_language, text
- **Language**: language, name, supports_formality
- **DocumentStatus**: document_id, status, seconds_remaining, billed_characters

## Supported Languages
- Bulgarian (BG), Chinese (ZH), Czech (CS), Danish (DA)
- Dutch (NL), English (EN), Estonian (ET), Finnish (FI)
- French (FR), German (DE), Greek (EL), Hungarian (HU)
- Indonesian (ID), Italian (IT), Japanese (JA), Korean (KO)
- Latvian (LV), Lithuanian (LT), Norwegian (NB), Polish (PL)
- Portuguese (PT), Romanian (RO), Russian (RU), Slovak (SK)
- Slovenian (SL), Spanish (ES), Swedish (SV), Turkish (TR)
- Ukrainian (UK)

## Use Cases
- Language learning tools
- Content localization
- Real-time translation apps
- Document translation workflows
- Multilingual chatbots
- Educational content adaptation

## Response Example
```json
{
  "translations": [
    {
      "detected_source_language": "EN",
      "text": "Hallo, Welt!"
    }
  ]
}
```
