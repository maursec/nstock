# NStock

A web-based inventory and supply planning tool for small businesses: real-time stock tracking, automated reordering and demand forecasting.

Software Engineering final project, CSU Dominguez Hills.

## Team

| Name | Role |
|---|---|
| Jasmynn Vaughan | Project lead and database design |
| Andrew Navarro | Backend and API |
| Julen Moss | Frontend and UI/UX |
| Abdullah Hasan | ML and IoT integration |

## Tech stack

- **Database:** MySQL
- **Backend:** Python (FastAPI)
- **Frontend:** Angular (TypeScript, SCSS)
- **Forecasting:** Python (pandas, scikit-learn)
- **IoT:** MQTT (paho-mqtt, Mosquitto)

## Repository layout

```
database/   schema, migrations, seed and backup scripts
backend/    API server
frontend/   Angular app
ml/         forecasting model and IoT listener/simulator
docs/       design decisions, meeting notes, report drafts
```

## Getting started

Setup steps will go here once each part is runnable.

## How we work

1. Pick an issue from the project board and assign it to yourself.
2. Create a branch from `main`: `git checkout -b feature/short-description`
3. Commit, push, and open a pull request. Fill out the template.
4. At least one teammate reviews and approves before merging.
5. Never push directly to `main`.

## Documentation

- [Design decisions](docs/decisions.md)
