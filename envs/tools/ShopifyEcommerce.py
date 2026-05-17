
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class ProductVariant(BaseModel):
    """Represents a product variant."""
    id: int = Field(..., ge=0, description="Variant ID")
    title: str = Field(default="", description="Variant title")
    price: str = Field(..., description="Variant price")
    sku: str = Field(default="", description="SKU")
    inventory_quantity: int = Field(default=0, ge=0, description="Inventory quantity")

class ProductImage(BaseModel):
    """Represents a product image."""
    src: str = Field(..., description="Image URL")

class Product(BaseModel):
    """Represents a product."""
    id: int = Field(..., ge=0, description="Product ID")
    title: str = Field(..., description="Product title")
    body_html: str = Field(default="", description="Product description")
    vendor: str = Field(default="", description="Vendor name")
    product_type: str = Field(default="", description="Product type")
    variants: List[ProductVariant] = Field(default=[], description="Product variants")
    images: List[ProductImage] = Field(default=[], description="Product images")

class OrderLineItem(BaseModel):
    """Represents an order line item."""
    title: str = Field(..., description="Item title")
    quantity: int = Field(..., ge=1, description="Item quantity")
    price: str = Field(..., description="Item price")
    variant_id: Optional[int] = Field(default=None, ge=0, description="Variant ID")

class Customer(BaseModel):
    """Represents a customer."""
    id: Optional[int] = Field(default=None, ge=0, description="Customer ID")
    email: str = Field(..., description="Customer email")
    first_name: str = Field(default="", description="First name")
    last_name: str = Field(default="", description="Last name")
    orders_count: int = Field(default=0, ge=0, description="Orders count")
    total_spent: str = Field(default="0.00", description="Total spent")

class Order(BaseModel):
    """Represents an order."""
    id: int = Field(..., ge=0, description="Order ID")
    name: str = Field(..., description="Order name")
    total_price: str = Field(..., description="Total price")
    financial_status: str = Field(default="pending", description="Financial status")
    fulfillment_status: Optional[str] = Field(default=None, description="Fulfillment status")
    line_items: List[OrderLineItem] = Field(default=[], description="Line items")
    customer: Optional[Customer] = Field(default=None, description="Customer")

class ShopifyScenario(BaseModel):
    """Main scenario model for Shopify e-commerce."""
    products: Dict[int, Product] = Field(default={}, description="Products catalog")
    orders: Dict[int, Order] = Field(default={}, description="Orders")
    customers: Dict[int, Customer] = Field(default={}, description="Customers")
    next_product_id: int = Field(default=1, ge=1, description="Next product ID")
    next_order_id: int = Field(default=1001, ge=1, description="Next order ID")
    next_customer_id: int = Field(default=1, ge=1, description="Next customer ID")
    next_variant_id: int = Field(default=1, ge=1, description="Next variant ID")

Scenario_Schema = [ProductVariant, ProductImage, Product, OrderLineItem, Customer, Order, ShopifyScenario]

# Section 2: Class
class ShopifyEcommerce:
    def __init__(self):
        """Initialize Shopify e-commerce API with empty state."""
        self.products: Dict[int, Product] = {}
        self.orders: Dict[int, Order] = {}
        self.customers: Dict[int, Customer] = {}
        self.next_product_id: int = 1
        self.next_order_id: int = 1001
        self.next_customer_id: int = 1
        self.next_variant_id: int = 1

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ShopifyScenario(**scenario)
        self.products = model.products
        self.orders = model.orders
        self.customers = model.customers
        self.next_product_id = model.next_product_id
        self.next_order_id = model.next_order_id
        self.next_customer_id = model.next_customer_id
        self.next_variant_id = model.next_variant_id

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "products": {pid: p.model_dump() for pid, p in self.products.items()},
            "orders": {oid: o.model_dump() for oid, o in self.orders.items()},
            "customers": {cid: c.model_dump() for cid, c in self.customers.items()},
            "next_product_id": self.next_product_id,
            "next_order_id": self.next_order_id,
            "next_customer_id": self.next_customer_id,
            "next_variant_id": self.next_variant_id
        }

    def get_products(self, limit: int, vendor: Optional[str], product_type: Optional[str]) -> dict:
        """Retrieve products with optional filtering."""
        filtered = list(self.products.values())
        if vendor:
            filtered = [p for p in filtered if p.vendor == vendor]
        if product_type:
            filtered = [p for p in filtered if p.product_type == product_type]
        return {"products": [p.model_dump() for p in filtered[:limit]]}

    def create_product(self, title: str, body_html: Optional[str], vendor: Optional[str], 
                      product_type: Optional[str], variants: Optional[List[dict]]) -> dict:
        """Create a new product."""
        pid = self.next_product_id
        self.next_product_id += 1
        
        variant_list = []
        if variants:
            for v in variants:
                vid = self.next_variant_id
                self.next_variant_id += 1
                variant_list.append(ProductVariant(
                    id=vid,
                    title=v.get("title", "Default"),
                    price=v.get("price", "0.00"),
                    sku=v.get("sku", ""),
                    inventory_quantity=v.get("inventory_quantity", 0)
                ))
        
        product = Product(
            id=pid,
            title=title,
            body_html=body_html or "",
            vendor=vendor or "",
            product_type=product_type or "",
            variants=variant_list,
            images=[]
        )
        self.products[pid] = product
        return {"product": {
            "id": product.id,
            "title": product.title,
            "body_html": product.body_html,
            "vendor": product.vendor,
            "product_type": product.product_type
        }}

    def get_orders(self, status: Optional[str], limit: int, created_at_min: Optional[str]) -> dict:
        """Retrieve orders with optional filtering."""
        filtered = list(self.orders.values())
        if status and status != "any":
            if status == "open":
                filtered = [o for o in filtered if o.fulfillment_status != "fulfilled"]
            elif status == "closed":
                filtered = [o for o in filtered if o.fulfillment_status == "fulfilled"]
            elif status == "cancelled":
                filtered = [o for o in filtered if o.financial_status == "refunded"]
        return {"orders": [o.model_dump() for o in filtered[:limit]]}

    def create_order(self, line_items: List[dict], customer: Optional[dict], 
                    financial_status: Optional[str]) -> dict:
        """Create a new order."""
        oid = self.next_order_id
        self.next_order_id += 1
        
        items = []
        total = 0.0
        for item in line_items:
            items.append(OrderLineItem(
                title=f"Product Variant {item['variant_id']}",
                quantity=item["quantity"],
                price=item["price"],
                variant_id=item["variant_id"]
            ))
            total += float(item["price"]) * item["quantity"]
        
        cust = None
        if customer:
            cust = Customer(
                email=customer["email"],
                first_name=customer.get("first_name", ""),
                last_name=customer.get("last_name", "")
            )
        
        order = Order(
            id=oid,
            name=f"#{oid}",
            total_price=f"{total:.2f}",
            financial_status=financial_status or "pending",
            fulfillment_status=None,
            line_items=items,
            customer=cust
        )
        self.orders[oid] = order
        return {"order": {
            "id": order.id,
            "name": order.name,
            "total_price": order.total_price,
            "financial_status": order.financial_status
        }}

    def get_customers(self, limit: int, email: Optional[str]) -> dict:
        """Retrieve customers with optional filtering."""
        filtered = list(self.customers.values())
        if email:
            filtered = [c for c in filtered if c.email == email]
        return {"customers": [c.model_dump() for c in filtered[:limit]]}

