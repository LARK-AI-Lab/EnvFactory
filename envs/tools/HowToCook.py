from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import random

# Section 1: Schema
class Ingredient(BaseModel):
    """Represents a recipe ingredient."""
    name: str = Field(..., description="Name of the ingredient")
    amount: str = Field(..., description="Quantity of the ingredient")

class Recipe(BaseModel):
    """Represents a complete recipe."""
    recipe_id: str = Field(..., description="Unique identifier for the recipe", pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., description="Display name of the recipe")
    description: str = Field(..., description="Short summary describing the dish")
    category: str = Field(..., description="Category of the recipe")
    ingredients: List[Ingredient] = Field(default=[], description="List of ingredients required")
    steps: List[str] = Field(default=[], description="Ordered cooking instructions")
    tips: List[str] = Field(default=[], description="Helpful cooking tips")

class CookingScenario(BaseModel):
    """Main scenario model for cooking assistant."""
    recipes: Dict[str, Recipe] = Field(default={
        "tomato_egg": Recipe(
            recipe_id="tomato_egg",
            name="Tomato Scrambled Eggs",
            description="A classic Chinese home-style dish with eggs and tomatoes",
            category="Home Cooking",
            ingredients=[
                Ingredient(name="Eggs", amount="3 pieces"),
                Ingredient(name="Tomatoes", amount="2 medium"),
                Ingredient(name="Green onion", amount="1 stalk"),
                Ingredient(name="Salt", amount="1 tsp"),
                Ingredient(name="Sugar", amount="1/2 tsp"),
                Ingredient(name="Cooking oil", amount="2 tbsp")
            ],
            steps=[
                "Beat the eggs with a pinch of salt",
                "Cut tomatoes into wedges",
                "Heat oil in a wok, scramble the eggs until set, then remove",
                "Add more oil, stir-fry tomatoes until soft",
                "Add eggs back, season with salt and sugar",
                "Garnish with green onion and serve"
            ],
            tips=[
                "Don't overcook the eggs - keep them tender",
                "Add a little sugar to balance the tomato acidity"
            ]
        ),
        "kung_pao_chicken": Recipe(
            recipe_id="kung_pao_chicken",
            name="Kung Pao Chicken",
            description="Spicy Sichuan dish with chicken, peanuts, and chili",
            category="Sichuan Cuisine",
            ingredients=[
                Ingredient(name="Chicken breast", amount="300g"),
                Ingredient(name="Peanuts", amount="50g"),
                Ingredient(name="Dried chili", amount="10 pieces"),
                Ingredient(name="Sichuan peppercorn", amount="1 tsp"),
                Ingredient(name="Green onion", amount="2 stalks"),
                Ingredient(name="Ginger", amount="1 tbsp"),
                Ingredient(name="Garlic", amount="3 cloves"),
                Ingredient(name="Soy sauce", amount="2 tbsp"),
                Ingredient(name="Vinegar", amount="1 tbsp"),
                Ingredient(name="Sugar", amount="1 tsp")
            ],
            steps=[
                "Dice chicken and marinate with soy sauce and cornstarch",
                "Fry peanuts until golden and set aside",
                "Stir-fry dried chilies and Sichuan peppercorn until fragrant",
                "Add chicken and stir-fry until cooked",
                "Add sauce mixture and toss to coat",
                "Mix in peanuts and green onions, serve hot"
            ],
            tips=[
                "Adjust chili amount based on spice preference",
                "Don't burn the chilies - keep heat medium"
            ]
        ),
        "mapo_tofu": Recipe(
            recipe_id="mapo_tofu",
            name="Mapo Tofu",
            description="Spicy tofu dish with minced pork in chili bean sauce",
            category="Sichuan Cuisine",
            ingredients=[
                Ingredient(name="Soft tofu", amount="400g"),
                Ingredient(name="Ground pork", amount="100g"),
                Ingredient(name="Doubanjiang", amount="2 tbsp"),
                Ingredient(name="Sichuan peppercorn", amount="1 tsp"),
                Ingredient(name="Chili oil", amount="1 tbsp"),
                Ingredient(name="Garlic", amount="3 cloves"),
                Ingredient(name="Ginger", amount="1 tbsp"),
                Ingredient(name="Green onion", amount="2 stalks"),
                Ingredient(name="Chicken stock", amount="200ml")
            ],
            steps=[
                "Cut tofu into 2cm cubes and blanch in salted water",
                "Fry ground pork until crispy, then add doubanjiang",
                "Add garlic, ginger, and aromatics",
                "Pour in stock and gently add tofu",
                "Simmer for 5 minutes, thicken with cornstarch slurry",
                "Sprinkle with Sichuan peppercorn powder and green onion"
            ],
            tips=[
                "Use soft tofu for authentic texture",
                "Be gentle when stirring to avoid breaking tofu"
            ]
        ),
        "fried_rice": Recipe(
            recipe_id="fried_rice",
            name="Egg Fried Rice",
            description="Simple and delicious fried rice with egg and vegetables",
            category="Home Cooking",
            ingredients=[
                Ingredient(name="Cooked rice", amount="2 bowls"),
                Ingredient(name="Eggs", amount="2 pieces"),
                Ingredient(name="Green peas", amount="1/4 cup"),
                Ingredient(name="Carrot", amount="1/4 cup diced"),
                Ingredient(name="Green onion", amount="2 stalks"),
                Ingredient(name="Soy sauce", amount="1 tbsp"),
                Ingredient(name="Sesame oil", amount="1 tsp"),
                Ingredient(name="Cooking oil", amount="2 tbsp")
            ],
            steps=[
                "Break up cold rice into separate grains",
                "Scramble eggs and set aside",
                "Stir-fry vegetables until tender",
                "Add rice and toss with high heat",
                "Add eggs and season with soy sauce",
                "Drizzle with sesame oil and serve"
            ],
            tips=[
                "Use day-old rice for best texture",
                "Keep the heat high for wok hei flavor"
            ]
        ),
        "sweet_sour_pork": Recipe(
            recipe_id="sweet_sour_pork",
            name="Sweet and Sour Pork",
            description="Crispy pork with tangy sweet and sour sauce",
            category="Cantonese Cuisine",
            ingredients=[
                Ingredient(name="Pork tenderloin", amount="300g"),
                Ingredient(name="Bell pepper", amount="1 piece"),
                Ingredient(name="Pineapple", amount="1/2 cup"),
                Ingredient(name="Onion", amount="1/2 piece"),
                Ingredient(name="Ketchup", amount="3 tbsp"),
                Ingredient(name="Vinegar", amount="2 tbsp"),
                Ingredient(name="Sugar", amount="3 tbsp"),
                Ingredient(name="Cornstarch", amount="1/2 cup"),
                Ingredient(name="Egg", amount="1 piece")
            ],
            steps=[
                "Cut pork into bite-sized pieces and marinate",
                "Coat pork with egg and cornstarch batter",
                "Deep-fry pork until golden and crispy",
                "Stir-fry vegetables and pineapple",
                "Make sauce with ketchup, vinegar, and sugar",
                "Toss pork in sauce and serve immediately"
            ],
            tips=[
                "Fry pork twice for extra crispiness",
                "Serve immediately to maintain crunch"
            ]
        )
    }, description="All available recipes")
    categories: List[str] = Field(default=["Home Cooking", "Sichuan Cuisine", "Cantonese Cuisine"], description="Available recipe categories")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducible recommendations")
    people_count: int = Field(default=2, ge=1, le=10, description="Number of people to cook for (range 1-10)")

