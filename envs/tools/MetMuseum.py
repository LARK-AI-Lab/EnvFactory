from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP


# Section 1: Schema
class Department(BaseModel):
    """Represents a curatorial department at The Met."""
    departmentId: str = Field(..., pattern=r"^\d+$", description="The unique identifier of the department at The Met.")
    displayName: str = Field(..., description="The human-readable name of the department.")


class MuseumObject(BaseModel):
    """Represents an object in The Metropolitan Museum of Art's collection."""
    objectId: str = Field(..., pattern=r"^\d+$", description="The unique identifier of the museum object.")
    title: str = Field(default="", description="The title or name of the artwork or object.")
    artist: str = Field(default="", description="The name of the artist or creator of the object.")
    artistBio: str = Field(default="", description="Biographical information about the artist, including nationality and life dates.")
    department: str = Field(default="", description="The curatorial department at The Met responsible for the object.")
    creditLine: str = Field(default="", description="The credit line acknowledging how the object was acquired by the museum.")
    medium: str = Field(default="", description="The materials and techniques used to create the object.")
    dimensions: str = Field(default="", description="The physical dimensions of the object.")
    primaryImageUrl: str = Field(default="", description="URL to the primary image of the object, available under Open Access policy.")
    tags: List[str] = Field(default_factory=list, description="Subject tags associated with the object for categorization and discovery.")