# Section 3: MCP Tools
mcp = FastMCP(name="ShopifyEcommerce")
api = ShopifyEcommerce()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Shopify e-commerce API.

    Args:
        scenario (dict): Scenario dictionary matching ShopifyScenario schema.

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
    Save current Shopify state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_products(limit: int = 10, vendor: Optional[str] = None, product_type: Optional[str] = None) -> dict:
    """
    Retrieve products from the store catalog with optional filtering.

    Args:
        limit (int): Number of products to return (maximum 250, default 10). [Optional]
        vendor (str): Filter products by vendor name. [Optional]
        product_type (str): Filter products by product type. [Optional]

    Returns:
        products (list): List of product objects with id, title, body_html, vendor, product_type, variants, and images.
    """
    try:
        if limit > 250:
            limit = 250
        return api.get_products(limit, vendor, product_type)
    except Exception as e:
        raise e

@mcp.tool()
def create_product(title: str, body_html: Optional[str] = None, vendor: Optional[str] = None,
                  product_type: Optional[str] = None, variants: Optional[List[dict]] = None) -> dict:
    """
    Create a new product in the store.

    Args:
        title (str): Product title.
        body_html (str): Product description in HTML format. [Optional]
        vendor (str): Vendor name. [Optional]
        product_type (str): Product type. [Optional]
        variants (list): List of variant dictionaries with price, sku, inventory_quantity. [Optional]

    Returns:
        product (dict): Created product object with id, title, body_html, vendor, and product_type.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        return api.create_product(title, body_html, vendor, product_type, variants)
    except Exception as e:
        raise e

@mcp.tool()
def get_orders(status: Optional[str] = None, limit: int = 50, created_at_min: Optional[str] = None) -> dict:
    """
    Retrieve orders from the store with optional filtering.

    Args:
        status (str): Filter by status: 'open', 'closed', 'cancelled', or 'any'. [Optional]
        limit (int): Number of orders to return (maximum 250, default 50). [Optional]
        created_at_min (str): Filter orders created on or after this date (ISO 8601 format). [Optional]

    Returns:
        orders (list): List of order objects with id, name, total_price, financial_status, fulfillment_status, and line_items.
    """
    try:
        if limit > 250:
            limit = 250
        return api.get_orders(status, limit, created_at_min)
    except Exception as e:
        raise e

@mcp.tool()
def create_order(line_items: List[dict], customer: Optional[dict] = None, 
                financial_status: Optional[str] = None) -> dict:
    """
    Create a new order in the store.

    Args:
        line_items (list): List of item dictionaries with variant_id, quantity, and price.
        customer (dict): Customer information with email, first_name, last_name. [Optional]
        financial_status (str): Payment status: 'pending', 'authorized', or 'paid'. [Optional]

    Returns:
        order (dict): Created order object with id, name, total_price, and financial_status.
    """
    try:
        if not line_items or not isinstance(line_items, list):
            raise ValueError("Line items must be a non-empty list")
        return api.create_order(line_items, customer, financial_status)
    except Exception as e:
        raise e

@mcp.tool()
def get_customers(limit: int = 50, email: Optional[str] = None) -> dict:
    """
    Retrieve customers from the store with optional filtering.

    Args:
        limit (int): Number of customers to return (maximum 250, default 50). [Optional]
        email (str): Filter customers by email address. [Optional]

    Returns:
        customers (list): List of customer objects with id, email, first_name, last_name, orders_count, and total_spent.
    """
    try:
        if limit > 250:
            limit = 250
        return api.get_customers(limit, email)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
