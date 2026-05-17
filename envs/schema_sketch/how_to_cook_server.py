# Server: HowToCook

def get_recipe_details(recipe_id: str) -> dict:
    """
    Retrieve full details for a specific recipe by its unique identifier.
    
    Args:
        recipe_id (str): Unique identifier of the recipe.
        
    Returns:
        dict: {
            "recipe_id": str,
            "name": str,
            "description": str,
            "category": str,
            "ingredients": list[dict],
            "steps": list[str],
            "tips": list[str]
        }
    """
    pass

def list_all_categories() -> list:
    """
    List all available categories of recipes.
    
    Returns:
        list: A list of category names.
    """
    pass

def list_recipes_by_category(category: str = None) -> list:
    """
    List all recipes belonging to a specific category.
    
    Args:
        category (str): [Optional] Category name (e.g., "水产", "早餐", "荤菜", "主食"). if not provided, returns all recipes.
        
    Returns:
        list: A list of recipes, each recipe contains {
            "recipe_id": str,
            "name": str,
            "description": str
        }
    """
    pass

def recommend_meal(people_count: int, category: str = None, avoid_items: list[str] = None) -> dict:
    """
    Generate a meal recipe based on preferences and restrictions.
    
    Args:
        people_count (int): Number of people to cook for (1-10)
        category (str): [Optional] Category name (e.g., "水产", "早餐", "荤菜", "主食"). if not provided, returns all recipes.
        avoid_items (list[str]): [Optional] List of ingredients to avoid
        
    Returns:
        dict: {
            "recipe_id": str,
            "name": str,
            "description": str,
            "category": str,
            "ingredients": list[dict],
            "steps": list[str],
            "tips": list[str],
        }
    """
    pass

def get_random_dish_recommendation(people_count: int) -> dict:
    """
    Get a random combination of dishes suitable for the number of people.
    
    Args:
        people_count (int): Number of people to dine (1-10)
        
    Returns:
        dict: {
            "recipe_id": str,
            "name": str,
            "description": str,
            "category": str,
            "ingredients": list[dict],
            "steps": list[str],
            "tips": list[str],
        }
    """
    pass

