
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class OrderItem(BaseModel):
    """Represents a line item in an order."""
    name: str = Field(..., description="Item name")
    quantity: int = Field(..., ge=1, description="Item quantity")
    unit_amount: str = Field(..., pattern=r"^\d+\.\d{2}$", description="Unit price")

class Order(BaseModel):
    """Represents a PayPal order."""
    id: str = Field(..., description="Order ID")
    status: str = Field(..., description="Order status")
    intent: str = Field(..., description="Payment intent")
    amount: str = Field(..., pattern=r"^\d+\.\d{2}$", description="Total amount")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Currency code")
    description: Optional[str] = Field(default=None, description="Order description")
    items: List[OrderItem] = Field(default_factory=list, description="Order items")
    links: List[Dict[str, str]] = Field(default_factory=list, description="HATEOAS links")
    payer: Optional[Dict[str, Any]] = Field(default=None, description="Payer information")
    create_time: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$", description="Creation timestamp")
    update_time: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$", description="Update timestamp")

class Authorization(BaseModel):
    """Represents a payment authorization."""
    id: str = Field(..., description="Authorization ID")
    order_id: str = Field(..., description="Associated order ID")
    amount: str = Field(..., pattern=r"^\d+\.\d{2}$", description="Authorized amount")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Currency code")
    expiration_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$", description="Expiration timestamp")

class Capture(BaseModel):
    """Represents a payment capture."""
    id: str = Field(..., description="Capture ID")
    order_id: Optional[str] = Field(default=None, description="Associated order ID")
    authorization_id: Optional[str] = Field(default=None, description="Associated authorization ID")
    status: str = Field(..., description="Capture status")
    amount: str = Field(..., pattern=r"^\d+\.\d{2}$", description="Captured amount")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Currency code")
    final_capture: bool = Field(default=False, description="Is final capture")

