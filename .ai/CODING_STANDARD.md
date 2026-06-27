# Coding Standard

## General

* Prefer simple, explicit Python.
* Reuse existing modules before adding new helpers.
* Keep functions small enough to test directly.
* Avoid broad refactors during feature work.
* Do not reformat unrelated files.

## Python

* Use type hints for public functions and data boundaries.
* Use Pydantic schemas for API request and response validation.
* Raise meaningful exceptions at module boundaries.
* Convert external failures into safe API errors.
* Keep business logic outside FastAPI route handlers when it grows.

## Imports

* Import provider SDKs only inside approved provider modules.
* Do not import model vendor SDKs outside `packages/model_layer/providers`.
* Do not import broker SDKs outside approved broker or data source adapters.

## Data Handling

* Treat external market data as fallible.
* Include source, analysis time, and risk disclaimer in investment outputs.
* Prefer best-effort fallback only when the user experience remains honest.

## Comments

Add comments only when they explain non-obvious decisions, data limitations, or compliance boundaries.
