
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class PaymentIntent(BaseModel):
    """Represents a Stripe PaymentIntent."""
    id: str = Field(..., description="Unique identifier of the PaymentIntent")
    client_secret: str = Field(..., description="Secret key for client confirmation")
    status: str = Field(..., description="Current status of the payment intent")
    amount: int = Field(..., ge=0, description="Amount in smallest currency unit")
    currency: str = Field(..., pattern=r"^[a-z]{3}$", description="Three-letter ISO currency code")
    customer: Optional[str] = Field(default=None, description="Customer ID")
    payment_method: Optional[str] = Field(default=None, description="Payment method ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    created: int = Field(..., ge=0, description="Unix timestamp of creation")

class Customer(BaseModel):
    """Represents a Stripe Customer."""
    id: str = Field(..., description="Unique identifier of the customer")
    email: str = Field(..., description="Customer email address")
    name: Optional[str] = Field(default=None, description="Customer full name")
    phone: Optional[str] = Field(default=None, description="Customer phone number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    created: int = Field(..., ge=0, description="Unix timestamp of creation")

class Refund(BaseModel):
    """Represents a Stripe Refund."""
    id: str = Field(..., description="Unique identifier of the refund")
    amount: int = Field(..., ge=0, description="Amount refunded in smallest currency unit")
    status: str = Field(..., description="Current status of the refund")
    reason: Optional[str] = Field(default=None, description="Reason for refund")
    payment_intent_id: str = Field(..., description="Associated PaymentIntent ID")

class Charge(BaseModel):
    """Represents a Stripe Charge."""
    id: str = Field(..., description="Unique identifier of the charge")
    amount: int = Field(..., ge=0, description="Amount charged in smallest currency unit")
    currency: str = Field(..., pattern=r"^[a-z]{3}$", description="Three-letter ISO currency code")
    status: str = Field(..., description="Current status of the charge")
    customer: Optional[str] = Field(default=None, description="Customer ID")
    created: int = Field(..., ge=0, description="Unix timestamp of creation")

class StripeScenario(BaseModel):
    """Main scenario model for Stripe payment processing."""
    payment_intents: Dict[str, PaymentIntent] = Field(default_factory=dict, description="Payment intents storage")
    customers: Dict[str, Customer] = Field(default_factory=dict, description="Customers storage")
    refunds: Dict[str, Refund] = Field(default_factory=dict, description="Refunds storage")
    charges: List[Charge] = Field(default_factory=list, description="Charges history")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [PaymentIntent, Customer, Refund, Charge, StripeScenario]

# Section 2: Class
class StripePaymentServer:
    def __init__(self):
        """Initialize Stripe payment server with empty state."""
        self.payment_intents: Dict[str, PaymentIntent] = {}
        self.customers: Dict[str, Customer] = {}
        self.refunds: Dict[str, Refund] = {}
        self.charges: List[Charge] = []
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server instance."""
        model = StripeScenario(**scenario)
        self.payment_intents = model.payment_intents
        self.customers = model.customers
        self.refunds = model.refunds
        self.charges = model.charges
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "payment_intents": {pi_id: pi.model_dump() for pi_id, pi in self.payment_intents.items()},
            "customers": {cust_id: cust.model_dump() for cust_id, cust in self.customers.items()},
            "refunds": {ref_id: ref.model_dump() for ref_id, ref in self.refunds.items()},
            "charges": [charge.model_dump() for charge in self.charges],
            "current_time": self.current_time
        }

    def create_payment_intent(self, amount: int, currency: str, customer_id: Optional[str], payment_method_id: Optional[str], metadata: Optional[Dict[str, Any]]) -> dict:
        """Create a PaymentIntent to collect payment from a customer."""
        import time
        pi_id = f"pi_{len(self.payment_intents) + 1}"
        client_secret = f"{pi_id}_secret_{len(self.payment_intents)}"
        created = int(time.mktime(time.strptime(self.current_time, "%Y-%m-%dT%H:%M:%SZ")))
        
        pi = PaymentIntent(
            id=pi_id,
            client_secret=client_secret,
            status="requires_payment_method",
            amount=amount,
            currency=currency,
            customer=customer_id,
            payment_method=payment_method_id,
            metadata=metadata or {},
            created=created
        )
        self.payment_intents[pi_id] = pi
        
        charge = Charge(
            id=f"ch_{len(self.charges) + 1}",
            amount=amount,
            currency=currency,
            status="succeeded",
            customer=customer_id,
            created=created
        )
        self.charges.append(charge)
        
        return {
            "id": pi.id,
            "client_secret": pi.client_secret,
            "status": pi.status,
            "amount": pi.amount,
            "currency": pi.currency,
            "created": pi.created
        }

    def retrieve_payment_intent(self, payment_intent_id: str) -> dict:
        """Retrieve the complete details of an existing PaymentIntent."""
        pi = self.payment_intents[payment_intent_id]
        return {
            "id": pi.id,
            "client_secret": pi.client_secret,
            "status": pi.status,
            "amount": pi.amount,
            "currency": pi.currency,
            "customer": pi.customer,
            "payment_method": pi.payment_method,
            "metadata": pi.metadata,
            "created": pi.created
        }

    def create_customer(self, email: str, name: Optional[str], phone: Optional[str], metadata: Optional[Dict[str, Any]]) -> dict:
        """Create a new customer record."""
        import time
        cust_id = f"cus_{len(self.customers) + 1}"
        created = int(time.mktime(time.strptime(self.current_time, "%Y-%m-%dT%H:%M:%SZ")))
        
        customer = Customer(
            id=cust_id,
            email=email,
            name=name,
            phone=phone,
            metadata=metadata or {},
            created=created
        )
        self.customers[cust_id] = customer
        
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "created": customer.created
        }

    def create_refund(self, payment_intent_id: str, amount: Optional[int], reason: Optional[str]) -> dict:
        """Create a refund for a previously completed payment."""
        pi = self.payment_intents[payment_intent_id]
        refund_amount = amount if amount is not None else pi.amount
        refund_id = f"re_{len(self.refunds) + 1}"
        
        refund = Refund(
            id=refund_id,
            amount=refund_amount,
            status="succeeded",
            reason=reason,
            payment_intent_id=payment_intent_id
        )
        self.refunds[refund_id] = refund
        
        return {
            "id": refund.id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason
        }

    def list_charges(self, limit: Optional[int], customer_id: Optional[str]) -> dict:
        """Retrieve a list of payment charges with optional filtering."""
        filtered_charges = self.charges
        if customer_id:
            filtered_charges = [c for c in filtered_charges if c.customer == customer_id]
        
        limit_val = limit if limit is not None else 10
        filtered_charges = filtered_charges[:limit_val]
        
        return {
            "charges": [
                {
                    "id": c.id,
                    "amount": c.amount,
                    "currency": c.currency,
                    "status": c.status,
                    "customer": c.customer,
                    "created": c.created
                }
                for c in filtered_charges
            ]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="StripePaymentServer")
server = StripePaymentServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Stripe payment server.

    Args:
        scenario (dict): Scenario dictionary matching StripeScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Stripe payment state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def create_payment_intent(amount: int, currency: str, customer_id: str = None, payment_method_id: str = None, metadata: dict = None) -> dict:
    """
    Create a PaymentIntent to collect payment from a customer.

    Args:
        amount (int): Amount to charge in the smallest currency unit.
        currency (str): Three-letter ISO 4217 currency code in lowercase.
        customer_id (str): [Optional] The unique identifier of an existing Stripe customer.
        payment_method_id (str): [Optional] The unique identifier of a saved payment method.
        metadata (dict): [Optional] Custom key-value pairs to attach additional information.

    Returns:
        id (str): The unique identifier of the created PaymentIntent.
        client_secret (str): Secret key used by the client to confirm the payment.
        status (str): Current status of the payment intent.
        amount (int): Amount to charge in the smallest currency unit.
        currency (str): Three-letter ISO 4217 currency code in lowercase.
        created (int): Unix timestamp indicating when the PaymentIntent was created.
    """
    try:
        if not currency or not isinstance(currency, str):
            raise ValueError("Currency must be a non-empty string")
        return server.create_payment_intent(amount, currency, customer_id, payment_method_id, metadata)
    except Exception as e:
        raise e

@mcp.tool()
def retrieve_payment_intent(payment_intent_id: str) -> dict:
    """
    Retrieve the complete details of an existing PaymentIntent.

    Args:
        payment_intent_id (str): The unique identifier of the PaymentIntent to retrieve.

    Returns:
        id (str): The unique identifier of the PaymentIntent.
        client_secret (str): Secret key used by the client to confirm the payment.
        status (str): Current status of the payment intent.
        amount (int): Amount to charge in the smallest currency unit.
        currency (str): Three-letter ISO 4217 currency code in lowercase.
        customer (str): The unique identifier of the Stripe customer.
        payment_method (str): The unique identifier of the payment method.
        metadata (dict): Custom key-value pairs attached to this payment intent.
        created (int): Unix timestamp indicating when the PaymentIntent was created.
    """
    try:
        if not payment_intent_id or not isinstance(payment_intent_id, str):
            raise ValueError("Payment intent ID must be a non-empty string")
        if payment_intent_id not in server.payment_intents:
            raise ValueError(f"PaymentIntent {payment_intent_id} not found")
        return server.retrieve_payment_intent(payment_intent_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_customer(email: str, name: str = None, phone: str = None, metadata: dict = None) -> dict:
    """
    Create a new customer record for storing payment methods and managing recurring billing.

    Args:
        email (str): The email address of the customer.
        name (str): [Optional] The full name of the customer.
        phone (str): [Optional] The phone number of the customer.
        metadata (dict): [Optional] Custom key-value pairs to attach additional information.

    Returns:
        id (str): The unique identifier of the created Stripe customer.
        email (str): The email address of the customer.
        name (str): The full name of the customer.
        created (int): Unix timestamp indicating when the customer was created.
    """
    try:
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
        return server.create_customer(email, name, phone, metadata)
    except Exception as e:
        raise e

@mcp.tool()
def create_refund(payment_intent_id: str, amount: int = None, reason: str = None) -> dict:
    """
    Create a refund for a previously completed payment.

    Args:
        payment_intent_id (str): The unique identifier of the PaymentIntent to refund.
        amount (int): [Optional] Amount to refund in the smallest currency unit.
        reason (str): [Optional] Reason for the refund ('duplicate', 'fraudulent', or 'requested_by_customer').

    Returns:
        id (str): The unique identifier of the created refund.
        amount (int): Amount refunded in the smallest currency unit.
        status (str): Current status of the refund.
        reason (str): Reason for the refund.
    """
    try:
        if not payment_intent_id or not isinstance(payment_intent_id, str):
            raise ValueError("Payment intent ID must be a non-empty string")
        if payment_intent_id not in server.payment_intents:
            raise ValueError(f"PaymentIntent {payment_intent_id} not found")
        return server.create_refund(payment_intent_id, amount, reason)
    except Exception as e:
        raise e

@mcp.tool()
def list_charges(limit: int = None, customer_id: str = None) -> dict:
    """
    Retrieve a list of payment charges with optional filtering by customer.

    Args:
        limit (int): [Optional] Maximum number of charge records to return (1-100, defaults to 10).
        customer_id (str): [Optional] The unique identifier of an existing Stripe customer to filter charges by.

    Returns:
        charges (list): List of charge objects matching the specified filters.
    """
    try:
        return server.list_charges(limit, customer_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
