# Server Name: ChinaRailway

def get_stations_code_in_city(city: str) -> list:
    """
    通过城市名查询该城市所有车站的station_code。
    
    Args:
        city (str): 城市中文名称
        
    Returns:
        list: 包含该城市所有车站station_code和station_name的列表
            - station_code (str): 车站的station_code
            - station_name (str): 车站的中文名称
    """
    pass


def get_station_code_by_name(station_name: str) -> str:
    """
    通过车站名查询station_code，结果是唯一的。
    
    Args:
        station_name (str): 车站中文名称
        
    Returns:
        station_code (str): 车站对应的唯一station_code
    """
    pass

def get_station_by_code(station_code: str) -> dict:
    """
    通过station_code查询车站信息，结果是唯一的。
    
    Args:
        station_code (str): 车站的station_code
        
    Returns:
        dict: 包含车站信息的字典，包含以下字段：
            - station_name (str): 车站中文名称
            - address (str): 车站的地理位置或地址信息
            - phone (str): 车站的联系电话
    """
    pass

def get_tickets(date: str, from_station_code: str, to_station_code: str) -> dict:
    """
    查询12306余票信息。
    
    Args:
        date (str): 查询日期(格式: yyyy-mm-dd)
        from_station_code (str): 出发车站的station_code
        to_station_code (str): 到达车站的station_code
        
    Returns:
        dict: 包含余票信息的字典，包含以下字段：
            - trains (list): 可用车次列表，每个车次包含以下字段：
                - train_no (str): 车次编号
                - departure_time (str): 出发时间
                - arrival_time (str): 到达时间
                - duration (str): 运行时长
                - seat_availability (dict): 座位余票信息，包含以下字段：
                    - business_class (int): 商务座余票数量
                    - first_class (int): 一等座余票数量
                    - second_class (int): 二等座余票数量
    """
    pass

def get_train_route_stations(date: str, from_station_code: str, to_station_code: str, train_no: str) -> dict:
    """
    查询列车途径车站信息，包括所有停靠站及其到发时间。
    
    Args:
        date (str): 列车出发日期(格式: yyyy-mm-dd)
        from_station_code (str): 出发车站的station_code
        to_station_code (str): 到达车站的station_code
        train_no (str): 实际车次编号train_no，例如240000G10336
        
    Returns:
        dict: 包含列车途径车站信息的字典，包含以下字段：
            - route_stations (list): 途径车站列表，每个车站包含以下字段：
                - station_name (str): 车站中文名称
                - arrival_time (str): 到达时间
                - departure_time (str): 出发时间
                - stop_duration (str): 停靠时长
    """
    pass

