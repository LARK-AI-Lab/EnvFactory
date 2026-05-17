
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class PropertyProfile(BaseModel):
    """Property profile with basic identifiers."""
    property_id: str = Field(..., description="Unique property identifier")
    fips: str = Field(..., description="FIPS county code")
    apn: str = Field(..., description="Assessor's Parcel Number")
    address: str = Field(..., description="Standardized street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., pattern=r"^[A-Z]{2}$", description="Two-letter state code")
    zip: str = Field(..., pattern=r"^\d{5}(-\d{4})?$", description="ZIP code")

class PropertyDetails(BaseModel):
    """Detailed property characteristics."""
    property_id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Standardized street address")
    sqft: int = Field(..., ge=0, description="Living area in square feet")
    lot_size: int = Field(..., ge=0, description="Lot size in square feet")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    year_built: int = Field(..., ge=1600, le=2100, description="Year constructed")
    property_type: str = Field(..., description="Property classification")
    stories: int = Field(..., ge=1, description="Number of floors")
    garage_type: str = Field(..., description="Garage classification")

class PropertyValuation(BaseModel):
    """AVM valuation estimate."""
    estimated_value: float = Field(..., ge=0, description="AVM market value estimate")
    value_range_low: float = Field(..., ge=0, description="Lower bound estimate")
    value_range_high: float = Field(..., ge=0, description="Upper bound estimate")
    confidence_score: str = Field(..., description="Reliability rating")
    valuation_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Valuation date")

class TaxAssessment(BaseModel):
    """Tax assessment record."""
    assessed_value: float = Field(..., ge=0, description="Total assessed value")
    assessed_land_value: float = Field(..., ge=0, description="Land value portion")
    assessed_improvement_value: float = Field(..., ge=0, description="Improvement value portion")
    tax_amount: float = Field(..., ge=0, description="Annual tax amount")
    tax_year: int = Field(..., ge=1900, description="Tax fiscal year")
    assessment_year: int = Field(..., ge=1900, description="Assessment year")

class School(BaseModel):
    """School information."""
    school_name: str = Field(..., description="School name")
    distance: float = Field(..., ge=0, description="Distance in miles")
    school_type: str = Field(..., description="School classification")
    grade_level: str = Field(..., description="Grade range served")
    rating: float = Field(..., ge=0, le=10, description="Quality rating")

class AttomScenario(BaseModel):
    """Main scenario for ATTOM real estate data."""
    property_profiles: Dict[str, PropertyProfile] = Field(default={}, description="Property profiles by address")
    property_details: Dict[str, PropertyDetails] = Field(default={}, description="Property details by address")
    property_valuations: Dict[str, PropertyValuation] = Field(default={}, description="Property valuations by address")
    tax_assessments: Dict[str, TaxAssessment] = Field(default={}, description="Tax assessments by address")
    schools_by_address: Dict[str, List[School]] = Field(default={}, description="Schools by property address")

Scenario_Schema = [PropertyProfile, PropertyDetails, PropertyValuation, TaxAssessment, School, AttomScenario]

# Section 2: Class
class AttomRealEstateAPI:
    def __init__(self):
        """Initialize ATTOM real estate API with empty state."""
        self.property_profiles: Dict[str, PropertyProfile] = {}
        self.property_details: Dict[str, PropertyDetails] = {}
        self.property_valuations: Dict[str, PropertyValuation] = {}
        self.tax_assessments: Dict[str, TaxAssessment] = {}
        self.schools_by_address: Dict[str, List[School]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = AttomScenario(**scenario)
        self.property_profiles = model.property_profiles
        self.property_details = model.property_details
        self.property_valuations = model.property_valuations
        self.tax_assessments = model.tax_assessments
        self.schools_by_address = model.schools_by_address

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "property_profiles": {addr: profile.model_dump() for addr, profile in self.property_profiles.items()},
            "property_details": {addr: details.model_dump() for addr, details in self.property_details.items()},
            "property_valuations": {addr: val.model_dump() for addr, val in self.property_valuations.items()},
            "tax_assessments": {addr: tax.model_dump() for addr, tax in self.tax_assessments.items()},
            "schools_by_address": {addr: [school.model_dump() for school in schools] for addr, schools in self.schools_by_address.items()}
        }

    def get_property_profile(self, address: str) -> dict:
        """Retrieve property profile by address."""
        profile = self.property_profiles[address]
        return profile.model_dump()

    def get_property_details(self, address: str) -> dict:
        """Retrieve property details by address."""
        details = self.property_details[address]
        return details.model_dump()

    def get_property_valuation(self, address: str) -> dict:
        """Retrieve property valuation by address."""
        valuation = self.property_valuations[address]
        return valuation.model_dump()

    def get_tax_assessment(self, address: str) -> dict:
        """Retrieve tax assessment by address."""
        assessment = self.tax_assessments[address]
        return assessment.model_dump()

    def get_nearby_schools(self, address: str, radius: int) -> dict:
        """Retrieve nearby schools within radius."""
        schools = self.schools_by_address.get(address, [])
        filtered = [s for s in schools if s.distance <= radius]
        return {"schools": [school.model_dump() for school in filtered]}

# Section 3: MCP Tools
mcp = FastMCP(name="AttomRealEstate")
api = AttomRealEstateAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the ATTOM real estate API.

    Args:
        scenario (dict): Scenario dictionary matching AttomScenario schema.

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
    Save current ATTOM real estate state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_property_profile(address: str) -> dict:
    """
    Retrieves basic identifying information for a property including its unique identifiers, standardized address components, and geographic coding.

    Args:
        address (str): The complete street address of the target property, including city, state, and ZIP code.

    Returns:
        property_id (str): The unique identifier assigned to the property by the ATTOM data system.
        fips (str): The Federal Information Processing Standards (FIPS) county code for the property's location.
        apn (str): The Assessor's Parcel Number, a unique identifier assigned by the local tax assessor's office.
        address (str): The standardized full street address of the property.
        city (str): The city name where the property is located.
        state (str): The two-letter state abbreviation where the property is located.
        zip (str): The postal ZIP code for the property's address.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if address not in api.property_profiles:
            raise ValueError(f"Property profile not found for address: {address}")
        return api.get_property_profile(address)
    except Exception as e:
        raise e

@mcp.tool()
def get_property_details(address: str) -> dict:
    """
    Retrieves detailed physical characteristics and building specifications for a property including square footage, room counts, construction year, and structural features.

    Args:
        address (str): The complete street address of the target property, including city, state, and ZIP code.

    Returns:
        property_id (str): The unique identifier assigned to the property by the ATTOM data system.
        address (str): The standardized full street address of the property.
        sqft (int): The total finished living area of the property in square feet.
        lot_size (int): The total land area of the property lot in square feet.
        bedrooms (int): The total number of bedrooms in the property.
        bathrooms (float): The total number of bathrooms in the property, including partial baths as decimal values.
        year_built (int): The calendar year when the property was originally constructed.
        property_type (str): The classification of the property structure (e.g., Single Family Residence, Condominium, Townhouse).
        stories (int): The number of above-ground levels or floors in the property structure.
        garage_type (str): The classification of garage facilities attached to the property (e.g., Attached, Detached, None).
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if address not in api.property_details:
            raise ValueError(f"Property details not found for address: {address}")
        return api.get_property_details(address)
    except Exception as e:
        raise e

@mcp.tool()
def get_property_valuation(address: str) -> dict:
    """
    Retrieves an Automated Valuation Model (AVM) estimate for a property including the estimated market value, confidence range, and valuation metadata.

    Args:
        address (str): The complete street address of the target property, including city, state, and ZIP code.

    Returns:
        estimated_value (float): The calculated Automated Valuation Model estimate of the property's current market value in USD.
        value_range_low (float): The lower bound of the estimated value range representing the conservative market value estimate.
        value_range_high (float): The upper bound of the estimated value range representing the optimistic market value estimate.
        confidence_score (str): The rating indicating the reliability of the AVM estimate based on available data quality and comparables (e.g., High, Medium, Low).
        valuation_date (str): The date when the valuation estimate was calculated, typically in ISO 8601 format.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if address not in api.property_valuations:
            raise ValueError(f"Property valuation not found for address: {address}")
        return api.get_property_valuation(address)
    except Exception as e:
        raise e

@mcp.tool()
def get_tax_assessment(address: str) -> dict:
    """
    Retrieves official tax assessment records for a property including assessed values, land/improvement breakdowns, and annual tax obligations.

    Args:
        address (str): The complete street address of the target property, including city, state, and ZIP code.

    Returns:
        assessed_value (float): The total assessed value of the property as determined by the local tax assessor for taxation purposes.
        assessed_land_value (float): The portion of the total assessed value attributed to the land itself, excluding improvements.
        assessed_improvement_value (float): The portion of the total assessed value attributed to structures and improvements on the land.
        tax_amount (float): The total annual property tax amount due based on the assessed value and local millage rates.
        tax_year (int): The fiscal year for which the property taxes are assessed and collected.
        assessment_year (int): The year in which the property valuation was assessed by the local tax authority.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if address not in api.tax_assessments:
            raise ValueError(f"Tax assessment not found for address: {address}")
        return api.get_tax_assessment(address)
    except Exception as e:
        raise e

@mcp.tool()
def get_nearby_schools(address: str, radius: int = 5) -> dict:
    """
    Retrieves a list of educational institutions located within a specified radius of the target property, including distance, type, and quality metrics.

    Args:
        address (str): The complete street address of the target property, including city, state, and ZIP code.
        radius (int): [Optional] The search radius in miles from the property location to find nearby schools. Defaults to 5 miles if not specified.

    Returns:
        schools (list): A collection of educational institutions found within the specified search radius.
            school_name (str): The official name of the educational institution.
            distance (float): The linear distance from the property to the school in miles.
            school_type (str): The classification of the school (e.g., Public, Private, Charter).
            grade_level (str): The range of grade levels served by the school (e.g., Elementary, Middle, High, K-12).
            rating (float): The numerical quality or performance rating assigned to the school by relevant educational authorities.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if address not in api.schools_by_address:
            raise ValueError(f"Schools data not found for address: {address}")
        return api.get_nearby_schools(address, radius)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
