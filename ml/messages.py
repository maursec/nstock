"""
MQTT topics and message formats for NStock devices.

An MQTT topic works like a mailing address. A device publishes (sends) a
message to a topic, and every program subscribed to that topic receives it.
Messages are JSON.

Barcode scanner  ->  nstock/scanner/<scanner_id>
    {"product_id": 3, "action": "sale", "quantity": 1, "timestamp": "..."}
    action is "sale" (stock goes down) or "restock" (stock goes up).

Shelf sensor     ->  nstock/shelf/<shelf_id>
    {"product_id": 3, "count": 37, "timestamp": "..."}
    count is how many units are physically on the shelf right now.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from config import TOPIC_ROOT

# "+" is an MQTT wildcard for exactly one level, so these match every
# scanner and every shelf sensor.
SCANNER_TOPICS = f"{TOPIC_ROOT}/scanner/+"
SHELF_TOPICS = f"{TOPIC_ROOT}/shelf/+"

SCAN_ACTIONS = ("sale", "restock")


@dataclass
class ScanEvent:
    scanner_id: str
    product_id: int
    action: str       # "sale" or "restock"
    quantity: int     # always 1 or more
    timestamp: str


@dataclass
class ShelfReading:
    shelf_id: str
    product_id: int
    count: int        # 0 or more
    timestamp: str


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def scanner_topic(scanner_id):
    return f"{TOPIC_ROOT}/scanner/{scanner_id}"


def shelf_topic(shelf_id):
    return f"{TOPIC_ROOT}/shelf/{shelf_id}"


def make_scan(scanner_id, product_id, action, quantity=1):
    """Build the (topic, payload) a barcode scanner would send."""
    payload = {
        "product_id": product_id,
        "action": action,
        "quantity": quantity,
        "timestamp": now(),
    }
    return scanner_topic(scanner_id), json.dumps(payload)


def make_shelf_reading(shelf_id, product_id, count):
    """Build the (topic, payload) a shelf sensor would send."""
    payload = {"product_id": product_id, "count": count, "timestamp": now()}
    return shelf_topic(shelf_id), json.dumps(payload)


def parse(topic, payload):
    """
    Turn a raw MQTT message into a ScanEvent or a ShelfReading.

    Raises ValueError with a readable reason if anything is wrong, so the
    listener can log a bad message and move on instead of crashing.
    """
    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != TOPIC_ROOT or not parts[2]:
        raise ValueError(f"unknown topic {topic!r}")
    device_type, device_id = parts[1], parts[2]

    try:
        data = json.loads(payload)
    except ValueError:  # bad JSON or bytes that aren't text
        raise ValueError("payload is not valid JSON") from None
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")

    product_id = _whole_number(data, "product_id", minimum=1)
    timestamp = str(data.get("timestamp") or now())

    if device_type == "scanner":
        action = data.get("action")
        if action not in SCAN_ACTIONS:
            raise ValueError(f"action must be 'sale' or 'restock', got {action!r}")
        quantity = _whole_number(data, "quantity", minimum=1)
        return ScanEvent(device_id, product_id, action, quantity, timestamp)

    if device_type == "shelf":
        count = _whole_number(data, "count", minimum=0)
        return ShelfReading(device_id, product_id, count, timestamp)

    raise ValueError(f"unknown device type {device_type!r}")


def _whole_number(data, field, minimum):
    value = data.get(field)
    # In Python, True/False count as ints, so rule them out explicitly
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be a whole number, got {value!r}")
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}, got {value}")
    return value