Scenario_Schema = [Ingredient, Recipe, CookingScenario]

# Section 2: Class
class HowToCookAPI:
    def __init__(self):
        """Initialize cooking API with empty state."""
        self.recipes: Dict[str, Recipe] = {}
        self.categories: List[str] = []
        self.random_seed: Optional[int] = None
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = CookingScenario(**scenario)
        self.recipes = model.recipes
        self.categories = model.categories
        self.random_seed = model.random_seed
        if self.random_seed is not None:
            random.seed(self.random_seed)

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "recipes": {recipe_id: recipe.model_dump() for recipe_id, recipe in self.recipes.items()},
            "categories": self.categories,
            "random_seed": self.random_seed
        }

    def _recipe_to_dict(self, recipe: Recipe, include_full_details: bool = True) -> dict:
        """
        Convert a Recipe object to dictionary format.
        
        Args:
            recipe: The Recipe object to convert.
            include_full_details: If True, include all fields; if False, include only basic info.
        
        Returns:
            Dictionary representation of the recipe.
        """
        base_dict = {
            "recipe_id": recipe.recipe_id,
            "name": recipe.name,
            "description": recipe.description
        }
        
        if include_full_details:
            base_dict.update({
                "category": recipe.category,
                "ingredients": [ingredient.model_dump() for ingredient in recipe.ingredients],
                "steps": recipe.steps,
                "tips": recipe.tips
            })
        
        return base_dict

    def get_recipe_details(self, recipe_id: str) -> dict:
        """Retrieve full details for a specific recipe."""
        if recipe_id not in self.recipes:
            return {
                "error": f"Recipe '{recipe_id}' not found",
                "available_recipes": list(self.recipes.keys())
            }
        
        recipe = self.recipes[recipe_id]
        return self._recipe_to_dict(recipe, include_full_details=True)

    def list_all_categories(self) -> dict:
        """List all available recipe categories."""
        return {"categories": self.categories}

    def list_recipes_by_category(self, category: Optional[str] = None) -> dict:
        """List recipes filtered by category."""
        filtered_recipes = []
        
        if category:
            recipes = [recipe for recipe in self.recipes.values() if recipe.category == category]
        else:
            recipes = list(self.recipes.values())
            
        for recipe in recipes:
            filtered_recipes.append(self._recipe_to_dict(recipe, include_full_details=False))
            
        return {"recipes": filtered_recipes}

    def recommend_meal(self, people_count: int, category: Optional[str] = None, avoid_items: Optional[List[str]] = None) -> dict:
        """Generate personalized meal recommendation."""
        if avoid_items is None:
            avoid_items = []
            
        candidates = []
        for recipe in self.recipes.values():
            if category and recipe.category != category:
                continue
                
            # Check if recipe contains avoided ingredients
            recipe_ingredients = [ing.name.lower() for ing in recipe.ingredients]
            has_avoided = any(avoid_item.lower() in " ".join(recipe_ingredients) for avoid_item in avoid_items)
            
            if not has_avoided:
                candidates.append(recipe)
                
        if not candidates:
            # Return any recipe if no matches found
            candidates = list(self.recipes.values())
            
        selected = random.choice(candidates)
        
        return self._recipe_to_dict(selected, include_full_details=True)

    def get_random_dish_recommendation(self, people_count: int) -> dict:
        """Get random dish recommendation."""
        selected = random.choice(list(self.recipes.values()))
        
        return self._recipe_to_dict(selected, include_full_details=True)

