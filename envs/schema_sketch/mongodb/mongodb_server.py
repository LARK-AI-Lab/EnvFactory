# Data Source: https://www.mongodb.com/docs/mongodb-mcp-server/current/
# Server: MongoDB
# Category: Database


def list_databases() -> dict:
    """
    List databases visible to the MongoDB connection.

    Returns:
        dict: {
            "databases": list[{
                "name": str,
                "sizeOnDisk": int,
                "empty": bool
            }]
        }
    """
    pass


def list_collections(database: str) -> dict:
    """
    List collections in a MongoDB database.

    Args:
        database (str): Database name

    Returns:
        dict: {
            "database": str,
            "collections": list[{
                "name": str,
                "type": str,
                "options": dict
            }]
        }
    """
    pass


def find(database: str, collection: str, filter: dict = None,
         projection: dict = None, sort: dict = None, limit: int = 10,
         skip: int = 0) -> dict:
    """
    Find documents in a MongoDB collection.

    Args:
        database (str): Database name
        collection (str): Collection name
        filter (dict): [Optional] MongoDB query predicate
        projection (dict): [Optional] Projection specification for returned fields
        sort (dict): [Optional] Sort specification keyed by field
        limit (int): [Optional] Maximum number of documents to return
        skip (int): [Optional] Number of matching documents to skip

    Returns:
        dict: {
            "database": str,
            "collection": str,
            "documents": list[dict],
            "count": int
        }
    """
    pass


def aggregate(database: str, collection: str, pipeline: list) -> dict:
    """
    Run an aggregation pipeline against a MongoDB collection.

    Args:
        database (str): Database name
        collection (str): Collection name
        pipeline (list): Ordered list of aggregation pipeline stages

    Returns:
        dict: {
            "database": str,
            "collection": str,
            "results": list[dict],
            "count": int
        }
    """
    pass


def insert_one(database: str, collection: str, document: dict) -> dict:
    """
    Insert one document into a MongoDB collection.

    Args:
        database (str): Database name
        collection (str): Collection name
        document (dict): Document to insert

    Returns:
        dict: {
            "acknowledged": bool,
            "inserted_id": str,
            "document": dict
        }
    """
    pass
