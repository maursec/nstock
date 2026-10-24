# Design Decisions

A running log of the choices we make and why. This feeds the System Design section of the final report.

Each entry: date, the decision, the options we considered, and the reason.

---

## YYYY-MM-DD: Example — MySQL as the database
**Options considered:** MySQL, PostgreSQL, SQLite
**Decision:** MySQL
**Why:** Matches the course's suggested stack for an inventory system, the team has experience with it, and free hosting options exist. SQLite stays an option for a desktop build.


## 2026-10-24: Forecasting as a feature
**Options considered:** Keeping it, testing a yr's worth of seed data
**Decision:** Remove forecasting as a feature
**Why:** Keeps the application lightweight and streamlines us to a finished product.
