from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
products = [
    {"id": 1, "name": "Laptop", "quantity": 10},
    {"id": 2, "name": "Mouse", "quantity": 25},
    {"id": 3, "name": "Keyboard", "quantity": 15}
]

@app.get("/")
def home():
    return {"message": "Welcome to NStock API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products")
def get_products():
    return products
@app.get("/products/{product_id}")
def get_product(product_id: int):
    products = get_products()

    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/products")
def add_product(product: Product):
    new_product = {
        "id": len(products) + 1,
        "name": product.name,
        "quantity": product.quantity
    }

    products.append(new_product)

    return {
        "message": "Product added successfully",
        "product": new_product
    }


@app.put("/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    for product in products:
        if product["id"] == product_id:
            product["name"] = updated_product.name
            product["quantity"] = updated_product.quantity
            return {
                "message": "Product updated successfully",
                "product": product
            }

    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": "Product deleted successfully"}

    raise HTTPException(status_code=404, detail="Product not found")

# Supplier Model
class Supplier(BaseModel):
    name: str
    email: str
    phone: str

# Temporary supplier storage
suppliers = [
    {"id": 1, "name": "ABC Supplies",
     "email": "abc@example.com", "phone": "1234567890"},
    {"id": 2, "name": "Tech Distributors",
     "email": "tech@example.com", "phone": "9876543210"}
]


# Get all suppliers
@app.get("/suppliers")
def get_suppliers():
    return suppliers


# Get a supplier by ID
@app.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int):
    for supplier in suppliers:
        if supplier["id"] == supplier_id:
            return supplier

    raise HTTPException(
        status_code=404,
        detail="Supplier not found"
    )



# Add a new supplier
@app.post("/suppliers")
def add_supplier(supplier: Supplier):
    new_supplier = {
        "id": max((s["id"] for s in suppliers), default=0) + 1,
        "name": supplier.name,
        "email": supplier.email,
        "phone": supplier.phone
    }

    suppliers.append(new_supplier)

    return {
        "message": "Supplier added successfully",
        "supplier": new_supplier
    }


# Update a supplier
@app.put("/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, updated_supplier: Supplier):
    for supplier in suppliers:
        if supplier["id"] == supplier_id:
            supplier["name"] = updated_supplier.name
            supplier["email"] = updated_supplier.email
            supplier["phone"] = updated_supplier.phone

            return {
                "message": "Supplier updated successfully",
                "supplier": supplier
            }

    raise HTTPException(
        status_code=404,
        detail="Supplier not found"
    )



# Delete a supplier
@app.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int):
    for supplier in suppliers:
        if supplier["id"] == supplier_id:
            suppliers.remove(supplier)

            return {
                "message": "Supplier deleted successfully"
            }

    raise HTTPException(
        status_code=404,
        detail="Supplier not found"
    )


# Purchase Order Model
class PurchaseOrder(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int

# Temporary purchase order storage
purchase_orders = [
    {
        "id": 1,
        "product_id": 1,
        "supplier_id": 1,
        "quantity": 5
    },
    {
        "id": 2,
        "product_id": 2,
        "supplier_id": 2,
        "quantity": 10
    }
]


# Get all purchase orders
@app.get("/purchase-orders")
def get_purchase_orders():
    return purchase_orders


# Get a purchase order by ID
@app.get("/purchase-orders/{order_id}")
def get_purchase_order(order_id: int):
    for order in purchase_orders:
        if order["id"] == order_id:
            return order

    raise HTTPException(
        status_code=404,
        detail="Purchase order not found"
    )


# Add a new purchase order
@app.post("/purchase-orders")
def add_purchase_order(order: PurchaseOrder):
    new_order = {
        "id": max((o["id"] for o in purchase_orders), default=0) + 1,
        "product_id": order.product_id,
        "supplier_id": order.supplier_id,
        "quantity": order.quantity
    }

    purchase_orders.append(new_order)

    return {
        "message": "Purchase order added successfully",
        "purchase_order": new_order
    }


# Update a purchase order
@app.put("/purchase-orders/{order_id}")
def update_purchase_order(order_id: int, updated_order: PurchaseOrder):
    for order in purchase_orders:
        if order["id"] == order_id:
            order["product_id"] = updated_order.product_id
            order["supplier_id"] = updated_order.supplier_id
            order["quantity"] = updated_order.quantity

            return {
                "message": "Purchase order updated successfully",
                "purchase_order": order
            }

    raise HTTPException(
        status_code=404,
        detail="Purchase order not found"
    )


# Delete a purchase order
@app.delete("/purchase-orders/{order_id}")
def delete_purchase_order(order_id: int):
    for order in purchase_orders:
        if order["id"] == order_id:
            purchase_orders.remove(order)

            return {
                "message": "Purchase order deleted successfully"
            }

    raise HTTPException(
        status_code=404,
        detail="Purchase order not found"
    )


# Stock Transaction Model
class StockTransaction(BaseModel):
    product_id: int
    quantity: int
    transaction_type: str

# Temporary stock transaction storage
stock_transactions = []


# Add a stock transaction
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

    for product in products:
        if product["id"] == transaction.product_id:

            if transaction.transaction_type == "OUT":
                if product["quantity"] < transaction.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough stock"
                    )
                product["quantity"] -= transaction.quantity

            else:
                product["quantity"] += transaction.quantity

            new_transaction = {
                "id": len(stock_transactions) + 1,
                "product_id": transaction.product_id,
                "quantity": transaction.quantity,
                "transaction_type": transaction.transaction_type
            }

            stock_transactions.append(new_transaction)

            return {
                "message": "Stock updated successfully",
                "product": product,
                "transaction": new_transaction
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )
