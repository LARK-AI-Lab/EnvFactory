from pydantic import BaseModel, Field
from typing import Dict, List
from mcp.server.fastmcp import FastMCP
import uuid

# Section 1: Schema
class PriceEstimate(BaseModel):
    """Represents a price estimate response."""
    priceToken: str = Field(..., description="Temporary price token for order creation")
    needPayMoney: float = Field(..., ge=0, description="Estimated delivery fee in CNY")

class Order(BaseModel):
    """Represents a delivery order."""
    orderCode: str = Field(..., description="UU platform unique order code")
    fromAddress: str = Field(..., description="Pickup address")
    toAddress: str = Field(..., description="Delivery address")
    state: str = Field(..., description="Order status")
    createdAt: str = Field(..., description="Order creation time in ISO 8601 format")
    receiverPhone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Receiver phone number")
    senderPhone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Sender phone number")
    distance: float = Field(..., ge=0, description="Distance in kilometers")
    sendType: str = Field(..., description="Delivery type: instant or scheduled")
    adCode: str = Field(..., pattern=r"^\d{6}$", description="6-digit administrative division code")

class CancelResult(BaseModel):
    """Represents order cancellation result."""
    orderCode: str = Field(..., description="Cancelled order code")
    deductFee: int = Field(..., ge=0, description="Deduction fee in cents")

class UUPaoTuiScenario(BaseModel):
    """Main scenario model for UU跑腿 delivery service."""
    orders: Dict[str, Order] = Field(default={}, description="All orders keyed by orderCode")
    priceTokens: Dict[str, dict] = Field(default={}, description="Active price tokens mapping")
    baseRatesMap: Dict[str, float] = Field(default={
        "instant": 8.0, "scheduled": 6.0, "per_km": 2.5, "per_min": 0.5
    }, description="Base delivery rates")
    cityMultipliersMap: Dict[str, float] = Field(default={
        "110100": 1.2, "310100": 1.3, "440100": 1.1, "440300": 1.1, "330100": 1.0,
        "320100": 1.0, "420100": 0.9, "510100": 0.9, "500100": 1.0, "120100": 1.0,
        "210100": 0.8, "230100": 0.8, "610100": 0.8, "620100": 0.8, "630100": 0.8,
        "640100": 0.8, "650100": 0.8, "710100": 1.0, "810100": 1.0, "820100": 1.0
    }, description="City price multipliers by adCode")
    orderStates: List[str] = Field(default=[
        "待接单", "配送中", "已完成", "已取消", "异常订单"
    ], description="Possible order states")
    current_time: str = Field(default="2024-01-01T00:00:00", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [PriceEstimate, Order, CancelResult, UUPaoTuiScenario]

# Section 2: Class
class UUPaoTuiAPI:
    def __init__(self):
        """Initialize UU跑腿 API with empty state."""
        self.orders: Dict[str, Order] = {}
        self.priceTokens: Dict[str, dict] = {}
        self.baseRatesMap: Dict[str, float] = {}
        self.cityMultipliersMap: Dict[str, float] = {}
        self.orderStates: List[str] = []
        self.current_time: str = "2024-01-01T00:00:00"
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = UUPaoTuiScenario(**scenario)
        self.orders = model.orders
        self.priceTokens = model.priceTokens
        self.baseRatesMap = model.baseRatesMap
        self.cityMultipliersMap = model.cityMultipliersMap
        self.orderStates = model.orderStates
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "orders": {code: order.model_dump() for code, order in self.orders.items()},
            "priceTokens": self.priceTokens,
            "baseRatesMap": self.baseRatesMap,
            "cityMultipliersMap": self.cityMultipliersMap,
            "orderStates": self.orderStates,
            "current_time": self.current_time
        }

    def _calculate_distance(self, from_addr: str, to_addr: str) -> float:
        """Calculate distance between addresses (simplified)."""
        # Simple hash-based distance calculation for demo
        combined = f"{from_addr}|{to_addr}"
        return round((hash(combined) % 50) + 1, 1)

    def _get_multiplier(self, adCode: str) -> float:
        """Get city price multiplier."""
        return self.cityMultipliersMap.get(adCode, 1.0)

    def estimate_price(self, fromAddress: str, toAddress: str, adCode: str, sendType: str) -> dict:
        """Estimate delivery price and generate price token."""
        distance = self._calculate_distance(fromAddress, toAddress)
        multiplier = self._get_multiplier(adCode)
        
        base_fee = self.baseRatesMap.get(sendType, 8.0)
        distance_fee = distance * self.baseRatesMap.get("per_km", 2.5)
        total_fee = round((base_fee + distance_fee) * multiplier, 2)
        
        price_token = str(uuid.uuid4())
        
        # Store token info for later order creation
        self.priceTokens[price_token] = {
            "fromAddress": fromAddress,
            "toAddress": toAddress,
            "adCode": adCode,
            "sendType": sendType,
            "distance": distance,
            "needPayMoney": total_fee,
            "timestamp": self.current_time
        }
        
        return {"priceToken": price_token, "needPayMoney": total_fee}

    def create_order(self, priceToken: str, receiverPhone: str, senderPhone: str) -> dict:
        """Create order using price token."""
        if priceToken not in self.priceTokens:
            raise ValueError("Invalid or expired price token")
        
        token_info = self.priceTokens[priceToken]
        # Generate order code using current_time
        time_hash = hash(self.current_time) % 100000
        order_code = f"UU{time_hash}{hash(priceToken) % 10000:04d}"
        
        order = Order(
            orderCode=order_code,
            fromAddress=token_info["fromAddress"],
            toAddress=token_info["toAddress"],
            state=self.orderStates[0],  # 待接单
            createdAt=self.current_time,
            receiverPhone=receiverPhone,
            senderPhone=senderPhone,
            distance=token_info["distance"],
            sendType=token_info["sendType"],
            adCode=token_info["adCode"]
        )
        
        self.orders[order_code] = order
        del self.priceTokens[priceToken]  # Consume token
        
        return {"orderCode": order_code}

    def list_orders(self) -> dict:
        """List all orders."""
        order_list = []
        for order in self.orders.values():
            order_list.append({
                "orderCode": order.orderCode,
                "fromAddress": order.fromAddress,
                "toAddress": order.toAddress,
                "state": order.state,
                "createdAt": order.createdAt
            })
        return {"order_list": order_list}

    def query_order(self, orderCode: str) -> dict:
        """Query order details."""
        if orderCode not in self.orders:
            raise ValueError(f"Order {orderCode} not found")
        
        order = self.orders[orderCode]
        return {
            "orderCode": order.orderCode,
            "fromAddress": order.fromAddress,
            "toAddress": order.toAddress,
            "distance": order.distance,
            "state": order.state
        }

    def cancel_order(self, orderCode: str, reason: str) -> dict:
        """Cancel order and return deduction fee."""
        if orderCode not in self.orders:
            raise ValueError(f"Order {orderCode} not found")
        
        order = self.orders[orderCode]
        
        # Simple deduction logic: 10% if not completed
        deduct_fee = 0
        if order.state not in ["已完成", "已取消"]:
            deduct_fee = int(self.baseRatesMap.get("instant", 8.0) * 10)
        
        order.state = "已取消"
        return {"orderCode": orderCode, "deductFee": deduct_fee}