class PayPalScenario(BaseModel):
    """Main scenario model for PayPal payment processing."""
    orders: Dict[str, Order] = Field(default_factory=dict, description="All orders")
    authorizations: Dict[str, Authorization] = Field(default_factory=dict, description="All authorizations")
    captures: Dict[str, Capture] = Field(default_factory=dict, description="All captures")
    next_order_id: int = Field(default=1, ge=1, description="Next order ID counter")
    next_auth_id: int = Field(default=1, ge=1, description="Next authorization ID counter")
    next_capture_id: int = Field(default=1, ge=1, description="Next capture ID counter")
    current_time: str = Field(default="2026-03-05T12:12:45Z", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$", description="Current timestamp")

Scenario_Schema = [OrderItem, Order, Authorization, Capture, PayPalScenario]

# Section 2: Class
class PayPalPaymentProcessor:
    def __init__(self):
        """Initialize PayPal payment processor with empty state."""
        self.orders: Dict[str, Order] = {}
        self.authorizations: Dict[str, Authorization] = {}
        self.captures: Dict[str, Capture] = {}
        self.next_order_id: int = 1
        self.next_auth_id: int = 1
        self.next_capture_id: int = 1
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the processor instance."""
        model = PayPalScenario(**scenario)
        self.orders = model.orders
        self.authorizations = model.authorizations
        self.captures = model.captures
        self.next_order_id = model.next_order_id
        self.next_auth_id = model.next_auth_id
        self.next_capture_id = model.next_capture_id
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "orders": {oid: order.model_dump() for oid, order in self.orders.items()},
            "authorizations": {aid: auth.model_dump() for aid, auth in self.authorizations.items()},
            "captures": {cid: cap.model_dump() for cid, cap in self.captures.items()},
            "next_order_id": self.next_order_id,
            "next_auth_id": self.next_auth_id,
            "next_capture_id": self.next_capture_id,
            "current_time": self.current_time
        }

    def create_order(self, amount: str, currency_code: str, intent: str, description: str, items: List[dict]) -> dict:
        """Create a new PayPal order."""
        order_id = f"ORDER-{self.next_order_id}"
        self.next_order_id += 1
        
        order_items = [OrderItem(**item) for item in items] if items else []
        
        order = Order(
            id=order_id,
            status="CREATED",
            intent=intent,
            amount=amount,
            currency=currency_code,
            description=description,
            items=order_items,
            links=[
                {"rel": "approve", "href": f"https://www.paypal.com/checkoutnow?token={order_id}"},
                {"rel": "self", "href": f"https://api.paypal.com/v2/checkout/orders/{order_id}"}
            ],
            create_time=self.current_time,
            update_time=self.current_time
        )
        
        self.orders[order_id] = order
        
        return {
            "id": order.id,
            "status": order.status,
            "intent": order.intent,
            "amount": order.amount,
            "currency": order.currency,
            "links": order.links
        }

    def capture_order(self, order_id: str) -> dict:
        """Capture payment for an order."""
        order = self.orders[order_id]
        
        capture_id = f"CAPTURE-{self.next_capture_id}"
        self.next_capture_id += 1
        
        capture = Capture(
            id=capture_id,
            order_id=order_id,
            status="COMPLETED",
            amount=order.amount,
            currency=order.currency,
            final_capture=True
        )
        
        self.captures[capture_id] = capture
        order.status = "COMPLETED"
        order.update_time = self.current_time
        
        return {
            "id": order.id,
            "status": order.status,
            "capture_id": capture_id,
            "amount": order.amount,
            "currency": order.currency,
            "payer": order.payer or {}
        }

    def authorize_order(self, order_id: str) -> dict:
        """Authorize payment for an order."""
        order = self.orders[order_id]
        
        auth_id = f"AUTH-{self.next_auth_id}"
        self.next_auth_id += 1
        
        authorization = Authorization(
            id=auth_id,
            order_id=order_id,
            amount=order.amount,
            currency=order.currency,
            expiration_time=self.current_time
        )
        
        self.authorizations[auth_id] = authorization
        order.status = "APPROVED"
        order.update_time = self.current_time
        
        return {
            "id": order.id,
            "status": order.status,
            "authorization_id": auth_id,
            "amount": order.amount,
            "currency": order.currency,
            "expiration_time": authorization.expiration_time
        }

    def capture_authorized_payment(self, authorization_id: str, amount: str, final_capture: bool) -> dict:
        """Capture funds from a previously authorized payment."""
        authorization = self.authorizations[authorization_id]
        
        capture_id = f"CAPTURE-{self.next_capture_id}"
        self.next_capture_id += 1
        
        capture_amount = amount if amount else authorization.amount
        
        capture = Capture(
            id=capture_id,
            authorization_id=authorization_id,
            status="COMPLETED",
            amount=capture_amount,
            currency=authorization.currency,
            final_capture=final_capture
        )
        
        self.captures[capture_id] = capture
        
        return {
            "id": capture_id,
            "status": capture.status,
            "amount": capture.amount,
            "currency": capture.currency,
            "final_capture": capture.final_capture
        }

    def get_order_details(self, order_id: str) -> dict:
        """Retrieve complete details of an existing order."""
        order = self.orders[order_id]
        
        return {
            "id": order.id,
            "status": order.status,
            "intent": order.intent,
            "purchase_units": [{"amount": {"value": order.amount, "currency_code": order.currency}, "items": [item.model_dump() for item in order.items]}],
            "payer": order.payer or {},
            "create_time": order.create_time,
            "update_time": order.update_time
        }

# Section 3: MCP Tools
mcp = FastMCP(name="PayPalPaymentProcessor")
api = PayPalPaymentProcessor()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the PayPal payment processor.

    Args:
        scenario (dict): Scenario dictionary matching PayPalScenario schema.

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
    Save current PayPal payment processor state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def create_order(amount: str, currency_code: str = "USD", intent: str = "CAPTURE", description: str = "", items: list = None) -> dict:
    """
    Create a new PayPal order for payment processing with specified amount and currency.

    Args:
        amount (str): The total payment amount as a decimal string (e.g., '100.00').
        currency_code (str): [Optional] The three-letter ISO 4217 currency code for the payment (e.g., 'USD', 'EUR').
        intent (str): [Optional] The payment intent: 'CAPTURE' for immediate payment capture or 'AUTHORIZE' for delayed capture requiring explicit authorization.
        description (str): [Optional] A human-readable description of the order for reference purposes.
        items (list): [Optional] Line items included in the order, each containing name, quantity, and unit_amount properties.

    Returns:
        id (str): The unique PayPal order identifier used to reference this order in subsequent operations.
        status (str): The current status of the order (e.g., 'CREATED', 'APPROVED', 'COMPLETED').
        intent (str): The payment intent: 'CAPTURE' for immediate payment capture or 'AUTHORIZE' for delayed capture requiring explicit authorization.
        amount (str): The total payment amount as a decimal string.
        currency (str): The three-letter ISO 4217 currency code for the payment.
        links (list): HATEOAS links for order-related actions such as approval and capture URLs.
    """
    try:
        if not amount or not isinstance(amount, str):
            raise ValueError("Amount must be a non-empty string")
        if items is None:
            items = []
        return api.create_order(amount, currency_code, intent, description, items)
    except Exception as e:
        raise e

@mcp.tool()
def capture_order(order_id: str) -> dict:
    """
    Capture payment for an order to complete the transaction and transfer funds.

    Args:
        order_id (str): The unique PayPal order identifier used to reference this order in subsequent operations.

    Returns:
        id (str): The unique PayPal order identifier used to reference this order in subsequent operations.
        status (str): The current status of the order (e.g., 'CREATED', 'APPROVED', 'COMPLETED').
        capture_id (str): The unique identifier for the payment capture transaction.
        amount (str): The total payment amount as a decimal string.
        currency (str): The three-letter ISO 4217 currency code for the payment.
        payer (dict): Information about the payer including email, name, and PayPal account details.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError(f"Order {order_id} not found")
        return api.capture_order(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def authorize_order(order_id: str) -> dict:
    """
    Authorize payment for an order without capturing funds, allowing for delayed capture.

    Args:
        order_id (str): The unique PayPal order identifier used to reference this order in subsequent operations.

    Returns:
        id (str): The unique PayPal order identifier used to reference this order in subsequent operations.
        status (str): The current status of the order (e.g., 'CREATED', 'APPROVED', 'COMPLETED').
        authorization_id (str): The unique identifier for the payment authorization that can be used to capture funds later.
        amount (str): The total payment amount as a decimal string.
        currency (str): The three-letter ISO 4217 currency code for the payment.
        expiration_time (str): The ISO 8601 timestamp when the authorization expires and can no longer be captured.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError(f"Order {order_id} not found")
        return api.authorize_order(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def capture_authorized_payment(authorization_id: str, amount: str = None, final_capture: bool = False) -> dict:
    """
    Capture funds from a previously authorized payment, either partially or in full.

    Args:
        authorization_id (str): The unique identifier for the payment authorization that can be used to capture funds later.
        amount (str): [Optional] The amount to capture as a decimal string; if omitted, captures the full authorized amount.
        final_capture (bool): [Optional] Indicates whether this is the final capture for the authorization; if true, any remaining authorized amount is released.

    Returns:
        id (str): The unique identifier for the payment capture transaction.
        status (str): The current status of the capture (e.g., 'PENDING', 'COMPLETED', 'DECLINED').
        amount (str): The total payment amount as a decimal string.
        currency (str): The three-letter ISO 4217 currency code for the payment.
        final_capture (bool): Indicates whether this is the final capture for the authorization; if true, any remaining authorized amount is released.
    """
    try:
        if not authorization_id or not isinstance(authorization_id, str):
            raise ValueError("Authorization ID must be a non-empty string")
        if authorization_id not in api.authorizations:
            raise ValueError(f"Authorization {authorization_id} not found")
        return api.capture_authorized_payment(authorization_id, amount, final_capture)
    except Exception as e:
        raise e

@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """
    Retrieve complete details of an existing PayPal order including status, payer information, and purchase units.

    Args:
        order_id (str): The unique PayPal order identifier used to reference this order in subsequent operations.

    Returns:
        id (str): The unique PayPal order identifier used to reference this order in subsequent operations.
        status (str): The current status of the order (e.g., 'CREATED', 'APPROVED', 'COMPLETED').
        intent (str): The payment intent: 'CAPTURE' for immediate payment capture or 'AUTHORIZE' for delayed capture requiring explicit authorization.
        purchase_units (list): The items or services being purchased, including amounts, descriptions, and shipping details.
        payer (dict): Information about the payer including email, name, and PayPal account details.
        create_time (str): The ISO 8601 timestamp when the order was created.
        update_time (str): The ISO 8601 timestamp when the order was last updated.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in api.orders:
            raise ValueError(f"Order {order_id} not found")
        return api.get_order_details(order_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
