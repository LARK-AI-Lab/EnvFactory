from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Fruit(BaseModel):
    """Represents a fruit with basic information."""
    name: str = Field(..., description="The common name of the fruit")

class NutritionInfo(BaseModel):
    """Represents nutritional information for a fruit."""
    calories: float = Field(..., ge=0, description="Energy content in kilocalories (kcal) per 100g")
    fat: float = Field(..., ge=0, description="Total fat content in grams per 100g")
    sugar: float = Field(..., ge=0, description="Total sugar content in grams per 100g")
    carbohydrates: float = Field(..., ge=0, description="Total carbohydrate content in grams per 100g")
    protein: float = Field(..., ge=0, description="Total protein content in grams per 100g")

class FruitNutrition(BaseModel):
    """Represents a fruit with detailed nutrition information."""
    name: str = Field(..., description="The common name of the fruit")
    nutritions: NutritionInfo = Field(..., description="Nutritional breakdown per 100 grams")

class FruityviceScenario(BaseModel):
    """Main scenario model for Fruityvice API data."""
    fruits: List[Fruit] = Field(default=[], description="List of available fruits")
    fruitNutritionMap: Dict[str, FruitNutrition] = Field(default={
        "apple": FruitNutrition(name="apple", nutritions=NutritionInfo(calories=52, fat=0.2, sugar=10.4, carbohydrates=14.0, protein=0.3)),
        "banana": FruitNutrition(name="banana", nutritions=NutritionInfo(calories=89, fat=0.3, sugar=12.2, carbohydrates=23.0, protein=1.1)),
        "orange": FruitNutrition(name="orange", nutritions=NutritionInfo(calories=47, fat=0.1, sugar=9.4, carbohydrates=12.0, protein=0.9)),
        "strawberry": FruitNutrition(name="strawberry", nutritions=NutritionInfo(calories=32, fat=0.3, sugar=4.9, carbohydrates=7.7, protein=0.7)),
        "blueberry": FruitNutrition(name="blueberry", nutritions=NutritionInfo(calories=57, fat=0.3, sugar=10.0, carbohydrates=14.0, protein=0.7)),
        "grape": FruitNutrition(name="grape", nutritions=NutritionInfo(calories=67, fat=0.4, sugar=16.0, carbohydrates=17.0, protein=0.6)),
        "watermelon": FruitNutrition(name="watermelon", nutritions=NutritionInfo(calories=30, fat=0.2, sugar=6.2, carbohydrates=7.6, protein=0.6)),
        "pineapple": FruitNutrition(name="pineapple", nutritions=NutritionInfo(calories=50, fat=0.1, sugar=10.0, carbohydrates=13.0, protein=0.5)),
        "mango": FruitNutrition(name="mango", nutritions=NutritionInfo(calories=60, fat=0.4, sugar=14.0, carbohydrates=15.0, protein=0.8)),
        "kiwi": FruitNutrition(name="kiwi", nutritions=NutritionInfo(calories=61, fat=0.5, sugar=9.0, carbohydrates=15.0, protein=1.1)),
        "peach": FruitNutrition(name="peach", nutritions=NutritionInfo(calories=39, fat=0.3, sugar=8.4, carbohydrates=10.0, protein=0.9)),
        "pear": FruitNutrition(name="pear", nutritions=NutritionInfo(calories=57, fat=0.1, sugar=10.0, carbohydrates=15.0, protein=0.4)),
        "plum": FruitNutrition(name="plum", nutritions=NutritionInfo(calories=46, fat=0.3, sugar=10.0, carbohydrates=11.0, protein=0.7)),
        "cherry": FruitNutrition(name="cherry", nutritions=NutritionInfo(calories=63, fat=0.2, sugar=13.0, carbohydrates=16.0, protein=1.1)),
        "avocado": FruitNutrition(name="avocado", nutritions=NutritionInfo(calories=160, fat=15.0, sugar=0.7, carbohydrates=9.0, protein=2.0)),
        "lemon": FruitNutrition(name="lemon", nutritions=NutritionInfo(calories=17, fat=0.2, sugar=1.5, carbohydrates=5.4, protein=0.6)),
        "lime": FruitNutrition(name="lime", nutritions=NutritionInfo(calories=30, fat=0.2, sugar=1.7, carbohydrates=11.0, protein=0.7)),
        "pomegranate": FruitNutrition(name="pomegranate", nutritions=NutritionInfo(calories=83, fat=1.2, sugar=14.0, carbohydrates=19.0, protein=1.7)),
        "papaya": FruitNutrition(name="papaya", nutritions=NutritionInfo(calories=43, fat=0.3, sugar=8.0, carbohydrates=11.0, protein=0.5)),
        "coconut": FruitNutrition(name="coconut", nutritions=NutritionInfo(calories=354, fat=33.0, sugar=6.2, carbohydrates=15.0, protein=3.3))
    }, description="Nutritional data mapping by fruit name")