# Section 3: MCP Tools
mcp = FastMCP(name="UUPaoTui")
api = UUPaoTuiAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the UU跑腿 API."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current UU跑腿 state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def estimate_price(fromAddress: str, toAddress: str, adCode: str, sendType: str) -> dict:
    """Estimate delivery price and generate price token.
    
    Args:
        fromAddress (str): Pickup address for distance calculation.
        toAddress (str): Delivery address for distance calculation.
        adCode (str): 6-digit administrative division code.
        sendType (str): Delivery type: instant or scheduled.
    
    Returns:
        priceToken (str): Temporary price token for order creation.
        needPayMoney (float): Estimated delivery fee in CNY.
    """
    try:
        if not fromAddress or not isinstance(fromAddress, str):
            raise ValueError("fromAddress must be a non-empty string")
        if not toAddress or not isinstance(toAddress, str):
            raise ValueError("toAddress must be a non-empty string")
        if not adCode or not isinstance(adCode, str):
            raise ValueError("adCode must be a non-empty string")
        if sendType not in ["instant", "scheduled"]:
            raise ValueError("sendType must be 'instant' or 'scheduled'")
        return api.estimate_price(fromAddress, toAddress, adCode, sendType)
    except Exception as e:
        raise e

@mcp.tool()
def create_order(priceToken: str, receiverPhone: str, senderPhone: str) -> dict:
    """Create order using price token.
    
    Args:
        priceToken (str): Price token from estimate_price.
        receiverPhone (str): Receiver phone number.
        senderPhone (str): Sender phone number.
    
    Returns:
        orderCode (str): UU platform unique order code.
    """
    try:
        if not priceToken or not isinstance(priceToken, str):
            raise ValueError("priceToken must be a non-empty string")
        return api.create_order(priceToken, receiverPhone, senderPhone)
    except Exception as e:
        raise e

@mcp.tool()
def list_orders() -> dict:
    """List all orders for current account.
    
    Returns:
        order_list (list): Array of order summaries.
    """
    try:
        return api.list_orders()
    except Exception as e:
        raise e

@mcp.tool()
def query_order(orderCode: str) -> dict:
    """Query order details by order code.
    
    Args:
        orderCode (str): UU platform unique order code.
    
    Returns:
        orderCode (str): Order code.
        fromAddress (str): Pickup address.
        toAddress (str): Delivery address.
        distance (float): Distance in kilometers.
        state (str): Current order status.
    """
    try:
        if not orderCode or not isinstance(orderCode, str):
            raise ValueError("orderCode must be a non-empty string")
        return api.query_order(orderCode)
    except Exception as e:
        raise e

@mcp.tool()
def cancel_order(orderCode: str, reason: str) -> dict:
    """Cancel order and return deduction fee.
    
    Args:
        orderCode (str): UU platform unique order code.
        reason (str): Cancellation reason.
    
    Returns:
        orderCode (str): Cancelled order code.
        deductFee (int): Deduction fee in cents.
    """
    try:
        if not orderCode or not isinstance(orderCode, str):
            raise ValueError("orderCode must be a non-empty string")
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be a non-empty string")
        return api.cancel_order(orderCode, reason)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()