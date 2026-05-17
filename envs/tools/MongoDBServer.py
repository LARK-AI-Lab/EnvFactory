

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import copy

# Section 1: Schema

class DatabaseInfo(BaseModel):
    name: str = Field(..., description="Name of the database.")
    sizeOnDisk: int = Field(..., ge=0, description="Approximate total size of the database on disk in bytes.")
    empty: bool = Field(..., description="True if the database contains no collections.")

class CollectionInfo(BaseModel):
    name: str = Field(..., description="Name of the collection.")
    type: str = Field(..., description="Collection type (e.g., 'collection' or 'view').")
    options: Dict[str, Any] = Field(default={}, description="Additional collection options.")

class Document(BaseModel):
    id: str = Field(..., description="Document unique identifier (_id as string).")
    data: Dict[str, Any] = Field(default={}, description="Document fields.")

class MongoDBScenario(BaseModel):
    databases: List[Dict[str, Any]] = Field(default=[
        {"name": "admin", "sizeOnDisk": 40960, "empty": False},
        {"name": "config", "sizeOnDisk": 73728, "empty": False},
        {"name": "local", "sizeOnDisk": 40960, "empty": False},
        {"name": "testdb", "sizeOnDisk": 204800, "empty": False},
        {"name": "analyticsdb", "sizeOnDisk": 512000, "empty": False},
        {"name": "logsdb", "sizeOnDisk": 1048576, "empty": False},
    ], description="List of databases with metadata.")
    collections: Dict[str, List[Dict[str, Any]]] = Field(default={
        "testdb": [
            {"name": "users", "type": "collection", "options": {}},
            {"name": "orders", "type": "collection", "options": {}},
            {"name": "products", "type": "collection", "options": {}},
        ],
        "analyticsdb": [
            {"name": "events", "type": "collection", "options": {}},
            {"name": "sessions", "type": "collection", "options": {}},
        ],
        "logsdb": [
            {"name": "applogs", "type": "collection", "options": {}},
        ],
    }, description="Collections keyed by database name.")
    documents: Dict[str, List[Dict[str, Any]]] = Field(default={
        "testdb.users": [
            {"_id": "u001", "name": "Alice", "email": "alice@example.com", "age": 30, "role": "admin"},
            {"_id": "u002", "name": "Bob", "email": "bob@example.com", "age": 25, "role": "user"},
            {"_id": "u003", "name": "Carol", "email": "carol@example.com", "age": 35, "role": "user"},
        ],
        "testdb.orders": [
            {"_id": "o001", "userId": "u001", "product": "Laptop", "amount": 1200.0, "status": "shipped"},
            {"_id": "o002", "userId": "u002", "product": "Phone", "amount": 800.0, "status": "pending"},
            {"_id": "o003", "userId": "u001", "product": "Tablet", "amount": 500.0, "status": "delivered"},
        ],
        "testdb.products": [
            {"_id": "p001", "name": "Laptop", "price": 1200.0, "stock": 50, "category": "electronics"},
            {"_id": "p002", "name": "Phone", "price": 800.0, "stock": 100, "category": "electronics"},
            {"_id": "p003", "name": "Tablet", "price": 500.0, "stock": 75, "category": "electronics"},
        ],
        "analyticsdb.events": [
            {"_id": "e001", "type": "click", "userId": "u001", "timestamp": "2026-04-17T00:00:00"},
            {"_id": "e002", "type": "view", "userId": "u002", "timestamp": "2026-04-17T00:01:00"},
        ],
        "analyticsdb.sessions": [
            {"_id": "s001", "userId": "u001", "duration": 120, "pages": 5},
        ],
        "logsdb.applogs": [
            {"_id": "l001", "level": "INFO", "message": "Server started", "timestamp": "2026-04-17T00:00:00"},
            {"_id": "l002", "level": "ERROR", "message": "Connection timeout", "timestamp": "2026-04-17T00:05:00"},
        ],
    }, description="Documents keyed by 'database.collection'.")
    next_id_counter: int = Field(default=1000, ge=0, description="Counter for generating new document IDs.")

Scenario_Schema = [DatabaseInfo, CollectionInfo, Document, MongoDBScenario]


# Section 2: Class

