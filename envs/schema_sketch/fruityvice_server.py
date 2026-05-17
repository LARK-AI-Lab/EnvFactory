# Server: Fruityvice

def list_fruits(limit: int = None) -> list:
    """
    List all available fruits from Fruityvice API.
    
    Args:
        limit (int): [Optional] Maximum number of results to return
        
    Returns:
        list: Each fruit contains {
            "name": str
        }
    """
    pass

def get_fruit_nutrition(fruit_name: str) -> dict:
    """
    Get nutrition information and details for a specific fruit.
    
    Args:
        fruit_name (str): Name of the fruit (e.g., "apple", "banana", "orange")
        
    Returns:
        dict: {
            "name": str,
            "nutritions": {
                "calories": float,  # Unit: kcal per 100g
                "fat": float,  # Unit: grams per 100g
                "sugar": float,  # Unit: grams per 100g
                "carbohydrates": float,  # Unit: grams per 100g
                "protein": float  # Unit: grams per 100g
            }
        }
    """
    pass




