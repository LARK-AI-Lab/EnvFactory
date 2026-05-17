# Data Source: https://github.com/felores/airtable-mcp#readme
# Server: Airtable
# Category: Productivity Database


def list_bases() -> dict:
    """
    List Airtable bases available to the current workspace.

    Returns:
        dict: {
            "bases": list[{
                "id": str,
                "name": str,
                "permissionLevel": str
            }]
        }
    """
    pass


def list_tables(base_id: str) -> dict:
    """
    List tables and field schemas for an Airtable base.

    Args:
        base_id (str): Unique Airtable base identifier

    Returns:
        dict: {
            "base_id": str,
            "tables": list[{
                "id": str,
                "name": str,
                "description": str,
                "fields": list[dict],
                "views": list[dict]
            }]
        }
    """
    pass


def list_records(base_id: str, table_id: str, view: str = None,
                 filter_by_formula: str = None, max_records: int = 100,
                 page_size: int = 100, offset: str = None) -> dict:
    """
    Retrieve records from an Airtable table with optional view, filter, and pagination.

    Args:
        base_id (str): Unique Airtable base identifier
        table_id (str): Table ID or table name
        view (str): [Optional] View name or view ID used to order/filter records
        filter_by_formula (str): [Optional] Airtable formula expression used to filter records
        max_records (int): [Optional] Maximum records to return
        page_size (int): [Optional] Page size used for pagination
        offset (str): [Optional] Pagination cursor from a previous response

    Returns:
        dict: {
            "records": list[{
                "id": str,
                "createdTime": str,
                "fields": dict
            }],
            "offset": str
        }
    """
    pass


def create_record(base_id: str, table_id: str, fields: dict) -> dict:
    """
    Create a new record in an Airtable table.

    Args:
        base_id (str): Unique Airtable base identifier
        table_id (str): Table ID or table name
        fields (dict): Field values keyed by Airtable field name or field ID

    Returns:
        dict: {
            "id": str,
            "createdTime": str,
            "fields": dict
        }
    """
    pass


def update_record(base_id: str, table_id: str, record_id: str,
                  fields: dict) -> dict:
    """
    Update fields on an existing Airtable record.

    Args:
        base_id (str): Unique Airtable base identifier
        table_id (str): Table ID or table name
        record_id (str): Record identifier
        fields (dict): Field values to update

    Returns:
        dict: {
            "id": str,
            "createdTime": str,
            "fields": dict
        }
    """
    pass
