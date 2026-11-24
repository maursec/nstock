"""
Tests for the simulator, plus the "stock math" check: run the pretend shop
through the listener and confirm the backend's numbers match the shelves.
"""
import random

import config
from listener import StockUpdater
from messages import ScanEvent, ShelfReading, parse
from simulator import Store
from stock_api import InMemoryStockAPI

START = {pid: qty for pid, (_name, qty) in config.DEMO_PRODUCTS.items()}


def make_store(seed=1, **options):
    return Store(START, rng=random.Random(seed), **options)


def test_every_message_is_valid():
    store = make_store()
    for _ in range(300):
        for topic, payload in store.step():
            parse(topic, payload)  # raises if the format is wrong


def test_stock_never_goes_negative():
    store = make_store(shrink_chance=0.5)
    for _ in range(1000):
        store.step()
        assert all(qty >= 0 for qty in store.stock.values())


def test_same_seed_gives_same_run():
    def run(seed):
        store = make_store(seed)
        # drop the timestamp so runs a second apart still compare equal
        return [
            (topic, {k: v for k, v in vars(parse(topic, payload)).items() if k != "timestamp"})
            for _ in range(50)
            for topic, payload in store.step()
        ]

    assert run(7) == run(7)
    assert run(7) != run(8)


def test_shelf_sensors_report_on_schedule():
    store = make_store(shelf_every=5)
    for tick in range(1, 21):
        readings = [parse(t, p) for t, p in store.step()]
        shelf = [r for r in readings if isinstance(r, ShelfReading)]
        if tick % 5 == 0:
            assert sorted(r.product_id for r in shelf) == sorted(START)
        else:
            assert shelf == []


def test_low_product_gets_restocked():
    store = Store({1: 6}, rng=random.Random(0), restock_below=5, restock_amount=24, shrink_chance=0)
    restocks = []
    for _ in range(10):
        restocks += [
            e for e in (parse(t, p) for t, p in store.step())
            if isinstance(e, ScanEvent) and e.action == "restock"
        ]
    assert restocks, "product 1 should have dropped below 5 and been restocked"
    assert all(e.quantity == 24 for e in restocks)


def run_through_listener(store, ticks):
    """Feed the simulator's messages to the listener, the same way MQTT
    would, and check the books after each shelf report."""
    api = InMemoryStockAPI({pid: (f"Product {pid}", qty) for pid, qty in store.stock.items()})
    updater = StockUpdater(api)

    for _ in range(ticks):
        outcomes = [updater.handle(t, p) for t, p in store.step()]
        assert all(o.status != "skipped" for o in outcomes), outcomes

        if store.tick % store.shelf_every == 0:
            # Right after the shelves report, the database must match them
            books = {p["id"]: p["quantity"] for p in api.list_products()}
            assert books == store.stock
    return api


def test_scans_alone_keep_stock_correct():
    # Nothing goes missing, so shelf checks should never need to fix anything
    api = run_through_listener(make_store(shrink_chance=0), ticks=500)
    assert not [h for h in api.history if h[2] == "adjustment"]


def test_shelf_sensors_catch_unscanned_losses():
    api = run_through_listener(make_store(shrink_chance=0.3), ticks=500)
    adjustments = [change for _, change, kind in api.history if kind == "adjustment"]
    assert adjustments, "with shrinkage on, some corrections should have happened"
    assert all(change < 0 for change in adjustments), "losses only ever lower stock"