class MetMuseumScenario(BaseModel):
    """Main scenario model for The Metropolitan Museum of Art collection data."""
    departments: List[Department] = Field(default_factory=lambda: [
        {"departmentId": "1", "displayName": "American Decorative Arts"},
        {"departmentId": "3", "displayName": "Ancient Near Eastern Art"},
        {"departmentId": "4", "displayName": "Arms and Armor"},
        {"departmentId": "5", "displayName": "Arts of Africa, Oceania, and the Americas"},
        {"departmentId": "6", "displayName": "Asian Art"},
        {"departmentId": "7", "displayName": "The Cloisters"},
        {"departmentId": "8", "displayName": "The Costume Institute"},
        {"departmentId": "9", "displayName": "Drawings and Prints"},
        {"departmentId": "10", "displayName": "Egyptian Art"},
        {"departmentId": "11", "displayName": "European Paintings"},
        {"departmentId": "12", "displayName": "European Sculpture and Decorative Arts"},
        {"departmentId": "13", "displayName": "Greek and Roman Art"},
        {"departmentId": "14", "displayName": "Islamic Art"},
        {"departmentId": "15", "displayName": "The Robert Lehman Collection"},
        {"departmentId": "16", "displayName": "The Libraries"},
        {"departmentId": "17", "displayName": "Medieval Art"},
        {"departmentId": "18", "displayName": "Musical Instruments"},
        {"departmentId": "19", "displayName": "Photographs"},
        {"departmentId": "21", "displayName": "Modern and Contemporary Art"}
    ], description="List of all curatorial departments at The Met.")

    objects: Dict[str, MuseumObject] = Field(default_factory=lambda: {
        "436535": {"objectId": "436535", "title": "Sunflowers", "artist": "Vincent van Gogh", "artistBio": "Dutch, Zundert 1853–1890 Auvers-sur-Oise", "department": "European Paintings", "creditLine": "Rogers Fund, 1949", "medium": "Oil on canvas", "dimensions": "36 1/4 x 28 3/4 in. (92.1 x 73 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DP229743.jpg", "tags": ["Flowers", "Sunflowers", "Still Life"]},
        "437133": {"objectId": "437133", "title": "Wheat Field with Cypresses", "artist": "Vincent van Gogh", "artistBio": "Dutch, Zundert 1853–1890 Auvers-sur-Oise", "department": "European Paintings", "creditLine": "Purchase, The Annenberg Foundation Gift, 1993", "medium": "Oil on canvas", "dimensions": "28 7/8 x 36 3/4 in. (73.2 x 93.4 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg", "tags": ["Landscapes", "Wheat", "Cypresses", "Sky"]},
        "436524": {"objectId": "436524", "title": "Self-Portrait with a Straw Hat", "artist": "Vincent van Gogh", "artistBio": "Dutch, Zundert 1853–1890 Auvers-sur-Oise", "department": "European Paintings", "creditLine": "Bequest of Miss Adelaide Milton de Groot (1876-1967), 1967", "medium": "Oil on canvas", "dimensions": "16 x 12 1/2 in. (40.6 x 31.8 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DT1502_cropped2.jpg", "tags": ["Portraits", "Self-Portrait", "Hats"]},
        "438417": {"objectId": "438417", "title": "Water Lilies", "artist": "Claude Monet", "artistBio": "French, Paris 1840–1926 Giverny", "department": "European Paintings", "creditLine": "H. O. Havemeyer Collection, Bequest of Mrs. H. O. Havemeyer, 1929", "medium": "Oil on canvas", "dimensions": "51 1/4 x 79 in. (130.2 x 200.7 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DT833.jpg", "tags": ["Flowers", "Water Lilies", "Ponds", "Gardens"]},
        "437984": {"objectId": "437984", "title": "Bridge over a Pond of Water Lilies", "artist": "Claude Monet", "artistBio": "French, Paris 1840–1926 Giverny", "department": "European Paintings", "creditLine": "H. O. Havemeyer Collection, Bequest of Mrs. H. O. Havemeyer, 1929", "medium": "Oil on canvas", "dimensions": "36 1/2 x 29 in. (92.7 x 73.7 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DT847.jpg", "tags": ["Bridges", "Water Lilies", "Gardens", "Ponds"]},
        "459106": {"objectId": "459106", "title": "The Dance Class", "artist": "Edgar Degas", "artistBio": "French, Paris 1834–1917 Paris", "department": "European Paintings", "creditLine": "Bequest of Mrs. Harry Payne Bingham, 1986", "medium": "Oil on canvas", "dimensions": "32 3/4 x 30 1/4 in. (83.2 x 76.8 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DT2360.jpg", "tags": ["Dance", "Ballet", "Dancers", "Interiors"]},
        "435882": {"objectId": "435882", "title": "Washington Crossing the Delaware", "artist": "Emanuel Leutze", "artistBio": "American, Schwäbisch Gmünd 1816–1868 Washington, D.C.", "department": "American Paintings and Sculpture", "creditLine": "Gift of John Stewart Kennedy, 1897", "medium": "Oil on canvas", "dimensions": "149 x 255 in. (378.5 x 647.7 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ap/original/DT73.jpg", "tags": ["History", "George Washington", "American Revolution", "Boats"]},
        "10467": {"objectId": "10467", "title": "Armor of Emperor Ferdinand I", "artist": "Kunz Lochner", "artistBio": "German, Nuremberg, active 1510–1567", "department": "Arms and Armor", "creditLine": "Gift of William H. Riggs, 1913", "medium": "Steel, gold, leather, textile", "dimensions": "H. 67 in. (170.2 cm); Wt. 52 lb. 6 oz. (23.77 kg)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/aa/original/DT773.jpg", "tags": ["Armor", "Medieval", "Emperor", "Military"]},
        "544896": {"objectId": "544896", "title": "Temple of Dendur", "artist": "", "artistBio": "", "department": "Egyptian Art", "creditLine": "Given to the United States by Egypt in 1965, awarded to The Metropolitan Museum of Art in 1967, and installed in The Sackler Wing in 1978", "medium": "Aeolian sandstone", "dimensions": "Temple proper: H. 6.4 m (21 ft.); W. 6.4 m (21 ft.); D. 12.5 m (41 ft.)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/eg/original/DP116357.jpg", "tags": ["Temple", "Egypt", "Ancient", "Architecture"]},
        "45434": {"objectId": "45434", "title": "Statue of a kouros (youth)", "artist": "", "artistBio": "", "department": "Greek and Roman Art", "creditLine": "Fletcher Fund, 1932", "medium": "Naxian marble", "dimensions": "H. 76 3/8 in. (194 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/gr/original/DP132634.jpg", "tags": ["Sculpture", "Greek", "Youth", "Marble"]},
        "503940": {"objectId": "503940", "title": "The Great Wave off Kanagawa", "artist": "Katsushika Hokusai", "artistBio": "Japanese, Tokyo (Edo) 1760–1849 Tokyo (Edo)", "department": "Asian Art", "creditLine": "H. O. Havemeyer Collection, Bequest of Mrs. H. O. Havemeyer, 1929", "medium": "Polychrome woodblock print; ink and color on paper", "dimensions": "10 1/8 x 14 15/16 in. (25.7 x 37.9 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/as/original/DP141063.jpg", "tags": ["Waves", "Japan", "Mount Fuji", "Boats", "Sea"]},
        "267838": {"objectId": "267838", "title": "Madame X (Madame Pierre Gautreau)", "artist": "John Singer Sargent", "artistBio": "American, Florence 1856–1925 London", "department": "American Paintings and Sculpture", "creditLine": "Arthur Hoppock Hearn Fund, 1916", "medium": "Oil on canvas", "dimensions": "82 1/8 x 43 1/4 in. (208.6 x 109.9 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ap/original/DT1576.jpg", "tags": ["Portraits", "Women", "Fashion", "Evening Dress"]},
        "436105": {"objectId": "436105", "title": "The Starry Night", "artist": "Vincent van Gogh", "artistBio": "Dutch, Zundert 1853–1890 Auvers-sur-Oise", "department": "European Paintings", "creditLine": "Acquired through the Lillie P. Bliss Bequest, 1941", "medium": "Oil on canvas", "dimensions": "29 x 36 1/4 in. (73.7 x 92.1 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/ep/original/DP346474.jpg", "tags": ["Night Sky", "Stars", "Village", "Cypress"]},
        "248907": {"objectId": "248907", "title": "Mihrab (Prayer Niche)", "artist": "", "artistBio": "", "department": "Islamic Art", "creditLine": "Harris Brisbane Dick Fund, 1939", "medium": "Mosaic of polychrome-glazed cut tiles on stonite body; set into mortar", "dimensions": "H. 135 1/16 in. (343.1 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/is/original/DP170390.jpg", "tags": ["Islamic", "Architecture", "Mosque", "Tiles"]},
        "193804": {"objectId": "193804", "title": "Guitar", "artist": "Antonio de Torres Jurado", "artistBio": "Spanish, 1817–1892", "department": "Musical Instruments", "creditLine": "Gift of Joseph W. Drexel, 1889", "medium": "Spruce, rosewood, ebony, bone", "dimensions": "H. 38 1/4 in. (97.2 cm)", "primaryImageUrl": "https://images.metmuseum.org/CRDImages/mi/original/DP302641.jpg", "tags": ["Guitar", "Music", "Instrument", "Spanish"]}
    }, description="Collection of museum objects indexed by objectId.")


