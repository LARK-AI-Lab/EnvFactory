# Data Source: https://www.nps.gov/subjects/developer/get-started.htm
# Server: NationalParks
# Category: Parks & Recreation


def findParks(stateCode: str = None, q: str = None, limit: int = 10,
              start: int = 0, activities: str = None) -> dict:
    """
    Search National Park Service parks by state, text query, or activities.

    Args:
        stateCode (str): [Optional] State code filter, with multiple states comma-separated
        q (str): [Optional] Search term for park name or description
        limit (int): [Optional] Maximum number of parks to return
        start (int): [Optional] Result offset for pagination
        activities (str): [Optional] Comma-separated activity names or IDs

    Returns:
        dict: {
            "total": int,
            "limit": int,
            "start": int,
            "data": list[{
                "parkCode": str,
                "fullName": str,
                "states": str,
                "description": str,
                "activities": list[dict]
            }]
        }
    """
    pass


def getParkDetails(parkCode: str) -> dict:
    """
    Get detailed information for a National Park Service park.

    Args:
        parkCode (str): NPS park code such as "yose", "grca", or "yell"

    Returns:
        dict: {
            "parkCode": str,
            "fullName": str,
            "description": str,
            "directionsInfo": str,
            "operatingHours": list[dict],
            "entranceFees": list[dict],
            "contacts": dict,
            "addresses": list[dict]
        }
    """
    pass


def getAlerts(parkCode: str = None, limit: int = 10, start: int = 0,
              q: str = None) -> dict:
    """
    Get current alerts for parks, including closures, hazards, and notices.

    Args:
        parkCode (str): [Optional] One park code or comma-separated park codes
        limit (int): [Optional] Maximum number of alerts to return
        start (int): [Optional] Result offset for pagination
        q (str): [Optional] Search term for alert title or description

    Returns:
        dict: {
            "total": int,
            "data": list[{
                "id": str,
                "parkCode": str,
                "title": str,
                "description": str,
                "category": str,
                "lastIndexedDate": str
            }]
        }
    """
    pass


def getCampgrounds(parkCode: str = None, limit: int = 10,
                   start: int = 0, q: str = None) -> dict:
    """
    Get campground information for one or more parks.

    Args:
        parkCode (str): [Optional] One park code or comma-separated park codes
        limit (int): [Optional] Maximum number of campgrounds to return
        start (int): [Optional] Result offset for pagination
        q (str): [Optional] Search term for campground name or description

    Returns:
        dict: {
            "total": int,
            "data": list[{
                "id": str,
                "name": str,
                "parkCode": str,
                "description": str,
                "amenities": dict,
                "fees": list[dict],
                "reservationUrl": str
            }]
        }
    """
    pass


def getVisitorCenters(parkCode: str = None, limit: int = 10,
                      start: int = 0, q: str = None) -> dict:
    """
    Get visitor center information and operating details.

    Args:
        parkCode (str): [Optional] One park code or comma-separated park codes
        limit (int): [Optional] Maximum number of visitor centers to return
        start (int): [Optional] Result offset for pagination
        q (str): [Optional] Search term for visitor center name or description

    Returns:
        dict: {
            "total": int,
            "data": list[{
                "id": str,
                "name": str,
                "parkCode": str,
                "description": str,
                "operatingHours": list[dict],
                "contacts": dict,
                "addresses": list[dict]
            }]
        }
    """
    pass

