from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class User(BaseModel):
    """Represents a user account."""
    user_id: str = Field(..., description="Unique identifier for the customer account")
    name: Dict[str, str] = Field(..., description="User's name details including first and last name")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Registered email address")
    address: Dict[str, str] = Field(..., description="User's default shipping address")
    payment_methods: List[str] = Field(default=[], description="List of payment methods registered to the user")
    order_ids: List[str] = Field(default=[], description="List of order identifiers associated with the user")
    zip_code: str = Field(..., pattern=r"^\d{5}$", description="Five-digit postal zip code")

class Product(BaseModel):
    """Represents a product type."""
    product_id: str = Field(..., description="Unique identifier for the product type")
    name: str = Field(..., description="Display name of the product")
    description: str = Field(..., description="Detailed description of the product")
    item_ids: List[str] = Field(default=[], description="List of item identifiers for this product")

class OrderItem(BaseModel):
    """Represents an item in an order."""
    item_id: str = Field(..., description="Unique identifier for the item")
    product_id: str = Field(..., description="Product type identifier")
    status: str = Field(default="normal", description="Item status (normal, returned, exchanged)")

class Order(BaseModel):
    """Represents an order."""
    order_id: str = Field(..., pattern=r"^#\w+$", description="Unique order identifier with # prefix")
    user_id: str = Field(..., description="User who placed the order")
    status: str = Field(..., description="Current status of the order")
    items: List[OrderItem] = Field(default=[], description="List of items in the order")
    total_amount: float = Field(..., ge=0, description="Total monetary amount of the order")
    address: Dict[str, str] = Field(..., description="Shipping address for the order")

class RetailScenario(BaseModel):
    """Main scenario model for retail e-commerce system."""
    users: Dict[str, User] = Field(default={}, description="User accounts indexed by user_id")
    products: Dict[str, Product] = Field(default={}, description="Product catalog indexed by product_id")
    orders: Dict[str, Order] = Field(default={}, description="Orders indexed by order_id")
    valid_cancellation_reasons: List[str] = Field(default=[
        "Changed my mind", "Found better price", "No longer needed", "Ordered by mistake",
        "Shipping too slow", "Product unavailable", "Payment issues", "Address incorrect"
    ], description="Valid cancellation reasons")
    payment_methods: List[str] = Field(default=[
        "credit_card", "paypal", "alipay", "wechat_pay"
    ], description="Supported payment methods")

Scenario_Schema = [User, Product, OrderItem, Order, RetailScenario]

