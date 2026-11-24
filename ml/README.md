# NStock IoT: sensor simulator and MQTT listener

We don't have real store hardware, so `simulator.py` pretends to be barcode scanners and shelf sensors. It sends their messages through an MQTT broker (Mosquitto). `listener.py` receives those messages and updates stock through the backend API.

```
simulator.py  --MQTT-->  Mosquitto  --MQTT-->  listener.py  --HTTP-->  FastAPI backend  -->  MySQL
(fake devices)           (message hub)         (stock updates)         (/stock-transactions)
```

## Topics and messages

| Device | Topic | Payload |
|---|---|---|
| Barcode scanner | `nstock/scanner/<scanner_id>` | `{"product_id": 3, "action": "sale", "quantity": 1, "timestamp": "..."}` |
| Shelf sensor | `nstock/shelf/<shelf_id>` | `{"product_id": 3, "count": 37, "timestamp": "..."}` |

`action` is `"sale"` or `"restock"`. `count` is the number of units physically on the shelf.

## What the listener does

| Message | API call | Result in `stock_movements` |
|---|---|---|
| Scanner `sale` | `POST /stock-transactions` with `OUT` | `sale` row, negative quantity |
| Scanner `restock` | `POST /stock-transactions` with `IN` | `receive` row, positive quantity |
| Shelf reading that matches the database | none | nothing |
| Shelf reading that doesn't match | `PUT /products/{id}` with the shelf count | `adjustment` row for the difference |

Scanners report what happened. Shelf sensors check what's actually there and catch losses nobody scanned, like theft or breakage. Keeping the two jobs separate means a sale is never counted twice.

Bad messages, unknown products and sales larger than the stock on hand are logged and skipped. The listener keeps running.

## Setup

```bash
python -m pip install -r ml/requirements.txt
```

Install Mosquitto from https://mosquitto.org/download/ (Windows: `winget install EclipseFoundation.Mosquitto`).

## Running it

All commands run from the repo root.

**Offline demo (no broker, backend or database needed).** The simulator sends each message straight to the listener's logic, which updates an in-memory copy of the seed products:

```bash
python ml/simulator.py --offline --steps 30 --interval 0.2
```

**With the broker.** Use three terminals:

```bash
mosquitto -c ml/mosquitto.conf -v       # 1. the broker
python ml/listener.py --dry-run         # 2. listener, in-memory stock
python ml/simulator.py                  # 3. fake devices
```

Drop `--dry-run` to update the real backend. The backend must be running at `http://127.0.0.1:8000` with the database loaded. When the backend is up, the simulator also loads its starting stock from it.

Settings can be changed with environment variables: `MQTT_HOST`, `MQTT_PORT` and `NSTOCK_API_URL`.

Useful simulator options:

- `--steps N` stops after N ticks.
- `--interval S` waits S seconds between ticks.
- `--shelf-every N` makes the shelves report every N ticks.
- `--shrink-chance P` sets the chance of an unscanned loss on each tick.
- `--seed N` makes the run repeatable.

## Tests

```bash
python -m pytest ml -v
```

| File | Covers |
|---|---|
| `test_messages.py` | Message format: valid messages parse, malformed ones are rejected with a reason |
| `test_listener.py` | Each message type causes the right stock change; failures are skipped, not crashed |
| `test_simulator.py` | Simulator behavior, plus the end-to-end stock math: after every shelf report, the database matches the shelves |
| `test_live.py` | Real broker round trip and real backend round trip; each skips itself if its service isn't running |

## Files

| File | What it is |
|---|---|
| `config.py` | Broker and backend addresses, demo products |
| `messages.py` | Topic names, message format, parsing and validation |
| `stock_api.py` | HTTP client for the backend, plus an in-memory stand-in |
| `listener.py` | Subscribes to device topics and applies stock updates |
| `simulator.py` | The fake store and devices |
| `mosquitto.conf` | Local broker config |
