from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Customer(BaseModel):
    """Represents a telecom customer."""
    customer_id: str = Field(..., description="Unique customer identifier")
    full_name: str = Field(..., description="Customer's full legal name")
    phone_number: str = Field(..., pattern=r"^\+?1?\d{9,15}$", description="Primary phone number")
    email: str = Field(..., description="Customer's email address")
    city: str = Field(..., description="City of residence")
    country: str = Field(..., description="Country of residence")
    line_ids: List[str] = Field(default=[], description="Associated mobile line IDs")
    bill_ids: List[str] = Field(default=[], description="Associated billing statement IDs")
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date of birth in YYYY-MM-DD format")

class Bill(BaseModel):
    """Represents a billing statement."""
    bill_id: str = Field(..., description="Unique bill identifier")
    customer_id: str = Field(..., description="Associated customer ID")
    issue_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Issue date in ISO 8601 format")
    total_due: float = Field(..., ge=0, description="Total amount due")
    status: str = Field(..., description="Bill status (paid, pending, overdue)")

class Line(BaseModel):
    """Represents a mobile line."""
    line_id: str = Field(..., description="Unique line identifier")
    customer_id: str = Field(..., description="Associated customer ID")
    status: str = Field(default="active", description="Line status (active, suspended)")
    roaming_enabled: bool = Field(default=False, description="International roaming status")
    data_used_gb: float = Field(default=0, ge=0, description="Data used in current cycle (GB)")
    data_limit_gb: int = Field(default=20, ge=0, description="Monthly data allowance (GB)")
    data_refueling_gb: float = Field(default=0, ge=0, description="Additional purchased data (GB)")
    cycle_end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Cycle end date in ISO 8601 format")

class TelecomScenario(BaseModel):
    """Main scenario model for telecom management."""
    customers: Dict[str, Customer] = Field(default={}, description="Customer database")
    bills: Dict[str, Bill] = Field(default={}, description="Billing database")
    lines: Dict[str, Line] = Field(default={}, description="Mobile lines database")
    dataRefuelRatesMap: Dict[str, float] = Field(default={
        "US": 15.0, "CA": 12.0, "UK": 18.0, "DE": 20.0, "FR": 22.0,
        "AU": 25.0, "JP": 30.0, "KR": 28.0, "BR": 8.0, "MX": 10.0,
        "IN": 5.0, "CN": 8.0, "RU": 7.0, "ZA": 12.0, "NG": 6.0,
        "EG": 9.0, "AR": 11.0, "CL": 13.0, "CO": 9.0, "PE": 8.0
    }, description="Data refueling rates per GB by country (USD)")
    roamingRatesMap: Dict[str, float] = Field(default={
        "US": 0.0, "CA": 5.0, "UK": 15.0, "DE": 12.0, "FR": 14.0,
        "AU": 20.0, "JP": 25.0, "KR": 22.0, "BR": 8.0, "MX": 10.0,
        "IN": 18.0, "CN": 16.0, "RU": 14.0, "ZA": 18.0, "NG": 15.0,
        "EG": 12.0, "AR": 10.0, "CL": 11.0, "CO": 9.0, "PE": 10.0
    }, description="Daily roaming charges by country (USD)")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Customer, Bill, Line, TelecomScenario]

