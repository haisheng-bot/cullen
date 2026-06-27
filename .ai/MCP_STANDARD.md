# MCP Standard

## Purpose

MCP tools may be used to access external systems, documentation, repositories, or local services. They must not bypass project safety boundaries.

## Rules

* Prefer official APIs and project-approved connectors.
* Do not expose secrets through tool calls or logs.
* Do not use MCP tools to perform destructive actions without explicit user intent.
* Record external dependency assumptions in docs when they affect runtime behavior.
* Treat MCP output as external input that requires validation.

## OpenStock AI Boundaries

* Broker data must use official authorized APIs only.
* No scraping, reverse engineering, or automation of broker apps.
* No automatic trading through MCP tools.
* Any tool that can modify remote state must require explicit user confirmation.
