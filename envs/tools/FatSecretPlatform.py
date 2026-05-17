
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class FoodItem(BaseModel):
    """Represents a food item in search results."""
    food_id: str = Field(..., description="Unique identifier of the food item")
    food_name: str = Field(..., description="Display name of the food item")
    food_type: str = Field(..., description="Classification: Generic, Brand, or Restaurant")
    brand_name: Optional[str] = Field(default=None, description="Brand or manufacturer name")
    food_url: str = Field(..., description="URL to full food details page")
    food_description: str = Field(..., description="Brief nutritional summary")

class Serving(BaseModel):
    """Represents a serving size."""
    serving_description: str = Field(..., description="Description of serving size")
    metric_serving_amount: Optional[float] = Field(default=None, description="Amount in metric units")
    metric_serving_unit: Optional[str] = Field(default=None, description="Metric unit")

class Nutrition(BaseModel):
    """Nutritional information."""
    calories: float = Field(..., ge=0, description="Energy in kcal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    fiber: Optional[float] = Field(default=None, ge=0, description="Fiber in grams")
    sugar: Optional[float] = Field(default=None, ge=0, description="Sugar in grams")
    sodium: Optional[float] = Field(default=None, ge=0, description="Sodium in mg")
    cholesterol: Optional[float] = Field(default=None, ge=0, description="Cholesterol in mg")
    vitamins: Dict[str, Any] = Field(default={}, description="Vitamin content")
    allergens: List[str] = Field(default=[], description="List of allergens")

class DietaryPreferences(BaseModel):
    """Dietary classification flags."""
    is_vegan: bool = Field(default=False, description="No animal products")
    is_vegetarian: bool = Field(default=False, description="No meat or fish")
    is_gluten_free: bool = Field(default=False, description="No gluten")

class FoodDetails(BaseModel):
    """Detailed food information."""
    food_id: str = Field(..., description="Unique identifier")
    food_name: str = Field(..., description="Display name")
    servings: List[Dict[str, Any]] = Field(default=[], description="Available serving sizes")
    nutrition: Nutrition = Field(..., description="Nutritional information")
    dietary_preferences: DietaryPreferences = Field(..., description="Dietary flags")
    images: List[str] = Field(default=[], description="Image URLs")

class BarcodeResult(BaseModel):
    """Barcode lookup result."""
    food_id: str = Field(..., description="Unique identifier")
    food_name: str = Field(..., description="Display name")
    brand: str = Field(..., description="Brand name")
    package_size: str = Field(..., description="Package size")
    nutrition_per_serving: Dict[str, Any] = Field(default={}, description="Nutrition info")
    ingredients: str = Field(..., description="Ingredients list")
    allergen_info: str = Field(..., description="Allergen warnings")
    country: str = Field(..., description="Country of manufacture")

class ImageAnalysis(BaseModel):
    """Food image analysis result."""
    detected_foods: List[str] = Field(..., description="Detected food items")
    estimated_weight_g: float = Field(..., ge=0, description="Estimated weight in grams")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")
    nutrition_estimate: Dict[str, Any] = Field(default={}, description="Estimated nutrition")
    suggestions: List[str] = Field(default=[], description="Alternative suggestions")

class Ingredient(BaseModel):
    """Recipe ingredient."""
    quantity: float = Field(..., ge=0, description="Amount")
    unit: str = Field(..., description="Unit of measurement")
    food: str = Field(..., description="Food item name")

class Recipe(BaseModel):
    """Recipe information."""
    recipe_id: str = Field(..., description="Unique identifier")
    recipe_name: str = Field(..., description="Recipe title")
    recipe_description: str = Field(..., description="Brief summary")
    prep_time: Optional[str] = Field(default=None, description="Prep time")
    cook_time: Optional[str] = Field(default=None, description="Cook time")
    servings: int = Field(..., ge=1, description="Number of servings")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="User rating")
    images: List[str] = Field(default=[], description="Recipe images")
    ingredients: List[Dict[str, Any]] = Field(default=[], description="Ingredient list")
    directions: List[str] = Field(default=[], description="Cooking instructions")
    nutrition_per_serving: Dict[str, Any] = Field(default={}, description="Nutrition per serving")

class RecipeDetails(BaseModel):
    """Detailed recipe information."""
    recipe_id: str = Field(..., description="Unique identifier")
    recipe_name: str = Field(..., description="Recipe title")
    recipe_description: str = Field(..., description="Brief summary")
    prep_time_minutes: int = Field(..., ge=0, description="Prep time in minutes")
    cook_time_minutes: int = Field(..., ge=0, description="Cook time in minutes")
    servings: int = Field(..., ge=1, description="Number of servings")
    difficulty: str = Field(..., description="Difficulty level")
    ingredients: List[Ingredient] = Field(..., description="Ingredients with quantities")
    directions: List[str] = Field(..., description="Cooking instructions")
    nutrition_per_serving: Dict[str, Any] = Field(..., description="Nutrition per serving")
    categories: List[str] = Field(default=[], description="Recipe tags")
    images: List[str] = Field(default=[], description="Recipe images")

