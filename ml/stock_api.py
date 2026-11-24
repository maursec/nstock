"""
How the IoT code talks to the NStock backend.

StockAPI          sends real HTTP requests to the FastAPI backend.
InMemoryStockAPI  a stand-in backend that keeps stock in a Python dict and
                  follows the same rules (no negative stock, unknown product
                  is an error). Used by the tests and the offline demo, so
                  they work without MySQL or the backend running.

Both classes have the same methods, so the listener works with either.
"""
import requests


class StockAPIError(Exception):
    """The backend refused a request or couldn't be reached."""

    def __init__(self, status, detail):
        super().__init__(f"{status}: {detail}")
        self.status = status    # HTTP status code, or None if unreachable
        self.detail = detail


class StockAPI:
    def __init__(self, base_url, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def list_products(self):
        """GET /products -> [{"id", "name", "quantity"}, ...]"""
        return self._request("GET", "/products")

    def get_product(self, product_id):
        """GET /products/{id} -> {"id", "name", "quantity"}"""
        return self._request("GET", f"/products/{product_id}")

    def record_transaction(self, product_id, quantity, transaction_type):
        """POST /stock-transactions with type "IN" or "OUT".
        Returns the new stock level."""
        body = {
            "product_id": product_id,
            "quantity": quantity,
            "transaction_type": transaction_type,
        }
        result = self._request("POST", "/stock-transactions", json=body)
        return int(result["current_stock"])

    def set_quantity(self, product_id, name, quantity):
        """PUT /products/{id}. The backend records the difference between
        the old and new quantity as an 'adjustment' stock movement."""
        self._request(
            "PUT", f"/products/{product_id}", json={"name": name, "quantity": quantity}
        )

    def _request(self, method, path, **kwargs):
        try:
            response = self.session.request(
                method, self.base_url + path, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as error:
            raise StockAPIError(None, f"backend unreachable at {self.base_url} ({error})") from None

        if response.status_code >= 400:
            try:
                body = response.json()
                detail = body.get("detail", body) if isinstance(body, dict) else body
            except ValueError:
                detail = response.text
            raise StockAPIError(response.status_code, detail)

        return response.json()


class InMemoryStockAPI:
    def __init__(self, products):
        """products: {product_id: (name, quantity)}"""
        self.products = {
            pid: {"id": pid, "name": name, "quantity": qty}
            for pid, (name, qty) in products.items()
        }
        # Every change as (product_id, change, kind), like the
        # stock_movements table in the real database
        self.history = []

    def list_products(self):
        return [dict(p) for p in self.products.values()]

    def get_product(self, product_id):
        return dict(self._find(product_id))

    def record_transaction(self, product_id, quantity, transaction_type):
        product = self._find(product_id)
        if quantity <= 0:
            raise StockAPIError(400, "Quantity must be greater than zero")
        if transaction_type == "OUT":
            if product["quantity"] < quantity:
                raise StockAPIError(400, "Not enough stock")
            change, kind = -quantity, "sale"
        elif transaction_type == "IN":
            change, kind = quantity, "receive"
        else:
            raise StockAPIError(400, "Transaction type must be IN or OUT")

        product["quantity"] += change
        self.history.append((product_id, change, kind))
        return product["quantity"]

    def set_quantity(self, product_id, name, quantity):
        product = self._find(product_id)
        if quantity < 0:
            raise StockAPIError(400, "Quantity cannot be negative")
        change = quantity - product["quantity"]
        product["name"] = name
        product["quantity"] = quantity
        if change:
            self.history.append((product_id, change, "adjustment"))

    def _find(self, product_id):
        if product_id not in self.products:
            raise StockAPIError(404, "Product not found")
        return self.products[product_id]
