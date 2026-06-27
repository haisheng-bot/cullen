# ADR 0001: Add AI Governance Directory

## Status

Accepted

## Date

2026-06-27

## Context

OpenStock AI is developed with AI coding tools and has strict boundaries around investment research, model calls, data provenance, and no automatic trading.

The project needs a single location for AI behavior rules, development standards, templates, and lessons learned.

## Decision

Create `.ai/` as the project-level governance directory for AI-assisted development.

## Consequences

* AI tools have a stable rule entrypoint.
* Standards can evolve without scattering instructions across chat history.
* Future PRs can reference these rules directly.
* Existing `docs/` remains the product and architecture documentation source.