Scenario_Schema = [Department, MuseumObject, MetMuseumScenario]


# Section 2: Class
class MetMuseumAPI:
    def __init__(self):
        """Initialize Met Museum API with empty state."""
        self.departments: List[Department] = []
        self.objects: Dict[str, MuseumObject] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MetMuseumScenario(**scenario)
        self.departments = [Department(**d) if isinstance(d, dict) else d for d in model.departments]
        self.objects = {k: MuseumObject(**v) if isinstance(v, dict) else v for k, v in model.objects.items()}

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "departments": [d.model_dump() for d in self.departments],
            "objects": {k: v.model_dump() for k, v in self.objects.items()}
        }

    def list_departments(self) -> dict:
        """Retrieve a list of all valid curatorial departments at The Met."""
        return {
            "departments": [
                {"departmentId": d.departmentId, "displayName": d.displayName}
                for d in self.departments
            ]
        }

    def search_museum_objects(self, q: str, title: Optional[bool] = None, departmentId: Optional[str] = None) -> dict:
        """Search for objects in the museum's collection based on query and filters."""
        matching_ids = []
        query_lower = q.lower()

        for obj_id, obj in self.objects.items():
            # Filter by department if specified
            if departmentId is not None:
                dept_match = False
                for dept in self.departments:
                    if dept.departmentId == departmentId and dept.displayName == obj.department:
                        dept_match = True
                        break
                if not dept_match:
                    # Also check if department name contains the department display name
                    dept_names = [d.displayName for d in self.departments if d.departmentId == departmentId]
                    if not any(dn == obj.department for dn in dept_names):
                        continue

            # Search logic
            if title:
                # Search only in title
                if query_lower in obj.title.lower():
                    matching_ids.append(obj_id)
            else:
                # Search in title, artist, tags, medium, department
                searchable_text = " ".join([
                    obj.title,
                    obj.artist,
                    obj.artistBio,
                    obj.department,
                    obj.medium,
                    " ".join(obj.tags)
                ]).lower()
                if query_lower in searchable_text:
                    matching_ids.append(obj_id)

        return {
            "total": len(matching_ids),
            "objectIds": matching_ids
        }

    def get_museum_object(self, objectId: str) -> dict:
        """Retrieve detailed information about a specific object."""
        obj = self.objects[objectId]
        return {
            "objectId": obj.objectId,
            "title": obj.title,
            "artist": obj.artist,
            "artistBio": obj.artistBio,
            "department": obj.department,
            "creditLine": obj.creditLine,
            "medium": obj.medium,
            "dimensions": obj.dimensions,
            "primaryImageUrl": obj.primaryImageUrl,
            "tags": obj.tags
        }


