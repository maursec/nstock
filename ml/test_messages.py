"""Tests for the message formats: good messages parse, bad ones are rejected."""
import json

import pytest

from messages import (
    ScanEvent,
    ShelfReading,
    make_scan,
    make_shelf_reading,
    parse,
)


def test_scan_round_trip():
    topic, payload = make_scan("checkout-1", 3, "sale", 2)
    assert topic == "nstock/scanner/checkout-1"

    event = parse(topic, payload)
    assert isinstance(event, ScanEvent)
    assert (event.scanner_id, event.product_id, event.action, event.quantity) == (
        "checkout-1", 3, "sale", 2,
    )


def test_shelf_round_trip():
    topic, payload = make_shelf_reading("shelf-7", 7, 0)
    assert topic == "nstock/shelf/shelf-7"

    reading = parse(topic, payload)
    assert isinstance(reading, ShelfReading)
    assert (reading.shelf_id, reading.product_id, reading.count) == ("shelf-7", 7, 0)


def test_payload_can_be_bytes():
    # paho-mqtt hands the listener bytes, not str
    reading = parse("nstock/shelf/s1", b'{"product_id": 1, "count": 5}')
    assert reading.count == 5


def test_missing_timestamp_is_filled_in():
    event = parse("nstock/scanner/x", '{"product_id": 1, "action": "restock", "quantity": 4}')
    assert event.timestamp


@pytest.mark.parametrize(
    "payload, reason",
    [
        ("not json", "not valid JSON"),
        (b"\xff\xfe\xfa", "not valid JSON"),
        ("[1, 2]", "JSON object"),
        ({"action": "sale", "quantity": 1}, "product_id"),
        ({"product_id": 0, "action": "sale", "quantity": 1}, "product_id"),
        ({"product_id": "3", "action": "sale", "quantity": 1}, "product_id"),
        ({"product_id": True, "action": "sale", "quantity": 1}, "product_id"),
        ({"product_id": 3, "action": "steal", "quantity": 1}, "action"),
        ({"product_id": 3, "quantity": 1}, "action"),
        ({"product_id": 3, "action": "sale", "quantity": 0}, "quantity"),
        ({"product_id": 3, "action": "sale", "quantity": -2}, "quantity"),
        ({"product_id": 3, "action": "sale", "quantity": 1.5}, "quantity"),
    ],
)
def test_bad_scanner_payloads_are_rejected(payload, reason):
    if isinstance(payload, dict):
        payload = json.dumps(payload)
    with pytest.raises(ValueError, match=reason):
        parse("nstock/scanner/checkout-1", payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": 3},
        {"product_id": 3, "count": -1},
        {"product_id": 3, "count": "12"},
    ],
)
def test_bad_shelf_payloads_are_rejected(payload):
    with pytest.raises(ValueError, match="count"):
        parse("nstock/shelf/shelf-3", json.dumps(payload))


@pytest.mark.parametrize(
    "topic",
    [
        "other/scanner/x",
        "nstock/scanner",
        "nstock/scanner/",
        "nstock/scanner/a/b",
        "nstock/camera/x",
    ],
)
def test_unknown_topics_are_rejected(topic):
    with pytest.raises(ValueError):
        parse(topic, '{"product_id": 1, "action": "sale", "quantity": 1, "count": 1}')