class MongoDBAPI:
    def __init__(self):
        self.databases: List[Dict[str, Any]] = []
        self.collections: Dict[str, List[Dict[str, Any]]] = {}
        self.documents: Dict[str, List[Dict[str, Any]]] = {}
        self.next_id_counter: int = 1000

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance, fully replacing all prior state."""
        model = MongoDBScenario(**scenario)
        # Use deepcopy to ensure complete isolation from scenario input and prior state
        self.databases = copy.deepcopy([dict(d) for d in model.databases])
        self.collections = copy.deepcopy({k: [dict(c) for c in v] for k, v in model.collections.items()})
        self.documents = copy.deepcopy({k: [dict(d) for d in v] for k, v in model.documents.items()})
        self.next_id_counter = model.next_id_counter

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "databases": copy.deepcopy(self.databases),
            "collections": copy.deepcopy(self.collections),
            "documents": copy.deepcopy(self.documents),
            "next_id_counter": self.next_id_counter,
        }

    def list_databases(self) -> dict:
        return {"databases": self.databases}

    def list_collections(self, database: str) -> dict:
        cols = self.collections.get(database, [])
        return {"database": database, "collections": cols}

    def find(self, database: str, collection: str, filter: Optional[Dict[str, Any]], projection: Optional[Dict[str, Any]], sort: Optional[Dict[str, Any]], limit: int, skip: int) -> dict:
        key = f"{database}.{collection}"
        all_docs = list(self.documents.get(key, []))

        if filter:
            all_docs = [d for d in all_docs if all(d.get(k) == v for k, v in filter.items())]

        if sort:
            for field, direction in reversed(list(sort.items())):
                all_docs = sorted(all_docs, key=lambda d, f=field: d.get(f, None), reverse=(direction == -1))

        all_docs = all_docs[skip:skip + limit]

        if projection:
            include = {k for k, v in projection.items() if v == 1}
            exclude = {k for k, v in projection.items() if v == 0}
            if include:
                all_docs = [{k: d[k] for k in include if k in d} for d in all_docs]
            elif exclude:
                all_docs = [{k: v for k, v in d.items() if k not in exclude} for d in all_docs]

        return {"database": database, "collection": collection, "documents": all_docs, "count": len(all_docs)}

    def aggregate(self, database: str, collection: str, pipeline: List[Dict[str, Any]]) -> dict:
        key = f"{database}.{collection}"
        docs = list(self.documents.get(key, []))

        for stage in pipeline:
            if "$match" in stage:
                match = stage["$match"]
                docs = [d for d in docs if all(d.get(k) == v for k, v in match.items())]
            elif "$sort" in stage:
                sort = stage["$sort"]
                for field, direction in reversed(list(sort.items())):
                    docs = sorted(docs, key=lambda d, f=field: d.get(f, None), reverse=(direction == -1))
            elif "$limit" in stage:
                docs = docs[:stage["$limit"]]
            elif "$skip" in stage:
                docs = docs[stage["$skip"]:]
            elif "$project" in stage:
                proj = stage["$project"]
                include = {k for k, v in proj.items() if v == 1}
                exclude = {k for k, v in proj.items() if v == 0}
                if include:
                    docs = [{k: d[k] for k in include if k in d} for d in docs]
                elif exclude:
                    docs = [{k: v for k, v in d.items() if k not in exclude} for d in docs]
            elif "$count" in stage:
                field = stage["$count"]
                docs = [{field: len(docs)}]
            elif "$group" in stage:
                group = stage["$group"]
                group_id_field = group.get("_id")
                groups: Dict[Any, Dict[str, Any]] = {}
                for d in docs:
                    gid = d.get(group_id_field.lstrip("$"), None) if isinstance(group_id_field, str) and group_id_field.startswith("$") else group_id_field
                    if gid not in groups:
                        groups[gid] = {"_id": gid}
                    for out_field, expr in group.items():
                        if out_field == "_id":
                            continue
                        if isinstance(expr, dict):
                            if "$sum" in expr:
                                val = expr["$sum"]
                                inc = d.get(val.lstrip("$"), 0) if isinstance(val, str) and val.startswith("$") else val
                                groups[gid][out_field] = groups[gid].get(out_field, 0) + inc
                            elif "$avg" in expr:
                                val = expr["$avg"]
                                inc = d.get(val.lstrip("$"), 0) if isinstance(val, str) and val.startswith("$") else 0
                                prev = groups[gid].get(f"__avg_sum_{out_field}", 0)
                                cnt = groups[gid].get(f"__avg_cnt_{out_field}", 0)
                                groups[gid][f"__avg_sum_{out_field}"] = prev + inc
                                groups[gid][f"__avg_cnt_{out_field}"] = cnt + 1
                                groups[gid][out_field] = groups[gid][f"__avg_sum_{out_field}"] / groups[gid][f"__avg_cnt_{out_field}"]
                            elif "$push" in expr:
                                val = expr["$push"]
                                item = d.get(val.lstrip("$"), None) if isinstance(val, str) and val.startswith("$") else val
                                groups[gid].setdefault(out_field, []).append(item)
                            elif "$first" in expr:
                                val = expr["$first"]
                                if out_field not in groups[gid]:
                                    groups[gid][out_field] = d.get(val.lstrip("$"), None) if isinstance(val, str) and val.startswith("$") else val
                docs = [{k: v for k, v in g.items() if not k.startswith("__avg_")} for g in groups.values()]

        return {"database": database, "collection": collection, "results": docs, "count": len(docs)}

    def insert_one(self, database: str, collection: str, document: Dict[str, Any]) -> dict:
        key = f"{database}.{collection}"
        if key not in self.documents:
            self.documents[key] = []

        db_names = [d["name"] for d in self.databases]
        if database not in db_names:
            self.databases.append({"name": database, "sizeOnDisk": 0, "empty": False})

        if database not in self.collections:
            self.collections[database] = []
        col_names = [c["name"] for c in self.collections[database]]
        if collection not in col_names:
            self.collections[database].append({"name": collection, "type": "collection", "options": {}})

        document = copy.deepcopy(document)
        if "_id" not in document:
            document["_id"] = f"gen_{self.next_id_counter}"
            self.next_id_counter += 1

        self.documents[key].append(document)
        return {"acknowledged": True, "inserted_id": str(document["_id"]), "document": document}


# Section 3: MCP Tools

mcp = FastMCP(name="MongoDBServer")
api = MongoDBAPI()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the MongoDB API.

    Args:
        scenario (dict): Scenario dictionary matching MongoDBScenario schema.

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
    Save current MongoDB state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def list_databases() -> dict:
    """
    List all MongoDB databases visible to the current connection.

    Returns:
        databases (list): List of databases with name (str), sizeOnDisk (int), and empty (bool).
    """
    try:
        return api.list_databases()
    except Exception as e:
        raise e


@mcp.tool()
def list_collections(database: str) -> dict:
    """
    List all collections within a specified MongoDB database.

    Args:
        database (str): The name of the MongoDB database whose collections will be listed.

    Returns:
        database (str): The database name provided in the request.
        collections (list): List of collections with name (str), type (str), and options (dict).
    """
    try:
        if not database or not isinstance(database, str):
            raise ValueError("database must be a non-empty string")
        return api.list_collections(database)
    except Exception as e:
        raise e


@mcp.tool()
def find(
    database: str,
    collection: str,
    filter: Optional[dict] = None,
    projection: Optional[dict] = None,
    sort: Optional[dict] = None,
    limit: int = 10,
    skip: int = 0,
) -> dict:
    """
    Query documents in a MongoDB collection with optional filtering, projection, sorting, and pagination.

    Args:
        database (str): The name of the MongoDB database containing the collection to query.
        collection (str): The name of the MongoDB collection to query.
        filter (dict): [Optional] MongoDB query predicate to filter documents. Defaults to {} (match all).
        projection (dict): [Optional] Projection specification to include or exclude fields.
        sort (dict): [Optional] Sort specification keyed by field names, with values 1 or -1.
        limit (int): [Optional] Maximum number of documents to return. Defaults to 10.
        skip (int): [Optional] Number of matching documents to skip. Defaults to 0.

    Returns:
        database (str): The database name provided in the request.
        collection (str): The collection name provided in the request.
        documents (list): List of documents matching the query criteria.
        count (int): Number of documents returned in this response.
    """
    try:
        if not database or not isinstance(database, str):
            raise ValueError("database must be a non-empty string")
        if not collection or not isinstance(collection, str):
            raise ValueError("collection must be a non-empty string")
        return api.find(database, collection, filter or {}, projection, sort, limit, skip)
    except Exception as e:
        raise e


@mcp.tool()
def aggregate(database: str, collection: str, pipeline: list) -> dict:
    """
    Execute an aggregation pipeline against a MongoDB collection.

    Args:
        database (str): The name of the MongoDB database containing the collection to aggregate.
        collection (str): The name of the MongoDB collection to aggregate.
        pipeline (list): Ordered list of MongoDB aggregation pipeline stages.

    Returns:
        database (str): The database name provided in the request.
        collection (str): The collection name provided in the request.
        results (list): List of documents produced by the aggregation pipeline.
        count (int): Number of documents returned by the aggregation pipeline.
    """
    try:
        if not database or not isinstance(database, str):
            raise ValueError("database must be a non-empty string")
        if not collection or not isinstance(collection, str):
            raise ValueError("collection must be a non-empty string")
        if not isinstance(pipeline, list):
            raise ValueError("pipeline must be a list")
        return api.aggregate(database, collection, pipeline)
    except Exception as e:
        raise e


@mcp.tool()
def insert_one(database: str, collection: str, document: dict) -> dict:
    """
    Insert a single document into a MongoDB collection.

    Args:
        database (str): The name of the MongoDB database containing the collection to insert into.
        collection (str): The name of the MongoDB collection to insert the document into.
        document (dict): The JSON document to insert into the collection.

    Returns:
        acknowledged (bool): True if the insert operation was acknowledged by the server.
        inserted_id (str): The unique identifier (_id) assigned to the inserted document.
        document (dict): The full document as inserted, including the generated _id if applicable.
    """
    try:
        if not database or not isinstance(database, str):
            raise ValueError("database must be a non-empty string")
        if not collection or not isinstance(collection, str):
            raise ValueError("collection must be a non-empty string")
        if not isinstance(document, dict):
            raise ValueError("document must be a dictionary")
        return api.insert_one(database, collection, document)
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()