# Section 2: Class
class TelecomAPI:
    def __init__(self):
        """Initialize telecom API with empty state."""
        self.customers: Dict[str, Customer] = {}
        self.bills: Dict[str, Bill] = {}
        self.lines: Dict[str, Line] = {}
        self.dataRefuelRatesMap: Dict[str, float] = {}
        self.roamingRatesMap: Dict[str, float] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = TelecomScenario(**scenario)
        self.customers = model.customers
        self.bills = model.bills
        self.lines = model.lines
        self.dataRefuelRatesMap = model.dataRefuelRatesMap
        self.roamingRatesMap = model.roamingRatesMap
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "customers": {k: v.model_dump() for k, v in self.customers.items()},
            "bills": {k: v.model_dump() for k, v in self.bills.items()},
            "lines": {k: v.model_dump() for k, v in self.lines.items()},
            "dataRefuelRatesMap": self.dataRefuelRatesMap,
            "roamingRatesMap": self.roamingRatesMap,
            "current_time": self.current_time
        }

    def get_customer_by_phone(self, phone_number: str) -> dict:
        """Find customer by phone number."""
        for customer in self.customers.values():
            if customer.phone_number == phone_number or phone_number in [self.lines[line_id].line_id for line_id in customer.line_ids]:
                return {
                    "customer_id": customer.customer_id,
                    "full_name": customer.full_name,
                    "phone_number": customer.phone_number,
                    "line_ids": customer.line_ids
                }
        return {}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """Retrieve customer by ID."""
        customer = self.customers[customer_id]
        return {
            "customer_id": customer.customer_id,
            "full_name": customer.full_name,
            "phone_number": customer.phone_number,
            "line_ids": customer.line_ids
        }

    def get_customer_by_name(self, full_name: str, dob: str) -> dict:
        """Search customers by name and date of birth."""
        matches = []
        for customer in self.customers.values():
            if customer.full_name == full_name and customer.dob == dob:
                matches.append({
                    "customer_id": customer.customer_id,
                    "full_name": customer.full_name,
                    "phone_number": customer.phone_number,
                    "line_ids": customer.line_ids
                })
        return {"customers": matches}

    def get_details_by_id(self, customer_id: str) -> dict:
        """Get detailed customer information."""
        customer = self.customers[customer_id]
        return {
            "customer_id": customer.customer_id,
            "full_name": customer.full_name,
            "phone_number": customer.phone_number,
            "line_ids": customer.line_ids,
            "bill_ids": customer.bill_ids,
            "email": customer.email,
            "city": customer.city,
            "country": customer.country
        }

    def list_bills(self, customer_id: str, limit: Optional[int] = None) -> dict:
        """List customer bills, most recent first."""
        customer_bills = [bill for bill in self.bills.values() if bill.customer_id == customer_id]
        customer_bills.sort(key=lambda x: x.issue_date, reverse=True)
        if limit:
            customer_bills = customer_bills[:limit]
        return {"bills": [{"bill_id": b.bill_id, "issue_date": b.issue_date, "total_due": b.total_due, "status": b.status} for b in customer_bills]}

    def get_usage(self, customer_id: str, line_id: str) -> dict:
        """Get current data usage for a line."""
        line = self.lines[line_id]
        return {
            "line_id": line.line_id,
            "data_used_gb": line.data_used_gb,
            "data_limit_gb": line.data_limit_gb,
            "data_refueling_gb": line.data_refueling_gb,
            "cycle_end_date": line.cycle_end_date
        }

    def suspend_line(self, customer_id: str, line_id: str, reason: str) -> dict:
        """Suspend a mobile line."""
        line = self.lines[line_id]
        line.status = "suspended"
        return {
            "line_id": line.line_id,
            "status": line.status,
            "suspension_start_date": self.current_time[:10]
        }

    def resume_line(self, customer_id: str, line_id: str) -> dict:
        """Resume a suspended mobile line."""
        line = self.lines[line_id]
        line.status = "active"
        return {
            "line_id": line.line_id,
            "status": line.status
        }

    def enable_roaming(self, customer_id: str, line_id: str) -> dict:
        """Enable international roaming on a line."""
        line = self.lines[line_id]
        line.roaming_enabled = True
        return {
            "line_id": line.line_id,
            "roaming_enabled": line.roaming_enabled
        }

    def disable_roaming(self, customer_id: str, line_id: str) -> dict:
        """Disable international roaming on a line."""
        line = self.lines[line_id]
        line.roaming_enabled = False
        return {
            "line_id": line.line_id,
            "roaming_enabled": line.roaming_enabled
        }

    def refuel_data(self, customer_id: str, line_id: str, gb_amount: float) -> dict:
        """Add data to a mobile line."""
        line = self.lines[line_id]
        customer = self.customers[customer_id]
        rate = self.dataRefuelRatesMap.get(customer.country, 15.0)
        line.data_refueling_gb += gb_amount
        charge = gb_amount * rate
        return {
            "line_id": line.line_id,
            "new_data_refueling_gb": line.data_refueling_gb,
            "charge_amount": charge
        }

    def send_payment_request(self, customer_id: str, bill_id: str) -> dict:
        """Send payment request for a bill."""
        bill = self.bills[bill_id]
        return {
            "bill_id": bill.bill_id,
            "status": "sent"
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Telecom")
api = TelecomAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the telecom API.
    
    Args:
        scenario (dict): Scenario dictionary matching TelecomScenario schema.
    
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
    """Save current telecom state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_customer_by_phone(phone_number: str) -> dict:
    """Find a customer by their primary contact or line-associated phone number.
    
    Args:
        phone_number (str): The primary or line-associated phone number used to identify the customer account.
    
    Returns:
        customer_id (str): The unique identifier of the customer account.
        full_name (str): The customer's full legal name.
        phone_number (str): The primary or line-associated phone number of the customer.
        line_ids (List[str]): List of unique identifiers for the mobile lines associated with this customer.
    """
    try:
        if not phone_number or not isinstance(phone_number, str):
            raise ValueError("Phone number must be a non-empty string")
        result = api.get_customer_by_phone(phone_number)
        if not result:
            raise ValueError(f"Customer with phone number {phone_number} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_customer_by_id(customer_id: str) -> dict:
    """Retrieve customer details by their unique ID.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
    
    Returns:
        customer_id (str): The unique identifier of the customer account.
        full_name (str): The customer's full legal name.
        phone_number (str): The primary or line-associated phone number of the customer.
        line_ids (List[str]): List of unique identifiers for the mobile lines associated with this customer.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if customer_id not in api.customers:
            raise ValueError(f"Customer {customer_id} not found")
        return api.get_customer_by_id(customer_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_customer_by_name(full_name: str, dob: str) -> dict:
    """Search for customers by name and date of birth.
    
    Args:
        full_name (str): The customer's full legal name.
        dob (str): The customer's date of birth in YYYY-MM-DD format.
    
    Returns:
        customers (List[dict]): List of customers matching the provided name and date of birth.
    """
    try:
        if not full_name or not isinstance(full_name, str):
            raise ValueError("Full name must be a non-empty string")
        if not dob or not isinstance(dob, str):
            raise ValueError("Date of birth must be a non-empty string")
        return api.get_customer_by_name(full_name, dob)
    except Exception as e:
        raise e

@mcp.tool()
def get_details_by_id(customer_id: str) -> dict:
    """Retrieve detailed customer information including billing and contact data.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
    
    Returns:
        customer_id (str): The unique identifier of the customer account.
        full_name (str): The customer's full legal name.
        phone_number (str): The primary or line-associated phone number of the customer.
        line_ids (List[str]): List of unique identifiers for the mobile lines associated with this customer.
        bill_ids (List[str]): List of unique identifiers for the customer's billing statements.
        email (str): The customer's email address.
        city (str): The customer's city of residence.
        country (str): The customer's country of residence.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if customer_id not in api.customers:
            raise ValueError(f"Customer {customer_id} not found")
        return api.get_details_by_id(customer_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_bills(customer_id: str, limit: Optional[int] = None) -> dict:
    """Retrieve a list of the customer's bills, most recent first.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        limit (int) [Optional]: Maximum number of bills to return.
    
    Returns:
        bills (List[dict]): List of billing statements for the customer, ordered most recent first.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if customer_id not in api.customers:
            raise ValueError(f"Customer {customer_id} not found")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer")
        return api.list_bills(customer_id, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_usage(customer_id: str, line_id: str) -> dict:
    """Retrieve current data usage information for a specific line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        data_used_gb (float): Amount of data consumed in gigabytes during the current cycle.
        data_limit_gb (int): Monthly data allowance in gigabytes.
        data_refueling_gb (float): Additional data purchased for this cycle in gigabytes.
        cycle_end_date (str): Date when the current billing cycle ends in ISO 8601 format.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        return api.get_usage(customer_id, line_id)
    except Exception as e:
        raise e

@mcp.tool()
def suspend_line(customer_id: str, line_id: str, reason: str) -> dict:
    """Suspend an active mobile line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
        reason (str): Reason for the line suspension.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        status (str): The new status of the line after suspension.
        suspension_start_date (str): Date when the suspension takes effect in ISO 8601 format.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if not reason or not isinstance(reason, str):
            raise ValueError("Reason must be a non-empty string")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        if api.lines[line_id].status == "suspended":
            raise ValueError(f"Line {line_id} is already suspended")
        return api.suspend_line(customer_id, line_id, reason)
    except Exception as e:
        raise e

@mcp.tool()
def resume_line(customer_id: str, line_id: str) -> dict:
    """Resume a suspended mobile line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        status (str): The new status of the line after resumption.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        if api.lines[line_id].status == "active":
            raise ValueError(f"Line {line_id} is already active")
        return api.resume_line(customer_id, line_id)
    except Exception as e:
        raise e

@mcp.tool()
def enable_roaming(customer_id: str, line_id: str) -> dict:
    """Enable international roaming on a mobile line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        roaming_enabled (bool): Indicates whether international roaming is now enabled on the line.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        if api.lines[line_id].roaming_enabled:
            raise ValueError(f"Roaming is already enabled on line {line_id}")
        return api.enable_roaming(customer_id, line_id)
    except Exception as e:
        raise e

@mcp.tool()
def disable_roaming(customer_id: str, line_id: str) -> dict:
    """Disable international roaming on a mobile line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        roaming_enabled (bool): Indicates whether international roaming is now disabled on the line.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        if not api.lines[line_id].roaming_enabled:
            raise ValueError(f"Roaming is already disabled on line {line_id}")
        return api.disable_roaming(customer_id, line_id)
    except Exception as e:
        raise e

@mcp.tool()
def refuel_data(customer_id: str, line_id: str, gb_amount: float) -> dict:
    """Add more data to a specific mobile line.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        line_id (str): The unique identifier of the mobile line.
        gb_amount (float): Amount of data to add in gigabytes.
    
    Returns:
        line_id (str): The unique identifier of the mobile line.
        new_data_refueling_gb (float): Updated total amount of refueled data in gigabytes.
        charge_amount (float): The cost charged for the additional data in the customer's currency.
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not line_id or not isinstance(line_id, str):
            raise ValueError("Line ID must be a non-empty string")
        if not isinstance(gb_amount, (int, float)) or gb_amount <= 0:
            raise ValueError("GB amount must be a positive number")
        if line_id not in api.lines:
            raise ValueError(f"Line {line_id} not found")
        if api.lines[line_id].customer_id != customer_id:
            raise ValueError(f"Line {line_id} does not belong to customer {customer_id}")
        return api.refuel_data(customer_id, line_id, gb_amount)
    except Exception as e:
        raise e

@mcp.tool()
def send_payment_request(customer_id: str, bill_id: str) -> dict:
    """Send a payment request to the customer for a specific bill.
    
    Args:
        customer_id (str): The unique identifier of the customer account.
        bill_id (str): The unique identifier of the billing statement.
    
    Returns:
        bill_id (str): The unique identifier of the billing statement.
        status (str): The current status of the payment request (e.g., 'sent', 'delivered', 'failed').
    """
    try:
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a non-empty string")
        if not bill_id or not isinstance(bill_id, str):
            raise ValueError("Bill ID must be a non-empty string")
        if bill_id not in api.bills:
            raise ValueError(f"Bill {bill_id} not found")
        if api.bills[bill_id].customer_id != customer_id:
            raise ValueError(f"Bill {bill_id} does not belong to customer {customer_id}")
        return api.send_payment_request(customer_id, bill_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()