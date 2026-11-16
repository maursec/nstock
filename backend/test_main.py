
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_get_products():
    response = client.get("/products")
    assert response.status_code == 200

def test_get_suppliers():
    response = client.get("/suppliers")
    assert response.status_code == 200


def test_get_purchase_orders():
    response = client.get("/purchase-orders")
    assert response.status_code == 200

def test_get_purchase_order_by_id():
    response = client.get("/purchase-orders/1")
    assert response.status_code == 200


def test_add_stock_in():
    new_product = {
        "name": "Stock In Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    response = client.post(
        "/stock-transactions",
        json={
            "product_id": product_id,
            "quantity": 5,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 200
    assert response.json()["current_stock"] == 15


def test_add_stock_out():
    new_product = {
        "name": "Stock Out Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    response = client.post(
        "/stock-transactions",
        json={
            "product_id": product_id,
            "quantity": 5,
            "transaction_type": "OUT"
        }
    )

    assert response.status_code == 200
    assert response.json()["current_stock"] == 5


def test_invalid_quantity():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": -5,
            "transaction_type": "IN"
        }
    )
    assert response.status_code == 400


def test_invalid_transaction_type():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": 5,
            "transaction_type": "INVALID"
        }
    )
    assert response.status_code == 400


def test_product_not_found():
    response = client.get("/products/9999")
    assert response.status_code == 404


def test_supplier_not_found():
    response = client.get("/suppliers/9999")
    assert response.status_code == 404


def test_purchase_order_not_found():
    response = client.get("/purchase-orders/9999")
    assert response.status_code == 404


def test_insufficient_stock():
    new_product = {
        "name": "Insufficient Stock Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    response = client.post(
        "/stock-transactions",
        json={
            "product_id": product_id,
            "quantity": 999999,
            "transaction_type": "OUT"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough stock"


def test_add_product():
    new_product = {
        "name": "Test Product",
        "price": 25.99,
        "quantity": 50
    }

    response = client.post(
        "/products",
        json=new_product
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Product added successfully"


def test_delete_product():
    response = client.get("/products")
    product_id = response.json()[0]["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully"


def test_update_product():
    new_product = {
        "name": "Product for Update Test",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200

    product_id = response.json()["product"]["id"]

    updated_product = {
        "name": "Updated Product",
        "quantity": 50
    }

    response = client.put(
        f"/products/{product_id}",
        json=updated_product
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Product updated successfully"


def test_add_supplier():
    new_supplier = {
        "name": "Test Supplier",
        "email": "test@example.com",
        "phone": "1234567890"
    }

    response = client.post(
        "/suppliers",
        json=new_supplier
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Supplier added successfully"


def test_delete_supplier():
    new_supplier = {
        "name": "Supplier for Delete Test",
        "email": "delete@example.com",
        "phone": "1234567890"
    }

    response = client.post("/suppliers", json=new_supplier)
    assert response.status_code == 200

    supplier_id = response.json()["supplier"]["id"]

    response = client.delete(f"/suppliers/{supplier_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Supplier deleted successfully"


def test_update_supplier():
    response = client.get("/suppliers")
    supplier_id = response.json()[0]["id"]

    updated_supplier = {
        "name": "Updated Supplier",
        "email": "updated@example.com",
        "phone": "9876543210"
    }

    response = client.put(
        f"/suppliers/{supplier_id}",
        json=updated_supplier
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Supplier updated successfully"


def test_add_purchase_order():
    new_product = {
        "name": "Purchase Order Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    new_supplier = {
        "name": "Purchase Order Test Supplier",
        "email": "po@example.com",
        "phone": "1234567890"
    }

    response = client.post("/suppliers", json=new_supplier)
    assert response.status_code == 200
    supplier_id = response.json()["supplier"]["id"]

    new_order = {
        "product_id": product_id,
        "supplier_id": supplier_id,
        "quantity": 5
    }

    response = client.post(
        "/purchase-orders",
        json=new_order
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Purchase order added successfully"


def test_delete_purchase_order():
    new_product = {
        "name": "PO Delete Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    new_supplier = {
        "name": "PO Delete Test Supplier",
        "email": "podelete@example.com",
        "phone": "1234567890"
    }

    response = client.post("/suppliers", json=new_supplier)
    assert response.status_code == 200
    supplier_id = response.json()["supplier"]["id"]

    new_order = {
        "product_id": product_id,
        "supplier_id": supplier_id,
        "quantity": 5
    }

    response = client.post("/purchase-orders", json=new_order)
    assert response.status_code == 200

    order_id = response.json()["purchase_order"]["id"]

    response = client.delete(
        f"/purchase-orders/{order_id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Purchase order deleted successfully"


def test_update_purchase_order():
    new_product = {
        "name": "PO Update Test Product",
        "quantity": 10
    }

    response = client.post("/products", json=new_product)
    assert response.status_code == 200
    product_id = response.json()["product"]["id"]

    new_supplier = {
        "name": "PO Update Test Supplier",
        "email": "poupdate@example.com",
        "phone": "1234567890"
    }

    response = client.post("/suppliers", json=new_supplier)
    assert response.status_code == 200
    supplier_id = response.json()["supplier"]["id"]

    new_order = {
        "product_id": product_id,
        "supplier_id": supplier_id,
        "quantity": 5
    }

    response = client.post("/purchase-orders", json=new_order)
    assert response.status_code == 200
    order_id = response.json()["purchase_order"]["id"]

    updated_order = {
        "product_id": product_id,
        "supplier_id": supplier_id,
        "quantity": 20
    }

    response = client.put(
        f"/purchase-orders/{order_id}",
        json=updated_order
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Purchase order updated successfully"


def test_stock_product_not_found():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 999999,
            "quantity": 5,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_zero_quantity():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": 0,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Quantity must be greater than zero"


def test_negative_quantity():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": -10,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Quantity must be greater than zero"


def test_lowercase_transaction_type():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": 5,
            "transaction_type": "in"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Transaction type must be IN or OUT"


def test_missing_quantity():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 422


def test_missing_product_id():
    response = client.post(
        "/stock-transactions",
        json={
            "quantity": 5,
            "transaction_type": "IN"
        }
    )

    assert response.status_code == 422


def test_missing_transaction_type():
    response = client.post(
        "/stock-transactions",
        json={
            "product_id": 1,
            "quantity": 5
        }
    )

    assert response.status_code == 422


def test_missing_product_name():
    response = client.post(
        "/products",
        json={
            "quantity": 10
        }
    )

    assert response.status_code == 422

def test_cors():
    response = client.get(
        "/products",
        headers={"Origin": "http://localhost:4200"}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"