class FatSecretScenario(BaseModel):
    """Main scenario model for FatSecret platform."""
    foods: Dict[str, FoodDetails] = Field(default={}, description="Food database")
    barcode_lookup: Dict[str, BarcodeResult] = Field(default={}, description="Barcode database")
    recipes: Dict[str, RecipeDetails] = Field(default={}, description="Recipe database")
    image_analysis_results: Dict[str, ImageAnalysis] = Field(default={}, description="Image analysis cache")

Scenario_Schema = [FoodItem, Serving, Nutrition, DietaryPreferences, FoodDetails, BarcodeResult, ImageAnalysis, Ingredient, Recipe, RecipeDetails, FatSecretScenario]

# Section 2: Class
class FatSecretAPI:
    def __init__(self):
        """Initialize FatSecret API with empty state."""
        self.foods: Dict[str, FoodDetails] = {}
        self.barcode_lookup: Dict[str, BarcodeResult] = {}
        self.recipes: Dict[str, RecipeDetails] = {}
        self.image_analysis_results: Dict[str, ImageAnalysis] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = FatSecretScenario(**scenario)
        self.foods = model.foods
        self.barcode_lookup = model.barcode_lookup
        self.recipes = model.recipes
        self.image_analysis_results = model.image_analysis_results

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "foods": {fid: food.model_dump() for fid, food in self.foods.items()},
            "barcode_lookup": {bc: result.model_dump() for bc, result in self.barcode_lookup.items()},
            "recipes": {rid: recipe.model_dump() for rid, recipe in self.recipes.items()},
            "image_analysis_results": {path: result.model_dump() for path, result in self.image_analysis_results.items()}
        }

    def search_foods(self, query: str, region: str, language: str) -> dict:
        """Search foods by query string."""
        results = []
        for food_id, food in self.foods.items():
            if query.lower() in food.food_name.lower():
                results.append({
                    "food_id": food.food_id,
                    "food_name": food.food_name,
                    "food_type": "Generic",
                    "brand_name": None,
                    "food_url": f"https://fatsecret.com/food/{food_id}",
                    "food_description": f"Per serving: {food.nutrition.calories} calories"
                })
        return {"foods": results}

    def get_food_details(self, food_id: str) -> dict:
        """Retrieve detailed food information."""
        food = self.foods[food_id]
        return {
            "food_id": food.food_id,
            "food_name": food.food_name,
            "servings": food.servings,
            "nutrition": food.nutrition.model_dump(),
            "dietary_preferences": food.dietary_preferences.model_dump(),
            "images": food.images
        }

    def search_by_barcode(self, barcode: str, region: str) -> dict:
        """Look up food by barcode."""
        result = self.barcode_lookup[barcode]
        return result.model_dump()

    def analyze_food_image(self, image_path: str) -> dict:
        """Analyze food image."""
        result = self.image_analysis_results[image_path]
        return result.model_dump()

    def search_recipes(self, query: str, diet: Optional[str], max_calories: Optional[int]) -> dict:
        """Search recipes with filters."""
        results = []
        for recipe_id, recipe in self.recipes.items():
            if query.lower() in recipe.recipe_name.lower():
                nutrition = recipe.nutrition_per_serving
                if max_calories and nutrition.get("calories", 0) > max_calories:
                    continue
                results.append({
                    "recipe_id": recipe.recipe_id,
                    "recipe_name": recipe.recipe_name,
                    "recipe_description": recipe.recipe_description,
                    "prep_time": f"{recipe.prep_time_minutes} min",
                    "cook_time": f"{recipe.cook_time_minutes} min",
                    "servings": recipe.servings,
                    "rating": 4.5,
                    "images": recipe.images,
                    "ingredients": [ing.model_dump() for ing in recipe.ingredients],
                    "directions": recipe.directions,
                    "nutrition_per_serving": recipe.nutrition_per_serving
                })
        return {"recipes": results}

    def get_recipe_details(self, recipe_id: str) -> dict:
        """Retrieve detailed recipe information."""
        recipe = self.recipes[recipe_id]
        return recipe.model_dump()

