# Data Source: https://platform.fatsecret.com/platform-api
# Server: FatSecret
# Category: Health / Nutrition


def search_foods(query: str, region: str = "US", language: str = "en") -> list:
    """
    Search for foods in the comprehensive nutrition database.
    
    Args:
        query (str): Food name or keyword to search
        region (str): [Optional] Country code for localized results (default: "US")
        language (str): [Optional] Language code for results (default: "en")
        
    Returns:
        list: Each food contains {
            "food_id": str,
            "food_name": str,
            "food_type": str,        # "Generic", "Brand", "Restaurant"
            "brand_name": str,       # For branded foods
            "food_url": str,         # URL to food details
            "food_description": str  # Brief description with calories
        }
    """
    pass


def get_food_details(food_id: str) -> dict:
    """
    Get detailed nutrition information for a specific food.
    
    Args:
        food_id (str): Unique food identifier
        
    Returns:
        dict: {
            "food_id": str,
            "food_name": str,
            "servings": list,        # Available serving sizes
            "nutrition": {           # Per serving
                "calories": float,
                "protein": float,
                "carbs": float,
                "fat": float,
                "fiber": float,
                "sugar": float,
                "sodium": float,
                "cholesterol": float,
                "vitamins": dict,    # Vitamin and mineral content
                "allergens": list    # Contains allergens like "gluten", "dairy"
            },
            "dietary_preferences": { # Dietary flags
                "is_vegan": bool,
                "is_vegetarian": bool,
                "is_gluten_free": bool
            },
            "images": list           # URLs to food images in various sizes
        }
    """
    pass


def search_by_barcode(barcode: str, region: str = "US") -> dict:
    """
    Look up food/product information by UPC/EAN barcode.
    Database covers 90%+ of global barcodes.
    
    Args:
        barcode (str): UPC or EAN barcode number
        region (str): [Optional] Country code for localized results
        
    Returns:
        dict: {
            "food_id": str,
            "food_name": str,
            "brand": str,
            "package_size": str,
            "nutrition_per_serving": dict,
            "ingredients": str,      # Full ingredients list
            "allergen_info": str,    # Allergen warnings
            "country": str
        }
    """
    pass


def analyze_food_image(image_path: str) -> dict:
    """
    Analyze a food image and return nutrition information.
    Uses AI to detect food items, estimate portion sizes.
    
    Args:
        image_path (str): Path to food image file
        
    Returns:
        dict: {
            "detected_foods": list,  # Foods identified in image
            "estimated_weight_g": float,
            "confidence": float,     # AI confidence score
            "nutrition_estimate": dict,
            "suggestions": list      # Similar foods for confirmation
        }
    """
    pass


def search_recipes(query: str, diet: str = None, max_calories: int = None) -> list:
    """
    Search for recipes with nutrition information.
    
    Args:
        query (str): Recipe name or ingredient to search
        diet (str): [Optional] Diet filter: "vegan", "vegetarian", "gluten_free", "keto"
        max_calories (int): [Optional] Maximum calories per serving
        
    Returns:
        list: Each recipe contains {
            "recipe_id": str,
            "recipe_name": str,
            "recipe_description": str,
            "prep_time": str,
            "cook_time": str,
            "servings": int,
            "rating": float,
            "images": list,
            "ingredients": list,
            "directions": list,
            "nutrition_per_serving": dict
        }
    """
    pass


def get_recipe_details(recipe_id: str) -> dict:
    """
    Get full recipe details including ingredients and cooking instructions.
    
    Args:
        recipe_id (str): Unique recipe identifier
        
    Returns:
        dict: {
            "recipe_id": str,
            "recipe_name": str,
            "recipe_description": str,
            "prep_time_minutes": int,
            "cook_time_minutes": int,
            "servings": int,
            "difficulty": str,
            "ingredients": list,     # Each with quantity, unit, and food
            "directions": list,      # Step-by-step instructions
            "nutrition_per_serving": {
                "calories": float,
                "protein": float,
                "carbs": float,
                "fat": float
            },
            "categories": list,      # Recipe categories
            "images": list
        }
    """
    pass
