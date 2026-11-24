"""
Sensor simulator: pretends to be the store's hardware.

We don't have real scanners or smart shelves, so this script runs a small
pretend shop and sends the messages that hardware would send:

  checkout-1 scanner    a customer buys something              -> "sale"
  receiving-1 scanner   a delivery arrives for a low product   -> "restock"
  shelf-<id> sensors    every few steps, each shelf reports its count

Every so often an item goes missing without being scanned (theft or
breakage). The shelf sensors are how the system notices that.

Run it (from the repo root):
    python ml/simulator.py                   # send to the MQTT broker
    python ml/simulator.py --offline         # no broker needed: print each
                                             # message and apply it to an
                                             # in-memory stand-in backend
    python ml/simulator.py --steps 50 --interval 0.2 --seed 7
"""
import argparse
import logging
import random
import time

import paho.mqtt.client as mqtt

import config
from listener import StockUpdater
from messages import make_scan, make_shelf_reading
from stock_api import InMemoryStockAPI, StockAPI, StockAPIError

log = logging.getLogger("simulator")


class Store:
    """
    The pretend shop. Each call to step() moves time forward one tick and
    returns the (topic, payload) messages the devices would send.

    There is no networking in here, so the tests can run thousands of steps
    instantly and check the results.
    """

    def __init__(
        self,
        stock,
        rng=None,
        shelf_every=10,        # shelf sensors report every N ticks
        restock_below=5,       # order more when a product drops below this
        restock_amount=24,     # how many units a delivery brings
        shrink_chance=0.03,    # chance per tick that one item goes missing
    ):
        self.stock = dict(stock)   # {product_id: units physically on the shelf}
        self.rng = rng or random.Random()
        self.shelf_every = shelf_every
        self.restock_below = restock_below
        self.restock_amount = restock_amount
        self.shrink_chance = shrink_chance
        self.tick = 0

    def step(self):
        self.tick += 1
        messages = []

        # 1. A customer buys 1-3 units of something that's in stock
        in_stock = [pid for pid, qty in self.stock.items() if qty > 0]
        if in_stock:
            pid = self.rng.choice(in_stock)
            qty = self.rng.randint(1, min(3, self.stock[pid]))
            self.stock[pid] -= qty
            messages.append(make_scan("checkout-1", pid, "sale", qty))

        # 2. Any product running low gets a delivery, scanned in at the back
        for pid in self.stock:
            if self.stock[pid] < self.restock_below:
                self.stock[pid] += self.restock_amount
                messages.append(make_scan("receiving-1", pid, "restock", self.restock_amount))

        # 3. Sometimes an item disappears and nobody scans it. No message is
        #    sent; the next shelf reading will reveal it.
        if self.rng.random() < self.shrink_chance:
            in_stock = [pid for pid, qty in self.stock.items() if qty > 0]
            if in_stock:
                self.stock[self.rng.choice(in_stock)] -= 1

        # 4. Every few ticks, each shelf reports what's physically on it
        if self.tick % self.shelf_every == 0:
            for pid, qty in self.stock.items():
                messages.append(make_shelf_reading(f"shelf-{pid}", pid, qty))

        return messages


def load_starting_stock(api_url):
    """
    Start from the backend's real stock levels if it's running. Otherwise
    the first shelf readings would "correct" the database to made-up numbers.
    Falls back to the demo products if the backend can't be reached.
    """
    try:
        products = StockAPI(api_url).list_products()
        log.info("loaded %d products from %s", len(products), api_url)
        return {p["id"]: int(p["quantity"]) for p in products}
    except StockAPIError as error:
        log.warning("couldn't load products (%s); using demo products", error.detail)
        return {pid: qty for pid, (_name, qty) in config.DEMO_PRODUCTS.items()}


def run_with_broker(store, host, port, steps, interval):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(host, port)
    except OSError as error:
        raise SystemExit(
            f"Couldn't reach the MQTT broker at {host}:{port} ({error}). "
            "Is Mosquitto running? Or try --offline."
        )
    client.loop_start()   # a background thread handles the network traffic
    log.info("publishing to broker at %s:%s (Ctrl+C to stop)", host, port)

    try:
        for _ in _ticks(steps):
            for topic, payload in store.step():
                # QoS 1 = the broker confirms it got the message
                client.publish(topic, payload, qos=1).wait_for_publish(timeout=5)
                log.info("sent %s %s", topic, payload)
            time.sleep(interval)
    except KeyboardInterrupt:
        log.info("stopping")
    finally:
        client.disconnect()
        client.loop_stop()


def run_offline(store, steps, interval):
    """Skip MQTT: hand each message straight to the listener's logic, which
    updates an in-memory stand-in for the backend."""
    api = InMemoryStockAPI(
        {pid: (config.DEMO_PRODUCTS.get(pid, (f"Product {pid}", 0))[0], qty)
         for pid, qty in store.stock.items()}
    )
    updater = StockUpdater(api)
    try:
        for _ in _ticks(steps):
            for topic, payload in store.step():
                log.info("sent %s %s", topic, payload)
                updater.handle(topic, payload)
            time.sleep(interval)
    except KeyboardInterrupt:
        log.info("stopping")


def _ticks(steps):
    """Count 0, 1, 2, ... up to `steps`, or forever if steps is None."""
    tick = 0
    while steps is None or tick < steps:
        yield tick
        tick += 1


def main():
    parser = argparse.ArgumentParser(description="NStock sensor simulator")
    parser.add_argument("--broker", default=config.MQTT_HOST, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=config.MQTT_PORT, help="MQTT broker port")
    parser.add_argument("--api-url", default=config.API_URL, help="backend URL to load starting stock from")
    parser.add_argument("--offline", action="store_true", help="no broker or backend; print and apply messages locally")
    parser.add_argument("--steps", type=int, default=None, help="stop after this many ticks (default: run forever)")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between ticks")
    parser.add_argument("--shelf-every", type=int, default=10, help="shelf sensors report every N ticks")
    parser.add_argument("--shrink-chance", type=float, default=0.03, help="chance per tick of an unscanned loss")
    parser.add_argument("--seed", type=int, default=None, help="random seed, for repeatable runs")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.offline:
        starting_stock = {pid: qty for pid, (_name, qty) in config.DEMO_PRODUCTS.items()}
    else:
        starting_stock = load_starting_stock(args.api_url)

    store = Store(
        starting_stock,
        rng=random.Random(args.seed),
        shelf_every=args.shelf_every,
        shrink_chance=args.shrink_chance,
    )

    if args.offline:
        run_offline(store, args.steps, args.interval)
    else:
        run_with_broker(store, args.broker, args.port, args.steps, args.interval)


if __name__ == "__main__":
    main()