Scenario_Schema = [Fruit, NutritionInfo, FruitNutrition, FruityviceScenario]

# Section 2: Class
class FruityviceAPI:
    def __init__(self):
        """Initialize Fruityvice API with empty state."""
        self.fruits: List[Fruit] = []
        self.fruitNutritionMap: Dict[str, FruitNutrition] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = FruityviceScenario(**scenario)
        self.fruits = model.fruits
        self.fruitNutritionMap = model.fruitNutritionMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "fruits": [fruit.model_dump() for fruit in self.fruits],
            "fruitNutritionMap": {name: nutrition.model_dump() for name, nutrition in self.fruitNutritionMap.items()}
        }

    def list_fruits(self, limit: Optional[int] = None) -> dict:
        """Retrieve a list of all available fruits."""
        if limit is not None:
            limited_fruits = self.fruits[:limit]
        else:
            limited_fruits = self.fruits
        return {"fruits": [{"name": fruit.name} for fruit in limited_fruits]}

    def get_fruit_nutrition(self, fruit_name: str) -> dict:
        """Retrieve detailed nutritional information for a specific fruit."""
        nutrition_data = self.fruitNutritionMap[fruit_name.lower()]
        return {
            "name": nutrition_data.name,
            "nutritions": {
                "calories": nutrition_data.nutritions.calories,
                "fat": nutrition_data.nutritions.fat,
                "sugar": nutrition_data.nutritions.sugar,
                "carbohydrates": nutrition_data.nutritions.carbohydrates,
                "protein": nutrition_data.nutritions.protein
            }
        }

# Section 3: MCP Tools
mcp = FastMCP(name="FruityviceServer")
api = FruityviceAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Fruityvice API.
    
    Args:
        scenario (dict): Scenario dictionary matching FruityviceScenario schema.
    
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
    Save current Fruityvice state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_fruits(limit: Optional[int] = None) -> dict:
    """
    Retrieve a list of all available fruits from the Fruityvice database.
    
    Args:
        limit (int) [Optional]: Maximum number of fruit results to return. If not specified, all available fruits are returned.
    
    Returns:
        fruits (list): List of available fruits from the Fruityvice database.
    """
    try:
        # Basic type check only - range validation (ge=0) handled by Pydantic when data passes through models
        if limit is not None and not isinstance(limit, int):
            raise ValueError("Limit must be an integer")
        return api.list_fruits(limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_fruit_nutrition(fruit_name: str) -> dict:
    """
    Retrieve detailed nutritional information for a specific fruit by name.
    
    Args:
        fruit_name (str): The common name of the fruit to look up (e.g., 'apple', 'banana', 'orange').
    
    Returns:
        name (str): The common name of the fruit.
        nutritions (dict): Nutritional breakdown of the fruit per 100 grams of edible portion.
    """
    try:
        # Business logic check: verify fruit exists (not format validation)
        if not fruit_name or not isinstance(fruit_name, str):
            raise ValueError("Fruit name must be a non-empty string")
        fruit_key = fruit_name.lower()
        if fruit_key not in api.fruitNutritionMap:
            raise ValueError(f"Fruit '{fruit_name}' not found")
        return api.get_fruit_nutrition(fruit_name)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()