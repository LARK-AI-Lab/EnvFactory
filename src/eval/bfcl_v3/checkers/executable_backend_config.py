"""BFCL v3 executable backend mapping."""

from __future__ import annotations

BACKEND_PATH_PREFIX = "src.eval.bfcl_v3.func_source_code"

CLASS_FILE_PATH_MAPPING = {
    "GorillaFileSystem": BACKEND_PATH_PREFIX + ".gorilla_file_system",
    "MathAPI": BACKEND_PATH_PREFIX + ".math_api",
    "MessageAPI": BACKEND_PATH_PREFIX + ".message_api",
    "TwitterAPI": BACKEND_PATH_PREFIX + ".posting_api",
    "TicketAPI": BACKEND_PATH_PREFIX + ".ticket_api",
    "TradingBot": BACKEND_PATH_PREFIX + ".trading_bot",
    "TravelAPI": BACKEND_PATH_PREFIX + ".travel_booking",
    "VehicleControlAPI": BACKEND_PATH_PREFIX + ".vehicle_control",
}

STATELESS_CLASSES = ["MathAPI"]
