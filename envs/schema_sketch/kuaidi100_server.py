# Server: Kuaidi100

def query_trace(kuaidi_num: str, phone: str = None) -> dict:
    """
    Query logistics tracking information for a package.
    
    Args:
        kuaidi_num (str): Tracking number to query
        phone (str): [Optional] Phone number, required when courier is SF Express (shunfeng)
        
    Returns:
        dict: {
            "kuaidi_num": str,
            "kuaidi_company": str,
            "data": list of dicts with time, context
        }
    """
    pass

def estimate_time(from_addr: str, kuaidi_company: str, to_addr: str, exp_type: str = None, order_time: str = None, logistic: str = None) -> dict:
    """
    Estimate delivery time based on courier company, origin/destination addresses, order time and service type.
    For in-transit packages, historical tracking data can be provided for more accurate prediction.
    
    Args:
        from_addr (str): Origin address (must include 3 levels), e.g., "广东省深圳市南山区". If province/city/district info is missing, complete it
        kuaidi_company (str): Courier company code in lowercase. Supported: shunfeng, jd, debangkuaidi, yuantong, zhongtong, shentong, yunda, ems
        to_addr (str): Destination address (must include 3 levels), e.g., "北京市海淀区". If province/city/district info is missing, complete it.
        exp_type (str): [Optional] Service or product type, enum: "标准快递", "经济快递", "特快专递"
        order_time (str): [Optional] Order time in format yyyy-MM-dd HH:mm:ss, e.g., "2023-08-08 08:08:08". Defaults to current time if not provided. Note: if tomorrow or day after tomorrow is specified, calculate from today as base
        logistic (str): [Optional] Historical tracking data for predicting remaining transit time for in-transit packages. Format: JSON array string, e.g., [{"time":"2025-05-09 13:15:26","context":"您的快件离开【吉林省吉林市桦甸市】，已发往【长春转运中心】"},{"time":"2025-05-09 12:09:38","context":"您的快件在【吉林省吉林市桦甸市】 已揽收"}]. time is tracking node timestamp, context is description at that node
        
    Returns:
        dict: {
            "arrivalTime": str,
            "remaining_transit_time": int
        }
    """
    pass

def estimate_price(kuaidi_company: str, from_addr: str, to_addr: str, weight: str = "1.0") -> dict:
    """
    Estimate shipping cost based on courier company, origin/destination addresses and weight.
    
    Args:
        kuaidi_company (str): Courier company code in lowercase. Supported: shunfeng, jd, debangkuaidi, yuantong, zhongtong, shentong, yunda, ems
        from_addr (str): Origin address (must include 3 levels), e.g., "广东省深圳市南山区". If province/city/district info is missing, complete it
        to_addr (str): Destination address (must include 3 levels), e.g., "北京市海淀区". If province/city/district info is missing, complete it. If user doesn't provide destination, don't call service and ask user for destination
        weight (str): [Optional] Weight in kg, no unit needed in parameter, e.g., "1.0". Default weight is 1kg
        
    Returns:
        dict: {
            "price": float,
            "currency": str,
            "estimated_days": int
        }
    """
    pass