# Section 3: MCP Tools
mcp = FastMCP(name="HowToCook")
api = HowToCookAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the cooking API.
    
    Args:
        scenario (dict): Scenario dictionary matching CookingScenario schema.
    
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
    Save current cooking state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_recipe_details(recipe_id: str) -> dict:
    """
    Retrieve full details for a specific recipe by its unique identifier.
    
    Args:
        recipe_id (str): The unique identifier of the recipe.
    
    Returns:
        recipe_id (str): The unique identifier of the recipe.
        name (str): The display name of the recipe.
        description (str): A short summary describing the dish.
        category (str): The category to which the recipe belongs.
        ingredients (list): List of ingredient objects required for the recipe.
        steps (list): Ordered list of cooking instructions.
        tips (list): Helpful cooking tips or variations.
    """
    try:
        result = api.get_recipe_details(recipe_id)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def list_all_categories() -> dict:
    """
    List all available categories of recipes.
    
    Returns:
        categories (list): List of all category names available.
    """
    try:
        return api.list_all_categories()
    except Exception as e:
        raise e

@mcp.tool()
def list_recipes_by_category(category: Optional[str] = None) -> dict:
    """
    List all recipes belonging to a specific category.
    
    Args:
        category (str) [Optional]: The category name to filter recipes.
    
    Returns:
        recipes (list): List of recipes matching the specified category.
    """
    try:
        return api.list_recipes_by_category(category)
    except Exception as e:
        raise e

@mcp.tool()
def recommend_meal(people_count: int, category: Optional[str] = None, avoid_items: Optional[List[str]] = None) -> dict:
    """
    Generate personalized meal recommendation based on preferences.
    
    Args:
        people_count (int): The number of people to cook for (range 1-10).
        category (str) [Optional]: Preferred category to narrow recommendations.
        avoid_items (list) [Optional]: List of ingredient names to exclude.
    
    Returns:
        recipe_id (str): The unique identifier of the recommended recipe.
        name (str): The display name of the recipe.
        description (str): A short summary describing the dish.
        category (str): The category of the recipe.
        ingredients (list): List of ingredient objects required.
        steps (list): Ordered list of cooking instructions.
        tips (list): Helpful cooking tips or variations.
    """
    try:
        return api.recommend_meal(people_count, category, avoid_items)
    except Exception as e:
        raise e

@mcp.tool()
def get_random_dish_recommendation(people_count: int) -> dict:
    """
    Get a random dish recommendation suitable for the number of diners.
    
    Args:
        people_count (int): The number of people to dine (range 1-10).
    
    Returns:
        recipe_id (str): The unique identifier of the recommended recipe.
        name (str): The display name of the recipe.
        description (str): A short summary describing the dish.
        category (str): The category of the recipe.
        ingredients (list): List of ingredient objects required.
        steps (list): Ordered list of cooking instructions.
        tips (list): Helpful cooking tips or variations.
    """
    try:
        return api.get_random_dish_recommendation(people_count)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