# Section 3: MCP Tools
mcp = FastMCP(name="FatSecretPlatform")
api = FatSecretAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the FatSecret API.

    Args:
        scenario (dict): Scenario dictionary matching FatSecretScenario schema.

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
    Save current FatSecret state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_foods(query: str, region: str = "US", language: str = "en") -> dict:
    """
    Search the nutrition database for foods by name or keyword.

    Args:
        query (str): Search query string to match against food names.
        region (str): [Optional] ISO 3166-1 alpha-2 country code (default: 'US').
        language (str): [Optional] ISO 639-1 language code (default: 'en').

    Returns:
        foods (array): List of food items matching the search criteria.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_foods(query, region, language)
    except Exception as e:
        raise e

@mcp.tool()
def get_food_details(food_id: str) -> dict:
    """
    Retrieve detailed nutritional information for a specific food item.

    Args:
        food_id (str): Unique identifier of the food item.

    Returns:
        food_id (str): Unique identifier of the food item.
        food_name (str): Display name of the food item.
        servings (array): List of available serving sizes.
        nutrition (object): Detailed nutritional information per serving.
        dietary_preferences (object): Dietary classification flags.
        images (array): URLs to food images.
    """
    try:
        if not food_id or not isinstance(food_id, str):
            raise ValueError("Food ID must be a non-empty string")
        if food_id not in api.foods:
            raise ValueError(f"Food {food_id} not found")
        return api.get_food_details(food_id)
    except Exception as e:
        raise e

@mcp.tool()
def search_by_barcode(barcode: str, region: str = "US") -> dict:
    """
    Look up food and product information using a barcode number.

    Args:
        barcode (str): UPC or EAN barcode number to look up.
        region (str): [Optional] ISO 3166-1 alpha-2 country code (default: 'US').

    Returns:
        food_id (str): Unique identifier of the food item.
        food_name (str): Display name of the food item.
        brand (str): Brand or manufacturer name.
        package_size (str): Net weight or volume of the package.
        nutrition_per_serving (object): Nutritional information per serving.
        ingredients (str): Complete list of ingredients.
        allergen_info (str): Allergen warnings and advisory statements.
        country (str): Country of manufacture or primary market.
    """
    try:
        if not barcode or not isinstance(barcode, str):
            raise ValueError("Barcode must be a non-empty string")
        if barcode not in api.barcode_lookup:
            raise ValueError(f"Barcode {barcode} not found")
        return api.search_by_barcode(barcode, region)
    except Exception as e:
        raise e

@mcp.tool()
def analyze_food_image(image_path: str) -> dict:
    """
    Analyze a food image using AI to detect food items and estimate nutrition.

    Args:
        image_path (str): File system path to the food image.

    Returns:
        detected_foods (array): List of food items identified by AI.
        estimated_weight_g (number): Estimated total weight in grams.
        confidence (number): AI confidence score (0.0 to 1.0).
        nutrition_estimate (object): Estimated nutritional content.
        suggestions (array): Alternative food suggestions when confidence is low.
    """
    try:
        if not image_path or not isinstance(image_path, str):
            raise ValueError("Image path must be a non-empty string")
        if image_path not in api.image_analysis_results:
            raise ValueError(f"Image analysis for {image_path} not found")
        return api.analyze_food_image(image_path)
    except Exception as e:
        raise e

@mcp.tool()
def search_recipes(query: str, diet: Optional[str] = None, max_calories: Optional[int] = None) -> dict:
    """
    Search for recipes with optional filtering by dietary preferences and calories.

    Args:
        query (str): Search query string to match against recipe names.
        diet (str): [Optional] Dietary filter: 'vegan', 'vegetarian', 'gluten_free', or 'keto'.
        max_calories (int): [Optional] Maximum calories per serving.

    Returns:
        recipes (array): List of recipes matching the search and filter criteria.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_recipes(query, diet, max_calories)
    except Exception as e:
        raise e

@mcp.tool()
def get_recipe_details(recipe_id: str) -> dict:
    """
    Retrieve complete recipe information including ingredients and instructions.

    Args:
        recipe_id (str): Unique identifier of the recipe.

    Returns:
        recipe_id (str): Unique identifier of the recipe.
        recipe_name (str): Title of the recipe.
        recipe_description (str): Brief summary describing the recipe.
        prep_time_minutes (int): Preparation time in minutes.
        cook_time_minutes (int): Cooking time in minutes.
        servings (int): Number of servings the recipe produces.
        difficulty (str): Difficulty level of the recipe.
        ingredients (array): List of ingredients with quantities and units.
        directions (array): Ordered list of cooking instructions.
        nutrition_per_serving (object): Nutritional information per serving.
        categories (array): Recipe classifications and tags.
        images (array): URLs to recipe images.
    """
    try:
        if not recipe_id or not isinstance(recipe_id, str):
            raise ValueError("Recipe ID must be a non-empty string")
        if recipe_id not in api.recipes:
            raise ValueError(f"Recipe {recipe_id} not found")
        return api.get_recipe_details(recipe_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
