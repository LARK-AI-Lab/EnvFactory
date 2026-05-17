
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP


# Section 1: Schema

class AirtableBase(BaseModel):
    id: str
    name: str
    permissionLevel: str

class AirtableTable(BaseModel):
    id: str
    name: str
    tableDescription: Optional[str] = None
    fields: List[Any] = []
    views: List[Any] = []

class AirtableRecord(BaseModel):
    id: str
    createdTime: str
    fields: Dict[str, Any] = {}

class AirtableScenario(BaseModel):
    bases: List[AirtableBase] = []
    tables: Dict[str, List[AirtableTable]] = {}
    records: Dict[str, Dict[str, List[AirtableRecord]]] = {}
    record_counter: int = 0
    current_time: str = "2026-04-17T01:43:20"

Scenario_Schema = [AirtableBase, AirtableTable, AirtableRecord, AirtableScenario]


# Section 2: Class

class AirtableMcpServer:
    def __init__(self):
        self.bases: List[AirtableBase] = []
        self.tables: Dict[str, List[AirtableTable]] = {}
        self.records: Dict[str, Dict[str, List[AirtableRecord]]] = {}
        self.record_counter: int = 0
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        # Remap legacy 'description' key to 'tableDescription' in tables
        for base_tables in scenario.get("tables", {}).values():
            for t in base_tables:
                if isinstance(t, dict) and "description" in t and "tableDescription" not in t:
                    t["tableDescription"] = t.pop("description")
        model = AirtableScenario(**scenario)
        self.bases = model.bases
        self.tables = model.tables
        self.records = {
            base_id: {
                table_id: [AirtableRecord(**r) if isinstance(r, dict) else r for r in recs]
                for table_id, recs in table_map.items()
            }
            for base_id, table_map in model.records.items()
        }
        self.record_counter = model.record_counter
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        return {
            "bases": [b.model_dump() for b in self.bases],
            "tables": {
                base_id: [t.model_dump() for t in tables]
                for base_id, tables in self.tables.items()
            },
            "records": {
                base_id: {
                    table_id: [r.model_dump() for r in recs]
                    for table_id, recs in table_map.items()
                }
                for base_id, table_map in self.records.items()
            },
            "record_counter": self.record_counter,
            "current_time": self.current_time,
        }

    def list_bases(self) -> dict:
        return {"bases": [b.model_dump() for b in self.bases]}

    def list_tables(self, base_id: str) -> dict:
        tables = self.tables.get(base_id, [])
        return {"base_id": base_id, "tables": [t.model_dump() for t in tables]}

    def list_records(self, base_id: str, table_id: str, view, filter_by_formula, max_records, page_size, offset) -> dict:
        all_records = self.records.get(base_id, {}).get(table_id, [])
        start = 0
        if offset:
            try:
                start = int(offset)
            except ValueError:
                start = 0
        limit = min(min(max_records or 100, 100), min(page_size or 100, 100))
        page_records = all_records[start:start + limit]
        result = {"records": [r.model_dump() for r in page_records]}
        next_start = start + limit
        if next_start < len(all_records):
            result["offset"] = str(next_start)
        return result

    def create_record(self, base_id: str, table_id: str, fields: dict) -> dict:
        self.record_counter += 1
        record = AirtableRecord(id=f"rec{self.record_counter:010d}", createdTime=self.current_time, fields=fields)
        self.records.setdefault(base_id, {}).setdefault(table_id, []).append(record)
        return record.model_dump()

    def update_record(self, base_id: str, table_id: str, record_id: str, fields: dict) -> dict:
        for record in self.records.get(base_id, {}).get(table_id, []):
            if record.id == record_id:
                record.fields.update(fields)
                return record.model_dump()
        return None


# Section 3: MCP Tools

mcp = FastMCP(name="AirtableMcpServer")
api = AirtableMcpServer()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Airtable MCP server.

    Args:
        scenario (dict): Scenario dictionary matching AirtableScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e


@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Airtable state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def list_bases() -> dict:
    """
    Retrieve all bases accessible to the authenticated Airtable workspace.

    Returns:
        bases (array): List of bases, each with id (str), name (str), and permissionLevel (str).
    """
    try:
        return api.list_bases()
    except Exception as e:
        raise e


