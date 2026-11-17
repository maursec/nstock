from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.database import get_db_connection
from uuid import uuid4

app = FastAPI(title="NStock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Product(BaseModel):
    name: str
    quantity: int

@app.get("/")
def home():
    return {"message": "Welcome to NStock API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products")
def get_products():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.product_id AS id,
                p.name,
                COALESCE(SUM(sm.quantity), 0) AS quantity
            FROM products p
            LEFT JOIN stock_movements sm
                ON p.product_id = sm.product_id
                WHERE p.is_active = 1
            GROUP BY p.product_id, p.name
            ORDER BY p.product_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()
@app.get("/products/{product_id}")
def get_product(product_id: int):
    products = get_products()

    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/products")
def add_product(product: Product):
    if product.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        sku = str(uuid4())

        cursor.execute("""
            INSERT INTO products (sku, name)
            VALUES (%s, %s)
        """, (sku, product.name))

        product_id = cursor.lastrowid

        if product.quantity > 0:
            cursor.execute("""
                INSERT INTO stock_movements
                    (product_id, user_id, movement_type, quantity)
                VALUES (%s, %s, %s, %s)
            """, (product_id, 1, "receive", product.quantity))

        connection.commit()

        return {
            "message": "Product added successfully",
            "product": {
                "id": product_id,
                "name": product.name,
                "quantity": product.quantity
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.put("/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    if updated_product.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
           AND is_active = 1
            FOR UPDATE
        """, (product_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0) AS quantity
            FROM stock_movements
            WHERE product_id = %s
        """, (product_id,))

        current_quantity = cursor.fetchone()["quantity"]
        difference = updated_product.quantity - current_quantity

        cursor.execute("""
            UPDATE products
            SET name = %s
            WHERE product_id = %s
        """, (updated_product.name, product_id))

        if difference != 0:
            cursor.execute("""
                INSERT INTO stock_movements
                    (product_id, user_id, movement_type, quantity)
                VALUES (%s, %s, %s, %s)
            """, (product_id, 1, "adjustment", difference))

        connection.commit()

        return {
            "message": "Product updated successfully",
            "product": {
                "id": product_id,
                "name": updated_product.name,
                "quantity": updated_product.quantity
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE products
            SET is_active = 0
            WHERE product_id = %s
            AND is_active = 1
        """, (product_id,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        connection.commit()

        return {"message": "Product deleted successfully"}

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

# Supplier Model
class Supplier(BaseModel):
    name: str
    email: str
    phone: str


@app.get("/suppliers")
def get_suppliers():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                supplier_id AS id,
                name,
                email,
                phone
            FROM suppliers
            ORDER BY supplier_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


@app.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int):
    suppliers = get_suppliers()

    for supplier in suppliers:
        if supplier["id"] == supplier_id:
            return supplier

    raise HTTPException(
        status_code=404,
        detail="Supplier not found"
    )



@app.post("/suppliers")
def add_supplier(supplier: Supplier):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO suppliers (name, email, phone)
            VALUES (%s, %s, %s)
        """, (supplier.name, supplier.email, supplier.phone))

        supplier_id = cursor.lastrowid

        connection.commit()

        return {
            "message": "Supplier added successfully",
            "supplier": {
                "id": supplier_id,
                "name": supplier.name,
                "email": supplier.email,
                "phone": supplier.phone
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    suppliers.append(new_supplier)

    return {
        "message": "Supplier added successfully",
        "supplier": new_supplier
    }

@app.put("/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, updated_supplier: Supplier):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_id = %s
        """, (supplier_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found"
            )

        cursor.execute("""
            UPDATE suppliers
            SET name = %s, email = %s, phone = %s
            WHERE supplier_id = %s
        """, (
            updated_supplier.name,
            updated_supplier.email,
            updated_supplier.phone,
            supplier_id
        ))

        connection.commit()

        return {
            "message": "Supplier updated successfully",
            "supplier": {
                "id": supplier_id,
                "name": updated_supplier.name,
                "email": updated_supplier.email,
                "phone": updated_supplier.phone
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



@app.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM suppliers
            WHERE supplier_id = %s
        """, (supplier_id,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found"
            )

        connection.commit()

        return {
            "message": "Supplier deleted successfully"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# Purchase Order Model
class PurchaseOrder(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int


@app.get("/purchase-orders")
def get_purchase_orders():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                po.po_id AS id,
                poi.product_id,
                po.supplier_id,
                poi.quantity,
                po.status
            FROM purchase_orders po
            JOIN purchase_order_items poi
                ON po.po_id = poi.po_id
            ORDER BY po.po_id, poi.po_item_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


@app.get("/purchase-orders/{order_id}")
def get_purchase_order(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                po.po_id AS id,
                poi.product_id,
                po.supplier_id,
                poi.quantity,
                po.status
            FROM purchase_orders po
            JOIN purchase_order_items poi
                ON po.po_id = poi.po_id
            WHERE po.po_id = %s
            ORDER BY poi.po_item_id
        """, (order_id,))

        orders = cursor.fetchall()

        if not orders:
            raise HTTPException(
                status_code=404,
                detail="Purchase order not found"
            )

        return orders

    finally:
        cursor.close()
        connection.close()


@app.post("/purchase-orders")
def add_purchase_order(order: PurchaseOrder):
    if order.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_id = %s
        """, (order.supplier_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found"
            )

        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
            AND is_active = 1
        """, (order.product_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cursor.execute("""
            INSERT INTO purchase_orders
                (supplier_id, created_by, status, order_date)
            VALUES (%s, %s, %s, CURDATE())
        """, (order.supplier_id, 1, "draft"))

        order_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO purchase_order_items
                (po_id, product_id, quantity, unit_cost)
            VALUES (%s, %s, %s, %s)
        """, (
            order_id,
            order.product_id,
            order.quantity,
            0.00
        ))

        connection.commit()

        return {
            "message": "Purchase order added successfully",
            "purchase_order": {
                "id": order_id,
                "product_id": order.product_id,
                "supplier_id": order.supplier_id,
                "quantity": order.quantity,
                "status": "draft"
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.put("/purchase-orders/{order_id}")
def update_purchase_order(order_id: int, updated_order: PurchaseOrder):
    if updated_order.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT status
            FROM purchase_orders
            WHERE po_id = %s
            FOR UPDATE
        """, (order_id,))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Purchase order not found"
            )

        if order["status"] != "draft":
            raise HTTPException(
                status_code=400,
                detail="Only draft orders can be updated"
            )

        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_id = %s
        """, (updated_order.supplier_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found"
            )

        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
            AND is_active = 1
        """, (updated_order.product_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cursor.execute("""
            SELECT po_item_id
            FROM purchase_order_items
            WHERE po_id = %s
            FOR UPDATE
        """, (order_id,))

        items = cursor.fetchall()

        if len(items) != 1:
            raise HTTPException(
                status_code=400,
                detail="Only single-item orders can be updated"
            )

        cursor.execute("""
            UPDATE purchase_orders
            SET supplier_id = %s
            WHERE po_id = %s
        """, (
            updated_order.supplier_id,
            order_id
        ))

        cursor.execute("""
            UPDATE purchase_order_items
            SET product_id = %s,
                quantity = %s
            WHERE po_item_id = %s
        """, (
            updated_order.product_id,
            updated_order.quantity,
            items[0]["po_item_id"]
        ))

        connection.commit()

        return {
            "message": "Purchase order updated successfully",
            "purchase_order": {
                "id": order_id,
                "product_id": updated_order.product_id,
                "supplier_id": updated_order.supplier_id,
                "quantity": updated_order.quantity,
                "status": "draft"
            }
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.delete("/purchase-orders/{order_id}")
def delete_purchase_order(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT status
            FROM purchase_orders
            WHERE po_id = %s
            FOR UPDATE
        """, (order_id,))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Purchase order not found"
            )

        if order["status"] != "draft":
            raise HTTPException(
                status_code=400,
                detail="Only draft orders can be deleted"
            )

        cursor.execute("""
            DELETE FROM purchase_order_items
            WHERE po_id = %s
        """, (order_id,))

        cursor.execute("""
            DELETE FROM purchase_orders
            WHERE po_id = %s
        """, (order_id,))

        connection.commit()

        return {
            "message": "Purchase order deleted successfully"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# Stock Transaction Model
class StockTransaction(BaseModel):
    product_id: int
    quantity: int
    transaction_type: str


@app.post("/stock-transactions")
def add_stock_transaction(transaction: StockTransaction):
    if transaction.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    if transaction.transaction_type not in ["IN", "OUT"]:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be IN or OUT"
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
            AND is_active = 1
            FOR UPDATE
        """, (transaction.product_id,))

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0) AS stock
            FROM stock_movements
            WHERE product_id = %s
        """, (transaction.product_id,))

        current_stock = cursor.fetchone()["stock"]

        if transaction.transaction_type == "OUT":
            if current_stock < transaction.quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough stock"
                )

            movement_type = "sale"
            quantity = -transaction.quantity

        else:
            movement_type = "receive"
            quantity = transaction.quantity

        cursor.execute("""
            INSERT INTO stock_movements
                (product_id, user_id, movement_type, quantity)
            VALUES (%s, %s, %s, %s)
        """, (
            transaction.product_id,
            1,
            movement_type,
            quantity
        ))

        transaction_id = cursor.lastrowid

        connection.commit()

        return {
            "message": "Stock transaction added successfully",
            "transaction": {
                "id": transaction_id,
                "product_id": transaction.product_id,
                "quantity": transaction.quantity,
                "transaction_type": transaction.transaction_type
            },
            "current_stock": current_stock + quantity
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

@app.get("/stock-transactions")
def get_stock_transactions():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                movement_id AS id,
                product_id,
                ABS(quantity) AS quantity,
                CASE
                    WHEN quantity < 0 THEN 'OUT'
                    ELSE 'IN'
                END AS transaction_type
            FROM stock_movements
            ORDER BY movement_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()
