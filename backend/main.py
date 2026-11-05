from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="NStock API")
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