@mcp.tool()
def list_tables(base_id: str) -> dict:
    """
    Fetch schema and metadata for every table inside a specified base.

    Args:
        base_id (str): The unique identifier of the Airtable base whose tables are to be listed.

    Returns:
        base_id (str): The unique identifier of the Airtable base whose tables are returned.
        tables (array): Collection of tables with id, name, tableDescription, fields, and views.
    """
    try:
        if not base_id or not isinstance(base_id, str):
            raise ValueError("base_id must be a non-empty string")
        return api.list_tables(base_id)
    except Exception as e:
        raise e


@mcp.tool()
def list_records(
    base_id: str,
    table_id: str,
    view: Optional[str] = None,
    filter_by_formula: Optional[str] = None,
    max_records: Optional[int] = None,
    page_size: Optional[int] = None,
    offset: Optional[str] = None,
) -> dict:
    """
    Query and paginate through records in a table, optionally filtered by a view or formula.

    Args:
        base_id (str): The unique identifier of the Airtable base containing the table.
        table_id (str): The table ID or table name whose records are to be listed.
        view (str): [Optional] View name or ID that pre-orders or pre-filters the records.
        filter_by_formula (str): [Optional] Airtable formula string used to filter records.
        max_records (int): [Optional] Maximum number of records to return (default 100, max 100).
        page_size (int): [Optional] Number of records per page (default 100).
        offset (str): [Optional] Pagination cursor returned from a previous call.

    Returns:
        records (array): Array of record objects with id, createdTime, and fields.
        offset (str): Cursor for retrieving the next page; absent when no further pages exist.
    """
    try:
        if not base_id or not isinstance(base_id, str):
            raise ValueError("base_id must be a non-empty string")
        if not table_id or not isinstance(table_id, str):
            raise ValueError("table_id must be a non-empty string")
        return api.list_records(base_id, table_id, view, filter_by_formula, max_records, page_size, offset)
    except Exception as e:
        raise e


@mcp.tool()
def create_record(base_id: str, table_id: str, fields: dict) -> dict:
    """
    Insert a new record into the specified table with the provided field values.

    Args:
        base_id (str): The unique identifier of the Airtable base containing the table.
        table_id (str): The table ID or table name where the new record will be created.
        fields (dict): Map of field names or IDs to the values assigned to the new record.

    Returns:
        id (str): The unique identifier of the newly created record.
        createdTime (str): ISO 8601 timestamp indicating when the record was created.
        fields (dict): Complete set of field values as stored for the new record.
    """
    try:
        if not base_id or not isinstance(base_id, str):
            raise ValueError("base_id must be a non-empty string")
        if not table_id or not isinstance(table_id, str):
            raise ValueError("table_id must be a non-empty string")
        if not isinstance(fields, dict):
            raise ValueError("fields must be a dictionary")
        return api.create_record(base_id, table_id, fields)
    except Exception as e:
        raise e


@mcp.tool()
def update_record(base_id: str, table_id: str, record_id: str, fields: dict) -> dict:
    """
    Modify specific fields of an existing record without altering others.

    Args:
        base_id (str): The unique identifier of the Airtable base containing the table.
        table_id (str): The table ID or table name that holds the record to update.
        record_id (str): The unique identifier of the record to be updated.
        fields (dict): Map of field names or IDs to the new values; omitted fields remain unchanged.

    Returns:
        id (str): The unique identifier of the updated record.
        createdTime (str): ISO 8601 timestamp indicating when the record was originally created.
        fields (dict): Full set of field values reflecting the update.
    """
    try:
        if not base_id or not isinstance(base_id, str):
            raise ValueError("base_id must be a non-empty string")
        if not table_id or not isinstance(table_id, str):
            raise ValueError("table_id must be a non-empty string")
        if not record_id or not isinstance(record_id, str):
            raise ValueError("record_id must be a non-empty string")
        if not isinstance(fields, dict):
            raise ValueError("fields must be a dictionary")
        result = api.update_record(base_id, table_id, record_id, fields)
        if result is None:
            raise ValueError(f"Record {record_id} not found in base {base_id}, table {table_id}")
        return result
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()


