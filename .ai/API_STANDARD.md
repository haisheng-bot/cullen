# API Standard

## General

API behavior must be stable, explicit, and documented.

## Required Response Fields

Investment-related API responses should include:

* data source
* analysis time
* risk disclaimer

AI-generated responses should additionally include:

* model provider
* model name
* trace ID
* citations when available

## Errors

API errors should be meaningful and safe. Do not leak secrets, stack traces, or provider credentials.

## Versioning

Avoid breaking public endpoints. If a breaking change is unavoidable:

* document the reason
* update API docs
* provide migration notes
* consider a versioned route

## Documentation

When adding or changing an endpoint, update:

* `docs/api/api-design-v0.1.md`
* related product or standards docs
* tests under `tests/`
