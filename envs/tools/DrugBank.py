
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Drug(BaseModel):
    """Represents a drug in the database."""
    drugbank_id: str = Field(..., pattern=r"^DB\d{5}$", description="DrugBank ID (format: DB followed by 5 digits)")
    name: str = Field(..., description="Primary drug name")
    description: str = Field(default="", description="Clinical description")
    synonyms: List[str] = Field(default_factory=list, description="Alternative names")
    categories: List[str] = Field(default_factory=list, description="Therapeutic categories")
    atc_codes: List[str] = Field(default_factory=list, description="ATC classification codes")
    mechanism_of_action: str = Field(default="", description="Mechanism of action")
    pharmacodynamics: str = Field(default="", description="Pharmacodynamics")
    absorption: str = Field(default="", description="Absorption information")
    metabolism: str = Field(default="", description="Metabolism information")
    indications: List[str] = Field(default_factory=list, description="Approved therapeutic uses")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    dosage_forms: List[str] = Field(default_factory=list, description="Available dosage forms")
    side_effects: List[str] = Field(default_factory=list, description="Adverse reactions")
    pregnancy_category: str = Field(default="", description="Pregnancy safety category")

class Interaction(BaseModel):
    """Represents a drug-drug interaction."""
    drug1: str = Field(..., description="First drug identifier")
    drug2: str = Field(..., description="Second drug identifier")
    severity: str = Field(..., pattern=r"^(minor|moderate|major)$", description="Interaction severity")
    description: str = Field(..., description="Interaction description")
    management: str = Field(..., description="Management recommendations")

class Product(BaseModel):
    """Represents a commercial drug product."""
    barcode: str = Field(..., pattern=r"^\d{8,14}$", description="UPC/EAN barcode")
    drugbank_id: str = Field(..., pattern=r"^DB\d{5}$", description="DrugBank ID")
    product_name: str = Field(..., description="Commercial product name")
    manufacturer: str = Field(..., description="Manufacturer name")
    active_ingredients: List[str] = Field(..., description="Active ingredients")
    dosage_strength: str = Field(..., description="Dosage strength")
    packaging: str = Field(..., description="Packaging description")
    approved: bool = Field(..., description="Regulatory approval status")

class DrugBankScenario(BaseModel):
    """Main scenario model for DrugBank database."""
    drugs: Dict[str, Drug] = Field(default_factory=dict, description="Drugs indexed by DrugBank ID")
    interactions: List[Interaction] = Field(default_factory=list, description="Drug-drug interactions")
    products: Dict[str, Product] = Field(default_factory=dict, description="Products indexed by barcode")
    condition_index: Dict[str, List[str]] = Field(default_factory=dict, description="Condition to drug IDs mapping")

Scenario_Schema = [Drug, Interaction, Product, DrugBankScenario]

# Section 2: Class
class DrugBankAPI:
    def __init__(self):
        """Initialize DrugBank API with empty state."""
        self.drugs: Dict[str, Drug] = {}
        self.interactions: List[Interaction] = []
        self.products: Dict[str, Product] = {}
        self.condition_index: Dict[str, List[str]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = DrugBankScenario(**scenario)
        self.drugs = model.drugs
        self.interactions = model.interactions
        self.products = model.products
        self.condition_index = model.condition_index

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "drugs": {k: v.model_dump() for k, v in self.drugs.items()},
            "interactions": [i.model_dump() for i in self.interactions],
            "products": {k: v.model_dump() for k, v in self.products.items()},
            "condition_index": self.condition_index
        }

    def search_drugs(self, query: str, fuzzy: bool, limit: int) -> dict:
        """Search drugs by name or synonym."""
        results = []
        query_lower = query.lower()
        
        for drug in self.drugs.values():
            if query_lower in drug.name.lower() or any(query_lower in syn.lower() for syn in drug.synonyms):
                results.append({
                    "drugbank_id": drug.drugbank_id,
                    "name": drug.name,
                    "description": drug.description,
                    "synonyms": drug.synonyms,
                    "categories": drug.categories,
                    "atc_codes": drug.atc_codes
                })
                if len(results) >= limit:
                    break
        
        return {"drugs": results}

    def get_drug_details(self, drugbank_id: str) -> dict:
        """Retrieve comprehensive drug information."""
        drug = self.drugs[drugbank_id]
        return {
            "drugbank_id": drug.drugbank_id,
            "name": drug.name,
            "description": drug.description,
            "mechanism_of_action": drug.mechanism_of_action,
            "pharmacodynamics": drug.pharmacodynamics,
            "absorption": drug.absorption,
            "metabolism": drug.metabolism,
            "indications": drug.indications,
            "contraindications": drug.contraindications,
            "dosage_forms": drug.dosage_forms,
            "side_effects": drug.side_effects,
            "pregnancy_category": drug.pregnancy_category
        }

    def check_drug_interactions(self, drugs: List[str]) -> dict:
        """Analyze drugs for interactions."""
        found_interactions = []
        severity_order = {"minor": 1, "moderate": 2, "major": 3}
        highest_severity = "none"
        
        for interaction in self.interactions:
            if interaction.drug1 in drugs and interaction.drug2 in drugs:
                found_interactions.append({
                    "drug1": interaction.drug1,
                    "drug2": interaction.drug2,
                    "severity": interaction.severity,
                    "description": interaction.description,
                    "management": interaction.management
                })
                if severity_order.get(interaction.severity, 0) > severity_order.get(highest_severity, 0):
                    highest_severity = interaction.severity
        
        return {
            "interactions": found_interactions,
            "interaction_count": len(found_interactions),
            "highest_severity": highest_severity
        }

    def search_by_condition(self, condition: str) -> dict:
        """Find drugs for a medical condition."""
        condition_lower = condition.lower()
        drug_ids = []
        
        for cond, ids in self.condition_index.items():
            if condition_lower in cond.lower():
                drug_ids.extend(ids)
        
        results = []
        for drug_id in drug_ids:
            if drug_id in self.drugs:
                drug = self.drugs[drug_id]
                results.append({
                    "drugbank_id": drug.drugbank_id,
                    "name": drug.name,
                    "indication_type": "approved",
                    "efficacy": "established"
                })
        
        return {"drugs": results}

    def get_drug_by_barcode(self, barcode: str) -> dict:
        """Identify drug product by barcode."""
        product = self.products[barcode]
        return {
            "drugbank_id": product.drugbank_id,
            "product_name": product.product_name,
            "manufacturer": product.manufacturer,
            "active_ingredients": product.active_ingredients,
            "dosage_strength": product.dosage_strength,
            "packaging": product.packaging,
            "approved": product.approved
        }

