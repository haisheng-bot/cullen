# Database Standard

## General

Database changes must be backward-compatible when possible.

## Rules

* Schema changes require a documented migration path.
* Do not delete user or production-like data without explicit instruction.
* Prefer additive changes before destructive changes.
* Keep persistence logic in `packages/db`.
* Keep external data caches distinguishable from user-authored data.

## Auditability

AI outputs and workflow outputs should be traceable by:

* trace ID
* source data summary
* analysis time
* model metadata when applicable
* generated output
* risk disclaimer

## Tests

Database changes require tests for creation, readback, and failure behavior.
