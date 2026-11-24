"""
MQTT listener: receives device messages and updates stock through the API.

What happens to each message:

  scanner "sale"     ->  POST /stock-transactions  OUT  (stock goes down)
  scanner "restock"  ->  POST /stock-transactions  IN   (stock goes up)
  shelf reading      ->  compare the shelf count with the database. If they
                         differ (something was stolen, broken or miscounted
                         and never scanned), set the database to the real
                         count with PUT /products/{id}. The backend records
                         that as an "adjustment".

Scanners report what happened, and shelf sensors check what's actually
there. Because the two jobs are separate, a sale is never counted twice.

Run it (from the repo root):
    python ml/listener.py              # update the real backend
    python ml/listener.py --dry-run    # update a stand-in backend in memory
"""
import argparse
import logging
import threading
from collections import namedtuple

import paho.mqtt.client as mqtt

import config
from messages import SCANNER_TOPICS, SHELF_TOPICS, ScanEvent, parse
from stock_api import InMemoryStockAPI, StockAPI, StockAPIError

log = logging.getLogger("listener")

# What happened to one message:
#   status is "applied" (stock changed), "unchanged" (shelf matched the
#   database) or "skipped" (bad message, or the backend said no)
Outcome = namedtuple("Outcome", ["status", "detail"])


class StockUpdater:
    """
    Turns one device message into the right API call.

    There is no MQTT code in here, so the tests can call handle() directly
    without a broker running.
    """

    def __init__(self, api):
        self.api = api

    def handle(self, topic, payload):
        """Process one message. Never raises: a bad message or a refused
        update is logged and skipped so the listener keeps running."""
        try:
            message = parse(topic, payload)
        except ValueError as error:
            return self._report("skipped", f"bad message on {topic}: {error}")

        try:
            if isinstance(message, ScanEvent):
                return self._apply_scan(message)
            return self._apply_shelf_reading(message)
        except StockAPIError as error:
            return self._report(
                "skipped",
                f"backend refused update for product {message.product_id} "
                f"from {topic}: {error.detail}",
            )

    def _apply_scan(self, scan):
        transaction_type = "OUT" if scan.action == "sale" else "IN"
        new_stock = self.api.record_transaction(
            scan.product_id, scan.quantity, transaction_type
        )
        return self._report(
            "applied",
            f"{scan.scanner_id}: {scan.action} {scan.quantity} of product "
            f"{scan.product_id}, stock now {new_stock}",
        )

    def _apply_shelf_reading(self, reading):
        product = self.api.get_product(reading.product_id)
        recorded = int(product["quantity"])

        if recorded == reading.count:
            return self._report(
                "unchanged",
                f"{reading.shelf_id}: product {reading.product_id} matches ({recorded})",
                level=logging.DEBUG,
            )

        self.api.set_quantity(reading.product_id, product["name"], reading.count)
        return self._report(
            "applied",
            f"{reading.shelf_id}: product {reading.product_id} corrected "
            f"{recorded} -> {reading.count} ({reading.count - recorded:+d})",
        )

    def _report(self, status, detail, level=None):
        if level is None:
            level = logging.WARNING if status == "skipped" else logging.INFO
        log.log(level, detail)
        return Outcome(status, detail)


def create_client(updater):
    """
    Build an MQTT client that feeds every scanner and shelf message to
    `updater`. Call client.connect(...) and then a loop method to start it.

    client.user_data_get()["subscribed"] is a threading.Event that is set
    once the subscription is active (the broker-based test waits on it).
    """
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        userdata={"subscribed": threading.Event()},
    )

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("broker refused the connection: %s", reason_code)
            return
        # Subscribing here (not just once at start-up) means we subscribe
        # again automatically if the connection drops and comes back.
        client.subscribe([(SCANNER_TOPICS, 1), (SHELF_TOPICS, 1)])

    def on_subscribe(client, userdata, mid, reason_codes, properties):
        log.info("listening on %s and %s", SCANNER_TOPICS, SHELF_TOPICS)
        userdata["subscribed"].set()

    def on_message(client, userdata, msg):
        updater.handle(msg.topic, msg.payload)

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    return client


def main():
    parser = argparse.ArgumentParser(description="NStock MQTT listener")
    parser.add_argument("--broker", default=config.MQTT_HOST, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=config.MQTT_PORT, help="MQTT broker port")
    parser.add_argument("--api-url", default=config.API_URL, help="NStock backend URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="don't call the backend; keep stock in memory instead",
    )
    parser.add_argument("--verbose", action="store_true", help="also log shelf readings that match")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.dry_run:
        api = InMemoryStockAPI(config.DEMO_PRODUCTS)
        log.info("dry run: using in-memory stock for %d demo products", len(config.DEMO_PRODUCTS))
    else:
        api = StockAPI(args.api_url)
        log.info("sending stock updates to %s", args.api_url)

    client = create_client(StockUpdater(api))
    log.info("connecting to broker at %s:%s (Ctrl+C to stop)", args.broker, args.port)
    try:
        client.connect(args.broker, args.port)
    except OSError as error:
        raise SystemExit(
            f"Couldn't reach the MQTT broker at {args.broker}:{args.port} ({error}). "
            "Is Mosquitto running?"
        )

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        log.info("stopping")
        client.disconnect()


if __name__ == "__main__":
    main()
