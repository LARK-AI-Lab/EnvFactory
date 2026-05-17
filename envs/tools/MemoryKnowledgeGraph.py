from pydantic import BaseModel, Field
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Entity(BaseModel):
    name: str = Field(..., description="Unique name of the entity")
    entityType: str = Field(..., description="Category or class of the entity")
    observations: List[str] = Field(default_factory=list, description="Factual statements attached to this entity")

class Relation(BaseModel):
    from_entity: str = Field(..., description="Source entity name")
    to_entity: str = Field(..., description="Target entity name")
    relationType: str = Field(..., description="Label describing the nature of the relation")

class KnowledgeGraphScenario(BaseModel):
    entities: Dict[str, Any] = Field(default_factory=dict, description="All entities in the graph keyed by name")
    relations: List[Any] = Field(default_factory=list, description="All directed relations in the graph")

Scenario_Schema = [Entity, Relation, KnowledgeGraphScenario]

# Section 2: Class
class MemoryKnowledgeGraphAPI:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []

    def load_scenario(self, scenario: dict) -> None:
        self.entities = {}
        self.relations = []
        model = KnowledgeGraphScenario(**scenario)
        for name, data in model.entities.items():
            if isinstance(data, dict):
                self.entities[name] = Entity(**data)
            elif isinstance(data, Entity):
                self.entities[name] = data
            else:
                raise ValueError(f"Invalid entity data for '{name}': {data}")
        for r in model.relations:
            if isinstance(r, dict):
                self.relations.append(
                    Relation(
                        from_entity=r.get("from_entity") or r.get("from", ""),
                        to_entity=r.get("to_entity") or r.get("to", ""),
                        relationType=r["relationType"]
                    )
                )
            elif isinstance(r, Relation):
                self.relations.append(r)

    def save_scenario(self) -> dict:
        return {
            "entities": {name: e.model_dump() for name, e in self.entities.items()},
            "relations": [r.model_dump() for r in self.relations]
        }

    def create_entities(self, entities: list) -> dict:
        created = []
        skipped = []
        for e in entities:
            name = e["name"]
            if name in self.entities:
                skipped.append(name)
            else:
                entity = Entity(name=name, entityType=e["entityType"], observations=e.get("observations", []))
                self.entities[name] = entity
                created.append({"name": entity.name, "entityType": entity.entityType, "observations": entity.observations})
        return {"created": created, "skipped": skipped}

    def create_relations(self, relations: list) -> dict:
        created = []
        skipped = []
        for r in relations:
            # Accept both "from"/"to" and "from_entity"/"to_entity" key styles
            from_name = r.get("from") or r.get("from_entity", "")
            to_name = r.get("to") or r.get("to_entity", "")
            relation_type = r["relationType"]
            if from_name not in self.entities or to_name not in self.entities:
                skipped.append(r)
            else:
                duplicate = any(
                    rel.from_entity == from_name and rel.to_entity == to_name and rel.relationType == relation_type
                    for rel in self.relations
                )
                if duplicate:
                    skipped.append(r)
                else:
                    rel = Relation(from_entity=from_name, to_entity=to_name, relationType=relation_type)
                    self.relations.append(rel)
                    created.append({"from": from_name, "to": to_name, "relationType": relation_type})
        return {"created": created, "skipped": skipped}

    def add_observations(self, observations: list) -> dict:
        added = []
        for obs in observations:
            entity_name = obs["entityName"]
            contents = obs["contents"]
            # Normalize to list of strings — must check str first to avoid char-splitting
            if isinstance(contents, str):
                contents = [contents]
            elif not isinstance(contents, list):
                contents = [str(contents)]
            else:
                # Ensure all items in list are strings
                contents = [str(c) for c in contents]
            entity = self.entities[entity_name]
            new_obs = [c for c in contents if c not in entity.observations]
            entity.observations.extend(new_obs)
            added.append({"entityName": entity_name, "contents": new_obs})
        return {"added": added}

    def search_nodes(self, query: str) -> dict:
        query_lower = query.lower()
        matched_entities = []
        matched_names = set()
        for name, entity in self.entities.items():
            if (query_lower in name.lower() or
                query_lower in entity.entityType.lower() or
                any(query_lower in obs.lower() for obs in entity.observations)):
                matched_entities.append(entity.model_dump())
                matched_names.add(name)
        matched_relations = [
            {"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}
            for r in self.relations
            if r.from_entity in matched_names or r.to_entity in matched_names
        ]
        return {"entities": matched_entities, "relations": matched_relations}

    def open_nodes(self, names: list) -> dict:
        name_set = set(names)
        entities = [self.entities[n].model_dump() for n in names if n in self.entities]
        relations = [
            {"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}
            for r in self.relations
            if r.from_entity in name_set and r.to_entity in name_set
        ]
        return {"entities": entities, "relations": relations}

# Section 3: MCP Tools
mcp = FastMCP(name="MemoryKnowledgeGraph")
api = MemoryKnowledgeGraphAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the knowledge graph API.

    Args:
        scenario (dict): Scenario dictionary matching KnowledgeGraphScenario schema.

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
    Save current knowledge graph state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def create_entities(entities: list) -> dict:
    """
    Insert multiple entities into the knowledge graph.

    Args:
        entities (list): List of entity objects, each with name, entityType, and observations.

    Returns:
        created (list): Entities that were successfully created.
        skipped (list): Names of entities that already existed and were skipped.
    """
    try:
        if not entities or not isinstance(entities, list):
            raise ValueError("entities must be a non-empty list")
        for e in entities:
            if not e.get("name") or not e.get("entityType"):
                raise ValueError("Each entity must have a non-empty name and entityType")
        return api.create_entities(entities)
    except Exception as e:
        raise e

@mcp.tool()
def create_relations(relations: list) -> dict:
    """
    Create directed relationships between existing entities in the knowledge graph.

    Args:
        relations (list): List of relation objects, each with from, to, and relationType.

    Returns:
        created (list): Relations that were successfully created.
        skipped (list): Relations that could not be created (e.g., missing entities).
    """
    try:
        if not relations or not isinstance(relations, list):
            raise ValueError("relations must be a non-empty list")
        for r in relations:
            from_val = r.get("from") or r.get("from_entity")
            to_val = r.get("to") or r.get("to_entity")
            if not from_val or not to_val or not r.get("relationType"):
                raise ValueError("Each relation must have non-empty from, to, and relationType")
        return api.create_relations(relations)
    except Exception as e:
        raise e

@mcp.tool()
def add_observations(observations: list) -> dict:
    """
    Append new observations to existing entities in the knowledge graph.

    Args:
        observations (list): List of observation objects, each with entityName and contents (str or list of str).

    Returns:
        added (list): Records confirming which observations were appended, with entityName and contents fields.
    """
    try:
        if not observations or not isinstance(observations, list):
            raise ValueError("observations must be a non-empty list")
        for obs in observations:
            entity_name = obs.get("entityName")
            if not entity_name:
                raise ValueError("Each observation must have a non-empty entityName")
            if entity_name not in api.entities:
                raise ValueError(f"Entity '{entity_name}' not found")
            # Normalize contents to list before passing to API
            contents = obs.get("contents", [])
            if isinstance(contents, str):
                obs["contents"] = [contents]
            elif not isinstance(contents, list):
                obs["contents"] = [str(contents)]
        return api.add_observations(observations)
    except Exception as e:
        raise e

@mcp.tool()
def search_nodes(query: str) -> dict:
    """
    Search the knowledge graph for entities and relations matching a text query.

    Args:
        query (str): Text to match against entity names, types, and observation contents.

    Returns:
        entities (list): Entities whose name, type, or observations contain the query text.
        relations (list): Relations connected to matched entities.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("query must be a non-empty string")
        return api.search_nodes(query)
    except Exception as e:
        raise e

@mcp.tool()
def open_nodes(names: list) -> dict:
    """
    Retrieve full details of specific entities and any relations between them.

    Args:
        names (list): List of entity names to fetch.

    Returns:
        entities (list): Detailed objects for each requested entity.
        relations (list): Relations that exist among the requested entities.
    """
    try:
        if not names or not isinstance(names, list):
            raise ValueError("names must be a non-empty list")
        return api.open_nodes(names)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
