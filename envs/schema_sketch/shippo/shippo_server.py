# Data Source: https://docs.goshippo.com/
# Server: ShippoServer
# Category: logistics


def validate_address(street1: str, city: str, state: str, zip_code: str, 
                    country: str = "US", street2: str = None) -> dict:
    """
    Validate a shipping address.
    
    Args:
        street1 (str): Street address line 1
        city (str): City name
        state (str): State/province code
        zip_code (str): ZIP/postal code
        country (str): [Optional] Country code (default: "US")
        street2 (str): [Optional] Street address line 2 (apartment, suite, etc.)
        
    Returns:
        dict: {
            "object_state": str,
            "validation_status": str,
            "is_valid": bool,
            "address": {
                "street1": str,
                "street2": str,
                "city": str,
                "state": str,
                "zip": str,
                "country": str
            },
            "messages": [str]
        }
    """
    pass


def get_shipping_rates(address_from: dict, address_to: dict, 
                       parcels: list, async_req: bool = False) -> dict:
    """
    Get real-time shipping rates from multiple carriers.
    
    Args:
        address_from (dict): Sender address {street1, city, state, zip, country, name, phone}
        address_to (dict): Recipient address {street1, city, state, zip, country, name, phone}
        parcels (list): List of parcel objects [{length, width, height, weight, distance_unit, mass_unit}]
        async_req (bool): [Optional] Return immediately and poll for results (default: False)
        
    Returns:
        dict: {
            "object_id": str,
            "object_status": str,
            "rates": [
                {
                    "object_id": str,
                    "provider": str,
                    "servicelevel": {"name": str, "token": str},
                    "amount": float,
                    "currency": str,
                    "days": int,
                    "duration_terms": str
                }
            ]
        }
    """
    pass


def create_shipping_label(rate_id: str, label_file_type: str = "PDF", 
                         async_req: bool = False, metadata: str = None) -> dict:
    """
    Purchase and create a shipping label.
    
    Args:
        rate_id (str): Shippo rate object ID (from get_shipping_rates)
        label_file_type (str): [Optional] Label format (PDF, PNG, ZPLII) (default: "PDF")
        async_req (bool): [Optional] Async processing (default: False)
        metadata (str): [Optional] Order metadata/reference
        
    Returns:
        dict: {
            "object_id": str,
            "status": str,
            "tracking_number": str,
            "tracking_status": str,
            "tracking_url_provider": str,
            "label_url": str,
            "rate": {
                "amount": float,
                "currency": str,
                "provider": str,
                "servicelevel_name": str
            },
            "eta": str
        }
    """
    pass


def track_shipment(carrier: str, tracking_number: str) -> dict:
    """
    Track a shipment using carrier and tracking number.
    
    Args:
        carrier (str): Carrier token (e.g., "usps", "ups", "fedex")
        tracking_number (str): Tracking number
        
    Returns:
        dict: {
            "tracking_number": str,
            "carrier": str,
            "status": str,
            "tracking_history": [
                {
                    "status": str,
                    "status_details": str,
                    "status_date": str,
                    "location": dict
                }
            ],
            "eta": str
        }
    """
    pass


def get_carriers() -> dict:
    """
    Get list of available shipping carriers.
    
    Returns:
        dict: {
            "results": [
                {
                    "carrier": str,
                    "account_id": str,
                    "parameters": dict,
                    "is_active": bool,
                    "is_test": bool
                }
            ]
        }
    """
    pass
