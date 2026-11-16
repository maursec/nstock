"""
SQLAlchemy models: one class per table in database/nstock_schema.sql.

These describe the existing tables so Python can read and write them.
Don't call Base.metadata.create_all(); build the database from the .sql
file so everyone's tables match exactly.

Naming: these classes end in "Row" (ProductRow, SupplierRow...) so they
don't clash with the Pydantic models in main.py (Product, Supplier...),
which describe the JSON the API sends and receives.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String,
    func, select,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from database import Base


class UserRow(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Enum("owner", "staff"), default="staff")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CategoryRow(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class SupplierRow(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    contact_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockMovementRow(Base):
    __tablename__ = "stock_movements"

    movement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    movement_type: Mapped[str] = mapped_column(
        Enum("receive", "sale", "adjustment", "return")
    )
    quantity: Mapped[int] = mapped_column(Integer)  # + in, - out
    po_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.po_id"))
    note: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProductRow(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.category_id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.supplier_id"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # On-hand quantity = sum of this product's stock movements.
    # Read it like a normal attribute: product.on_hand
    on_hand: Mapped[int] = column_property(
        select(func.coalesce(func.sum(StockMovementRow.quantity), 0))
        .where(StockMovementRow.product_id == product_id)
        .correlate_except(StockMovementRow)
        .scalar_subquery()
    )


class PurchaseOrderRow(Base):
    __tablename__ = "purchase_orders"

    po_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.supplier_id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    status: Mapped[str] = mapped_column(
        Enum("draft", "ordered", "received", "cancelled"), default="draft"
    )
    order_date: Mapped[date | None] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date)

    items: Mapped[list["PurchaseOrderItemRow"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItemRow(Base):
    __tablename__ = "purchase_order_items"

    po_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.po_id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    purchase_order: Mapped[PurchaseOrderRow] = relationship(back_populates="items")
