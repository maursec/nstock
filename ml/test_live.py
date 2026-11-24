"""
Tests against real running services. Each one skips itself when its
service isn't up, so `pytest ml` always works.

  test_message_travels_through_broker   needs Mosquitto
  test_backend_stock_round_trip         needs the backend + MySQL
"""
import socket
import time

import paho.mqtt.client as mqtt
import pytest

import config
from listener import StockUpdater, create_client
from messages import make_scan
from stock_api import InMemoryStockAPI, StockAPI, StockAPIError


def broker_is_up():
    try:
        socket.create_connection((config.MQTT_HOST, config.MQTT_PORT), timeout=1).close()
        return True
    except OSError:
        return False


@pytest.mark.skipif(not broker_is_up(), reason="no MQTT broker running")
def test_message_travels_through_broker():
    # A product id that doesn't exist in the real database: if a real
    # listener is also running, it rejects this message and changes nothing.
    product_id = 987654
    api = InMemoryStockAPI({product_id: ("Broker test item", 10)})

    listener = create_client(StockUpdater(api))
    listener.connect(config.MQTT_HOST, config.MQTT_PORT)
    listener.loop_start()
    sender = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        assert listener.user_data_get()["subscribed"].wait(5), "listener never subscribed"

        sender.connect(config.MQTT_HOST, config.MQTT_PORT)
        sender.loop_start()
        topic, payload = make_scan("test-scanner", product_id, "sale", 3)
        sender.publish(topic, payload, qos=1).wait_for_publish(timeout=5)

        deadline = time.time() + 5
        while api.get_product(product_id)["quantity"] != 7 and time.time() < deadline:
            time.sleep(0.05)
        assert api.get_product(product_id)["quantity"] == 7
    finally:
        sender.disconnect()
        sender.loop_stop()
        listener.disconnect()
        listener.loop_stop()


def backend_is_up():
    try:
        StockAPI(config.API_URL, timeout=2).list_products()
        return True
    except StockAPIError:
        return False


@pytest.mark.skipif(not backend_is_up(), reason="backend not running at " + config.API_URL)
def test_backend_stock_round_trip():
    api = StockAPI(config.API_URL)
    product = api.list_products()[0]
    start = int(product["quantity"])

    # Add 2 then remove 2, so the database ends where it started
    assert api.record_transaction(product["id"], 2, "IN") == start + 2
    assert api.record_transaction(product["id"], 2, "OUT") == start
    assert int(api.get_product(product["id"])["quantity"]) == start

    # The backend should refuse to sell more than it has
    with pytest.raises(StockAPIError) as refused:
        api.record_transaction(product["id"], start + 1, "OUT")
    assert refused.value.status == 400