# Section 3: MCP Tools
mcp = FastMCP(name="DrugBank")
api = DrugBankAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the DrugBank API.

    Args:
        scenario (dict): Scenario dictionary matching DrugBankScenario schema.

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
    Save current DrugBank state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_drugs(query: str, fuzzy: bool = True, limit: int = 10) -> dict:
    """
    Search the DrugBank database for pharmaceutical substances.

    Args:
        query (str): Search term matching drug names or identifiers.
        fuzzy (bool): Enable approximate string matching [Optional].
        limit (int): Maximum number of results to return [Optional].

    Returns:
        drugs (list): List of matching pharmaceutical substances with drugbank_id, name, description, synonyms, categories, and atc_codes.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_drugs(query, fuzzy, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_drug_details(drugbank_id: str) -> dict:
    """
    Retrieve comprehensive pharmacological information for a specific drug.

    Args:
        drugbank_id (str): The unique DrugBank accession identifier.

    Returns:
        drugbank_id (str): DrugBank identifier.
        name (str): Primary drug name.
        description (str): Clinical description.
        mechanism_of_action (str): Mechanism of action.
        pharmacodynamics (str): Pharmacodynamics.
        absorption (str): Absorption information.
        metabolism (str): Metabolism information.
        indications (list): Approved therapeutic uses.
        contraindications (list): Contraindications.
        dosage_forms (list): Available dosage forms.
        side_effects (list): Adverse reactions.
        pregnancy_category (str): Pregnancy safety category.
    """
    try:
        if not drugbank_id or not isinstance(drugbank_id, str):
            raise ValueError("DrugBank ID must be a non-empty string")
        if drugbank_id not in api.drugs:
            raise ValueError(f"Drug {drugbank_id} not found")
        return api.get_drug_details(drugbank_id)
    except Exception as e:
        raise e

@mcp.tool()
def check_drug_interactions(drugs: List[str]) -> dict:
    """
    Analyze multiple drugs for potential pharmacological interactions.

    Args:
        drugs (list): List of drug identifiers to analyze for interactions.

    Returns:
        interactions (list): List of interactions with drug1, drug2, severity, description, and management.
        interaction_count (int): Total number of interactions identified.
        highest_severity (str): Most severe interaction level detected.
    """
    try:
        if not drugs or not isinstance(drugs, list):
            raise ValueError("Drugs must be a non-empty list")
        return api.check_drug_interactions(drugs)
    except Exception as e:
        raise e

@mcp.tool()
def search_by_condition(condition: str) -> dict:
    """
    Discover medications used to treat specific medical conditions.

    Args:
        condition (str): Medical condition or disease name to search for treatments.

    Returns:
        drugs (list): List of pharmaceutical products with drugbank_id, name, indication_type, and efficacy.
    """
    try:
        if not condition or not isinstance(condition, str):
            raise ValueError("Condition must be a non-empty string")
        return api.search_by_condition(condition)
    except Exception as e:
        raise e

@mcp.tool()
def get_drug_by_barcode(barcode: str) -> dict:
    """
    Identify pharmaceutical products using commercial product barcodes.

    Args:
        barcode (str): UPC or EAN barcode digits from product packaging.

    Returns:
        drugbank_id (str): DrugBank identifier.
        product_name (str): Commercial product name.
        manufacturer (str): Manufacturer name.
        active_ingredients (list): Active compounds.
        dosage_strength (str): Dosage strength.
        packaging (str): Packaging description.
        approved (bool): Regulatory approval status.
    """
    try:
        if not barcode or not isinstance(barcode, str):
            raise ValueError("Barcode must be a non-empty string")
        if barcode not in api.products:
            raise ValueError(f"Product with barcode {barcode} not found")
        return api.get_drug_by_barcode(barcode)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
