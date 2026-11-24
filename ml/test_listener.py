"""
Tests for the listener's logic: each kind of message leads to the right
stock change. Uses the in-memory backend, so no broker or database needed.
"""
import json

import pytest

from listener import StockUpdater
from messages import make_scan, make_shelf_reading
from stock_api import InMemoryStockAPI, StockAPIError


@pytest.fixture
def api():
    return InMemoryStockAPI({1: ("Sparkling Water 12oz", 10), 2: ("Lip Balm", 0)})


@pytest.fixture
def updater(api):
    return StockUpdater(api)


def stock(api, product_id):
    return api.get_product(product_id)["quantity"]


def test_sale_lowers_stock(api, updater):
    outcome = updater.handle(*make_scan("checkout-1", 1, "sale", 3))
    assert outcome.status == "applied"
    assert stock(api, 1) == 7
    assert api.history == [(1, -3, "sale")]


def test_restock_raises_stock(api, updater):
    outcome = updater.handle(*make_scan("receiving-1", 2, "restock", 24))
    assert outcome.status == "applied"
    assert stock(api, 2) == 24
    assert api.history == [(2, 24, "receive")]


def test_sale_with_not_enough_stock_is_skipped(api, updater):
    outcome = updater.handle(*make_scan("checkout-1", 1, "sale", 11))
    assert outcome.status == "skipped"
    assert "Not enough stock" in outcome.detail
    assert stock(api, 1) == 10
    assert api.history == []


def test_unknown_product_is_skipped(api, updater):
    outcome = updater.handle(*make_scan("checkout-1", 999, "sale", 1))
    assert outcome.status == "skipped"
    assert "Product not found" in outcome.detail


def test_bad_message_is_skipped_without_touching_stock(api, updater):
    outcome = updater.handle("nstock/scanner/checkout-1", b"garbage")
    assert outcome.status == "skipped"
    assert api.history == []


def test_shelf_matching_database_changes_nothing(api, updater):
    outcome = updater.handle(*make_shelf_reading("shelf-1", 1, 10))
    assert outcome.status == "unchanged"
    assert api.history == []


def test_shelf_lower_than_database_records_adjustment(api, updater):
    # Database says 10, shelf has 8: two went missing without a scan
    outcome = updater.handle(*make_shelf_reading("shelf-1", 1, 8))
    assert outcome.status == "applied"
    assert stock(api, 1) == 8
    assert api.history == [(1, -2, "adjustment")]


def test_shelf_higher_than_database_records_adjustment(api, updater):
    outcome = updater.handle(*make_shelf_reading("shelf-2", 2, 5))
    assert outcome.status == "applied"
    assert stock(api, 2) == 5
    assert api.history == [(2, 5, "adjustment")]


def test_shelf_correction_keeps_product_name(api, updater):
    updater.handle(*make_shelf_reading("shelf-1", 1, 8))
    assert api.get_product(1)["name"] == "Sparkling Water 12oz"


def test_backend_down_is_skipped_not_crashed():
    class DownAPI:
        def record_transaction(self, *args):
            raise StockAPIError(None, "backend unreachable")

    outcome = StockUpdater(DownAPI()).handle(*make_scan("checkout-1", 1, "sale", 1))
    assert outcome.status == "skipped"
    assert "unreachable" in outcome.detail


def test_messages_are_applied_in_order(api, updater):
    updater.handle(*make_scan("checkout-1", 1, "sale", 4))        # 10 -> 6
    updater.handle(*make_scan("receiving-1", 1, "restock", 24))   # 6 -> 30
    updater.handle(*make_scan("checkout-1", 1, "sale", 1))        # 30 -> 29
    updater.handle("nstock/shelf/shelf-1", json.dumps({"product_id": 1, "count": 28}))
    assert stock(api, 1) == 28
    assert [change for _, change, _ in api.history] == [-4, 24, -1, -1]