# Section 2: Class
class RetailAPI:
    def __init__(self):
        """Initialize retail API with empty state."""
        self.users: Dict[str, User] = {}
        self.products: Dict[str, Product] = {}
        self.orders: Dict[str, Order] = {}
        self.valid_cancellation_reasons: List[str] = []
        self.payment_methods: List[str] = []

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = RetailScenario(**scenario)
        self.users = model.users
        self.products = model.products
        self.orders = model.orders
        self.valid_cancellation_reasons = model.valid_cancellation_reasons
        self.payment_methods = model.payment_methods

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "users": {user_id: user.model_dump() for user_id, user in self.users.items()},
            "products": {product_id: product.model_dump() for product_id, product in self.products.items()},
            "orders": {order_id: order.model_dump() for order_id, order in self.orders.items()},
            "valid_cancellation_reasons": self.valid_cancellation_reasons,
            "payment_methods": self.payment_methods
        }

    def find_user_by_email(self, email: str) -> dict:
        """Find user by email address."""
        for user in self.users.values():
            if user.email == email:
                return {
                    "user_id": user.user_id,
                    "name": f"{user.name['first']} {user.name['last']}",
                    "email": user.email,
                    "zip_code": user.zip_code
                }
        return {}

    def find_user_by_name_zip(self, first_name: str, last_name: str, zip_code: str) -> dict:
        """Find user by name and zip code."""
        for user in self.users.values():
            if (user.name['first'] == first_name and 
                user.name['last'] == last_name and 
                user.zip_code == zip_code):
                return {
                    "user_id": user.user_id,
                    "name": f"{user.name['first']} {user.name['last']}",
                    "email": user.email,
                    "zip_code": user.zip_code
                }
        return {}

    def get_user_details(self, user_id: str) -> dict:
        """Get comprehensive user profile."""
        user = self.users[user_id]
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "address": user.address,
            "payment_methods": user.payment_methods,
            "zip_code": user.zip_code,
            "order_ids": user.order_ids
        }

    def modify_user_address(self, user_id: str, address: str, city: str, state: str, country: str, zip_code: str) -> dict:
        """Update user's default shipping address."""
        user = self.users[user_id]
        user.address = {
            "street": address,
            "city": city,
            "state": state,
            "country": country
        }
        user.zip_code = zip_code
        return {
            "user_id": user_id,
            "updated_address": user.address
        }

    def list_product_types(self) -> dict:
        """List all available product types."""
        products = []
        for product in self.products.values():
            products.append({
                "product_id": product.product_id,
                "name": product.name
            })
        return {"products": products}

    def get_product_details(self, product_id: str) -> dict:
        """Get detailed product information."""
        product = self.products[product_id]
        return {
            "name": product.name,
            "description": product.description,
            "item_ids": product.item_ids
        }

    def get_order_details(self, order_id: str) -> dict:
        """Get order status and details."""
        order = self.orders[order_id]
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "item_ids": [item.item_id for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def modify_pending_order_address(self, order_id: str, address: str, city: str, state: str, country: str, zip_code: str) -> dict:
        """Change shipping address for pending order."""
        order = self.orders[order_id]
        if order.status != "pending":
            raise ValueError("Order is not in pending status")
        order.address = {
            "street": address,
            "city": city,
            "state": state,
            "country": country,
            "zip_code": zip_code
        }
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "item_ids": [item.item_id for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def modify_pending_order_items(self, order_id: str, item_ids: List[str], new_item_ids: List[str], payment_method: str) -> dict:
        """Swap items in pending order."""
        order = self.orders[order_id]
        if order.status != "pending":
            raise ValueError("Order is not in pending status")
        if payment_method not in self.payment_methods:
            raise ValueError("Invalid payment method")
        
        # Remove old items
        order.items = [item for item in order.items if item.item_id not in item_ids]
        
        # Add new items (assuming same product for simplicity)
        for new_item_id in new_item_ids:
            # Find product_id for new item (simplified)
            product_id = "unknown"
            for product in self.products.values():
                if new_item_id in product.item_ids:
                    product_id = product.product_id
                    break
            order.items.append(OrderItem(item_id=new_item_id, product_id=product_id))
        
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "items": [{"item_id": item.item_id, "product_id": item.product_id, "status": item.status} for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def modify_pending_order_payment(self, order_id: str, payment_method: str) -> dict:
        """Update payment method for pending order."""
        order = self.orders[order_id]
        if order.status != "pending":
            raise ValueError("Order is not in pending status")
        if payment_method not in self.payment_methods:
            raise ValueError("Invalid payment method")
        
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "items": [{"item_id": item.item_id, "product_id": item.product_id, "status": item.status} for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def cancel_pending_order(self, order_id: str, reason: str) -> dict:
        """Cancel pending order with reason."""
        order = self.orders[order_id]
        if order.status != "pending":
            raise ValueError("Order is not in pending status")
        if reason not in self.valid_cancellation_reasons:
            raise ValueError("Invalid cancellation reason")
        
        order.status = "cancelled"
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "items": [{"item_id": item.item_id, "product_id": item.product_id, "status": item.status} for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def return_delivered_order_items(self, order_id: str, item_ids: List[str], payment_method: str) -> dict:
        """Request return for delivered order items."""
        order = self.orders[order_id]
        if order.status != "delivered":
            raise ValueError("Order is not in delivered status")
        if payment_method not in self.payment_methods:
            raise ValueError("Invalid payment method")
        
        # Update item statuses
        for item in order.items:
            if item.item_id in item_ids:
                item.status = "returned"
        
        # Update order status
        order.status = "return requested"
        
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "items": [{"item_id": item.item_id, "product_id": item.product_id, "status": item.status} for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

    def exchange_delivered_order_items(self, order_id: str, item_ids: List[str], new_item_ids: List[str], payment_method: str) -> dict:
        """Exchange delivered order items."""
        order = self.orders[order_id]
        if order.status != "delivered":
            raise ValueError("Order is not in delivered status")
        if payment_method not in self.payment_methods:
            raise ValueError("Invalid payment method")
        
        # Update item statuses
        for item in order.items:
            if item.item_id in item_ids:
                item.status = "exchanged"
        
        # Add new items
        for new_item_id in new_item_ids:
            product_id = "unknown"
            for product in self.products.values():
                if new_item_id in product.item_ids:
                    product_id = product.product_id
                    break
            order.items.append(OrderItem(item_id=new_item_id, product_id=product_id))
        
        # Update order status
        order.status = "exchange requested"
        
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "items": [{"item_id": item.item_id, "product_id": item.product_id, "status": item.status} for item in order.items],
            "total_amount": order.total_amount,
            "address": order.address
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Retail")
api = RetailAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the retail API.
    
    Args:
        scenario (dict): Scenario dictionary matching RetailScenario schema.
    
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
    Save current retail state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def find_user_by_email(email: str) -> dict:
    """
    Find user information by their registered email address.
    
    Args:
        email (str): The registered email address associated with the user account.
    
    Returns:
        user_id (str): The unique identifier for the customer account.
        name (str): The full name of the user.
        email (str): The registered email address associated with the user account.
        zip_code (str): The five-digit postal zip code of the user's address.
    """
    try:
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
        result = api.find_user_by_email(email)
        if not result:
            raise ValueError("User not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def find_user_by_name_zip(first_name: str, last_name: str, zip_code: str) -> dict:
    """
    Find user information by matching their legal name and zip code.
    
    Args:
        first_name (str): The legal first name of the user.
        last_name (str): The legal last name of the user.
        zip_code (str): The five-digit postal zip code of the user's address.
    
    Returns:
        user_id (str): The unique identifier for the customer account.
        name (str): The full name of the user.
        email (str): The registered email address associated with the user account.
        zip_code (str): The five-digit postal zip code of the user's address.
    """
    try:
        if not first_name or not isinstance(first_name, str):
            raise ValueError("First name must be a non-empty string")
        if not last_name or not isinstance(last_name, str):
            raise ValueError("Last name must be a non-empty string")
        if not zip_code or not isinstance(zip_code, str):
            raise ValueError("Zip code must be a non-empty string")
        result = api.find_user_by_name_zip(first_name, last_name, zip_code)
        if not result:
            raise ValueError("User not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_user_details(user_id: str) -> dict:
    """
    Retrieve comprehensive user profile including address, payment methods, and associated orders.
    
    Args:
        user_id (str): The unique identifier for the customer account.
    
    Returns:
        user_id (str): The unique identifier for the customer account.
        name (dict): The user's name details, including first and last name components.
        email (str): The registered email address associated with the user account.
        address (dict): The user's default shipping address details.
        payment_methods (list): List of payment methods registered to the user account.
        zip_code (str): The five-digit postal zip code of the user's address.
        order_ids (list): List of order identifiers associated with the user account.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if user_id not in api.users:
            raise ValueError("User not found")
        return api.get_user_details(user_id)
    except Exception as e:
        raise e

@mcp.tool()
def modify_user_address(user_id: str, address: str, city: str, state: str, country: str, zip_code: str) -> dict:
    """
    Update the default shipping address for a user account.
    
    Args:
        user_id (str): The unique identifier for the customer account.
        address (str): The primary line of the shipping address (e.g., street number and name).
        city (str): The city name for the shipping address.
        state (str): The state or province code for the shipping address.
        country (str): The country name for the shipping address.
        zip_code (str): The five-digit postal zip code for the shipping address.
    
    Returns:
        user_id (str): The unique identifier for the customer account.
        updated_address (dict): The newly updated shipping address details.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if user_id not in api.users:
            raise ValueError("User not found")
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        if not country or not isinstance(country, str):
            raise ValueError("Country must be a non-empty string")
        if not zip_code or not isinstance(zip_code, str):
            raise ValueError("Zip code must be a non-empty string")
        return api.modify_user_address(user_id, address, city, state, country, zip_code)
    except Exception as e:
        raise e

@mcp.tool()
def list_product_types() -> dict:
    """
    List all available product categories and their basic information.
    
    Returns:
        products (list): List of available product types with their identifiers and names.
    """
    try:
        return api.list_product_types()
    except Exception as e:
        raise e

@mcp.tool()
def get_product_details(product_id: str) -> dict:
    """
    Retrieve detailed information including description and available item variants for a product.
    
    Args:
        product_id (str): The unique identifier for the product type.
    
    Returns:
        name (str): The display name of the product.
        description (str): Detailed description of the product features and specifications.
        item_ids (list): List of item identifiers.
    """
    try:
        if not product_id or not isinstance(product_id, str):
            raise ValueError("Product ID must be a non-empty string")
        if product_id not in api.products:
            raise ValueError("Product not found")
        return api.get_product_details(product_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """
    Retrieve the status, items, and shipping details of a specific order.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The current status of the order (e.g., 'pending', 'delivered', 'cancelled').
        item_ids (list): List of item identifiers in the order.
        total_amount (float): The total monetary amount of the order.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        return api.get_order_details(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def modify_pending_order_address(order_id: str, address: str, city: str, state: str, country: str, zip_code: str) -> dict:
    """
    Change the shipping address for an order that is still in pending status.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        address (str): The primary line of the shipping address (e.g., street number and name).
        city (str): The city name for the shipping address.
        state (str): The state or province code for the shipping address.
        country (str): The country name for the shipping address.
        zip_code (str): The five-digit postal zip code for the shipping address.
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The current status of the order.
        item_ids (list): List of item identifiers in the order.
        total_amount (float): The total monetary amount of the order.
        address (dict): The updated shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        if not country or not isinstance(country, str):
            raise ValueError("Country must be a non-empty string")
        if not zip_code or not isinstance(zip_code, str):
            raise ValueError("Zip code must be a non-empty string")
        return api.modify_pending_order_address(order_id, address, city, state, country, zip_code)
    except Exception as e:
        raise e

@mcp.tool()
def modify_pending_order_items(order_id: str, item_ids: List[str], new_item_ids: List[str], payment_method: str) -> dict:
    """
    Swap items in a pending order with other variants of the same product.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        item_ids (list): List of current item identifiers to be removed from the order.
        new_item_ids (list): List of new item identifiers to be added as replacements.
        payment_method (str): The payment method used to settle any price difference resulting from the item swap.
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The current status of the order.
        items (list): The updated list of items in the order after modification.
        total_amount (float): The updated total monetary amount of the order.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not isinstance(item_ids, list) or not all(isinstance(item, str) for item in item_ids):
            raise ValueError("Item IDs must be a list of strings")
        if not isinstance(new_item_ids, list) or not all(isinstance(item, str) for item in new_item_ids):
            raise ValueError("New item IDs must be a list of strings")
        if not payment_method or not isinstance(payment_method, str):
            raise ValueError("Payment method must be a non-empty string")
        return api.modify_pending_order_items(order_id, item_ids, new_item_ids, payment_method)
    except Exception as e:
        raise e

@mcp.tool()
def modify_pending_order_payment(order_id: str, payment_method: str) -> dict:
    """
    Update the payment method used for a pending order.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        payment_method (str): The new payment method to be used for the order.
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The current status of the order.
        items (list): List of items in the order.
        total_amount (float): The total monetary amount of the order.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not payment_method or not isinstance(payment_method, str):
            raise ValueError("Payment method must be a non-empty string")
        return api.modify_pending_order_payment(order_id, payment_method)
    except Exception as e:
        raise e

@mcp.tool()
def cancel_pending_order(order_id: str, reason: str) -> dict:
    """
    Cancel a pending order with a specified cancellation reason.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        reason (str): The valid reason for the cancellation request.
    
    Returns:
        order_id (str): The unique identifier for the cancelled order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The updated status of the order (cancelled).
        items (list): List of items that were in the cancelled order.
        total_amount (float): The total monetary amount of the cancelled order.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not reason or not isinstance(reason, str):
            raise ValueError("Reason must be a non-empty string")
        return api.cancel_pending_order(order_id, reason)
    except Exception as e:
        raise e

@mcp.tool()
def return_delivered_order_items(order_id: str, item_ids: List[str], payment_method: str) -> dict:
    """
    Request a return for specific items in a delivered order.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        item_ids (list): List of item identifiers for items being returned.
        payment_method (str): The payment method to receive the refund.
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The updated status of the order (return requested).
        items (list): List of items in the order with their return status.
        total_amount (float): The total monetary amount of the order.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not isinstance(item_ids, list) or not all(isinstance(item, str) for item in item_ids):
            raise ValueError("Item IDs must be a list of strings")
        if not payment_method or not isinstance(payment_method, str):
            raise ValueError("Payment method must be a non-empty string")
        return api.return_delivered_order_items(order_id, item_ids, payment_method)
    except Exception as e:
        raise e

@mcp.tool()
def exchange_delivered_order_items(order_id: str, item_ids: List[str], new_item_ids: List[str], payment_method: str) -> dict:
    """
    Exchange delivered items for new variants of the same product.
    
    Args:
        order_id (str): The unique identifier for the order, including the '#' prefix (e.g., '#W0001').
        item_ids (list): List of item identifiers for items to be exchanged.
        new_item_ids (list): List of item identifiers for the new replacement items.
        payment_method (str): The payment method used to settle any price difference resulting from the exchange.
    
    Returns:
        order_id (str): The unique identifier for the order, including the '#' prefix.
        user_id (str): The unique identifier for the customer account that placed the order.
        status (str): The updated status of the order (exchange requested).
        items (list): List of items in the order with their exchange status.
        total_amount (float): The updated total monetary amount of the order after exchange.
        address (dict): The shipping address details for the order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError("Order not found")
        if not isinstance(item_ids, list) or not all(isinstance(item, str) for item in item_ids):
            raise ValueError("Item IDs must be a list of strings")
        if not isinstance(new_item_ids, list) or not all(isinstance(item, str) for item in new_item_ids):
            raise ValueError("New item IDs must be a list of strings")
        if not payment_method or not isinstance(payment_method, str):
            raise ValueError("Payment method must be a non-empty string")
        return api.exchange_delivered_order_items(order_id, item_ids, new_item_ids, payment_method)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()