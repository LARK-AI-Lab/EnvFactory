# Data Source: https://docparser.com/
# Server: Docparser
# Category: document


def upload_document(document_file: str, parser_id: str, remote_id: str = None) -> dict:
    """
    Upload a document to Docparser for parsing.

    Args:
        document_file (str): Document file URL, path, or base64
        parser_id (str): ID of the parser to use for extraction
        remote_id (str): [Optional] Custom ID for tracking the document

    Returns:
        dict: {
            "document_id": str,
            "parser_id": str,
            "status": str,  # "success", "processing"
            "file_name": str,
            "page_count": int,
            "file_size": int
        }
    """
    pass


def fetch_parsed_data(document_id: str, format: str = "json") -> dict:
    """
    Retrieve the extracted data from a parsed document.

    Args:
        document_id (str): The document ID from upload_document
        format (str): [Optional] "json", "csv", "xml", or "excel"

    Returns:
        dict: {
            "document_id": str,
            "parsed_data": dict,  # Extracted fields based on parser rules
            "extraction_confidence": float,
            "parsed_at": str  # ISO timestamp
        }
    """
    pass


def parse_invoice(invoice_file: str) -> dict:
    """
    Extract structured data from an invoice document.

    Args:
        invoice_file (str): Invoice PDF or image file

    Returns:
        dict: {
            "invoice_number": str,
            "invoice_date": str,
            "due_date": str,
            "vendor_name": str,
            "vendor_address": str,
            "customer_name": str,
            "total_amount": str,
            "tax_amount": str,
            "currency": str,
            "line_items": list,  # List of items with description, qty, price
            "raw_text": str
        }
    """
    pass


def parse_bank_statement(statement_file: str) -> dict:
    """
    Extract transaction data from bank or credit card statements.

    Args:
        statement_file (str): Statement PDF file

    Returns:
        dict: {
            "account_number": str,
            "statement_period": str,
            "opening_balance": str,
            "closing_balance": str,
            "transactions": list,  # List of transaction objects
            "total_credits": str,
            "total_debits": str
        }
    """
    pass


def parse_purchase_order(po_file: str) -> dict:
    """
    Extract data from purchase order documents.

    Args:
        po_file (str): Purchase order PDF or image

    Returns:
        dict: {
            "po_number": str,
            "po_date": str,
            "vendor": dict,  # vendor name, address, contact
            "buyer": dict,  # buyer info
            "line_items": list,
            "subtotal": str,
            "tax": str,
            "total": str,
            "delivery_date": str
        }
    """
    pass