# Section 3: MCP Tools
mcp = FastMCP(name="MetMuseum")
api = MetMuseumAPI()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Met Museum API.

    Args:
        scenario (dict): Scenario dictionary matching MetMuseumScenario schema.

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
    Save current Met Museum state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def list_departments() -> dict:
    """
    Retrieve a list of all valid curatorial departments at The Metropolitan Museum of Art.

    Args:
        None

    Returns:
        departments (list): List of all curatorial departments at The Met, each containing departmentId (str) and displayName (str).
    """
    try:
        return api.list_departments()
    except Exception as e:
        raise e


@mcp.tool()
def search_museum_objects(q: str, title: Optional[bool] = None, departmentId: Optional[str] = None) -> dict:
    """
    Search for objects in The Metropolitan Museum of Art's collection based on a query term, with optional filters for title-specific search and department.

    Args:
        q (str): The search term to query against the museum's collection (e.g., 'sunflowers', 'Van Gogh').
        title (bool): [Optional] When true, restricts the search to match only against the object's title field.
        departmentId (str): [Optional] The unique identifier of the department at The Met to filter search results.

    Returns:
        total (int): The total number of objects matching the search criteria.
        objectIds (list): List of object IDs matching the search criteria, which can be used with get_museum_object to retrieve full details.
    """
    try:
        if not q or not isinstance(q, str):
            raise ValueError("Search query 'q' must be a non-empty string")
        if title is not None and not isinstance(title, bool):
            raise ValueError("Parameter 'title' must be a boolean")
        if departmentId is not None and not isinstance(departmentId, str):
            raise ValueError("Parameter 'departmentId' must be a string")
        return api.search_museum_objects(q, title, departmentId)
    except Exception as e:
        raise e


@mcp.tool()
def get_museum_object(objectId: str) -> dict:
    """
    Retrieve detailed information about a specific object in The Metropolitan Museum of Art's collection, including metadata and Open Access image URL if available.

    Args:
        objectId (str): The unique identifier of the museum object to retrieve.

    Returns:
        objectId (str): The unique identifier of the museum object.
        title (str): The title or name of the artwork or object.
        artist (str): The name of the artist or creator of the object.
        artistBio (str): Biographical information about the artist, including nationality and life dates.
        department (str): The curatorial department at The Met responsible for the object.
        creditLine (str): The credit line acknowledging how the object was acquired by the museum.
        medium (str): The materials and techniques used to create the object (e.g., 'Oil on canvas').
        dimensions (str): The physical dimensions of the object, typically in both metric and imperial units.
        primaryImageUrl (str): URL to the primary image of the object, available under Open Access policy.
        tags (list): Subject tags associated with the object for categorization and discovery.
    """
    try:
        if not objectId or not isinstance(objectId, str):
            raise ValueError("Parameter 'objectId' must be a non-empty string")
        if objectId not in api.objects:
            raise ValueError(f"Object with ID '{objectId}' not found")
        return api.get_museum_object(objectId)
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
