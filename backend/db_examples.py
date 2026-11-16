"""
Examples for switching main.py from in-memory lists to MySQL.

Each function below is a drop-in replacement for the matching endpoint
in main.py. They keep the same URLs, JSON field names and messages, so
the frontend and the existing tests don't have to change (except that
products now need a "sku").

Pattern for every endpoint:
  1. add  db: Session = Depends(get_db)  to the function's parameters
  2. replace the loop over the list with a query
  3. after any change, call db.commit()
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import ProductRow, PurchaseOrderItemRow, PurchaseOrderRow, StockMovementRow, SupplierRow

router = APIRouter()


# ---------- Pydantic models (the JSON shapes) ----------

class Product(BaseModel):
    sku: str
    name: str
    price: float = Field(ge=0)
    quantity: int = Field(default=0, ge=0)


class StockTransaction(BaseModel):
    product_id: int
    quantity: int
    transaction_type: str


class PurchaseOrder(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int = Field(gt=0)
    status: str = "draft"


def product_to_dict(p: ProductRow) -> dict:
    """Turn a database row into the JSON the API already returns."""
    return {
        "id": p.product_id,
        "sku": p.sku,
        "name": p.name,
        "price": float(p.unit_price),
        "quantity": p.on_hand,
        "reorder_point": p.reorder_point,
    }


# ---------- Products ----------

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    rows = db.scalars(select(ProductRow).where(ProductRow.is_active == True)).all()
    return [product_to_dict(p) for p in rows]


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(ProductRow, product_id)
    if p is None or not p.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(p)


@router.post("/products")
def add_product(product: Product, db: Session = Depends(get_db)):
    row = ProductRow(sku=product.sku, name=product.name, unit_price=product.price)
    db.add(row)
    try:
        db.flush()  # gets row.product_id without committing yet
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="SKU already exists")

    # Starting quantity is recorded as a ledger entry, not stored on the product
    if product.quantity > 0:
        db.add(StockMovementRow(product_id=row.product_id, movement_type="adjustment",
                                quantity=product.quantity, note="Starting quantity"))
    db.commit()
    db.refresh(row)
    return {"message": "Product added successfully", "product": product_to_dict(row)}


@router.put("/products/{product_id}")
def update_product(product_id: int, updated: Product, db: Session = Depends(get_db)):
    p = db.get(ProductRow, product_id)
    if p is None or not p.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    p.sku, p.name, p.unit_price = updated.sku, updated.name, updated.price

    # If the quantity changed, record the difference as an adjustment
    difference = updated.quantity - p.on_hand
    if difference != 0:
        db.add(StockMovementRow(product_id=product_id, movement_type="adjustment",
                                quantity=difference, note="Manual count update"))
    db.commit()
    db.refresh(p)
    return {"message": "Product updated successfully", "product": product_to_dict(p)}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(ProductRow, product_id)
    if p is None or not p.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    # Soft delete: a real DELETE would fail (or erase history) because
    # stock_movements and purchase orders point to this product.
    p.is_active = False
    db.commit()
    return {"message": "Product deleted successfully"}


# ---------- Stock transactions ----------

@router.post("/stock-transactions")
def add_stock_transaction(transaction: StockTransaction, db: Session = Depends(get_db)):
    if transaction.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    if transaction.transaction_type not in ["IN", "OUT"]:
        raise HTTPException(status_code=400, detail="Transaction type must be IN or OUT")

    p = db.get(ProductRow, transaction.product_id)
    if p is None or not p.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    if transaction.transaction_type == "OUT":
        if p.on_hand < transaction.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")
        movement = StockMovementRow(product_id=p.product_id, movement_type="sale",
                                    quantity=-transaction.quantity)
    else:
        movement = StockMovementRow(product_id=p.product_id, movement_type="receive",
                                    quantity=transaction.quantity)

    db.add(movement)
    db.commit()
    db.refresh(p)
    return {
        "message": "Stock updated successfully",
        "product": product_to_dict(p),
        "transaction": {
            "id": movement.movement_id,
            "product_id": p.product_id,
            "quantity": transaction.quantity,
            "transaction_type": transaction.transaction_type,
        },
    }


# ---------- Purchase orders ----------

PO_STATUSES = ["draft", "ordered", "received", "cancelled"]


@router.post("/purchase-orders")
def add_purchase_order(order: PurchaseOrder, db: Session = Depends(get_db)):
    if order.status not in PO_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {PO_STATUSES}")

    product = db.get(ProductRow, order.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    supplier = db.get(SupplierRow, order.supplier_id)
    if supplier is None or not supplier.is_active:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # One PO header + one line (the API sends one product per order for now)
    po = PurchaseOrderRow(supplier_id=order.supplier_id, status=order.status,
                          order_date=date.today())
    po.items.append(PurchaseOrderItemRow(product_id=order.product_id,
                                         quantity=order.quantity,
                                         unit_cost=product.unit_cost))
    db.add(po)
    db.commit()
    return {
        "message": "Purchase order added successfully",
        "purchase_order": {
            "id": po.po_id,
            "product_id": order.product_id,
            "supplier_id": order.supplier_id,
            "quantity": order.quantity,
            "status": po.status,
        },
    }
