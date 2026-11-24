"""
Settings shared by the simulator and the listener.

Each value can be overridden with an environment variable, so teammates can
point the scripts at their own broker or backend without editing code.
"""
import os

# Where the Mosquitto broker is running
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Where the FastAPI backend is running
API_URL = os.getenv("NSTOCK_API_URL", "http://127.0.0.1:8000")

# Every NStock topic starts with this, e.g. "nstock/scanner/checkout-1"
TOPIC_ROOT = "nstock"

# The active products from database/nstock_seed.sql and how many of each
# the seed data leaves on hand: {product_id: (name, on_hand)}.
# Used when the backend isn't running (offline demo, unit tests).
DEMO_PRODUCTS = {
    1: ("Sparkling Water 12oz", 16),
    2: ("Cold Brew Coffee 11oz", 16),
    3: ("Orange Juice 16oz", 4),
    4: ("Green Tea 16oz", 23),
    5: ("Trail Mix 6oz", 8),
    6: ("Kettle Chips 2oz", 29),
    7: ("Protein Bar", 27),
    8: ("Dark Chocolate Bar", 10),
    9: ("Paper Towels 2pk", 14),
    10: ("Dish Soap 16oz", 5),
    11: ("Trash Bags 20ct", 18),
    12: ("Hand Sanitizer 8oz", 18),
    13: ("Toothpaste 4oz", 24),
    14: ("Lip Balm", 16),
}
