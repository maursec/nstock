# NStock Backend API

This backend uses Python and FastAPI to manage product inventory.

## Installation

Install dependencies:

```bash
py -m pip install -r requirements.txt
```

## Run the Server

```bash
py -m uvicorn main:app --reload
```

## API Documentation

After starting the server, open:

http://127.0.0.1:8000/docs

## Available Endpoints

- GET / — Home
- GET /health — Health check
- GET /products — List products
- GET /products/{product_id} — Get a product
- POST /products — Add a product
- PUT /products/{product_id} — Update a product
- DELETE /products/{product_id} — Delete a product

## Notes

Product data is currently stored in memory and resets when the server restarts.