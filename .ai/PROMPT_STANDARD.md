# Prompt Standard

## Scope

Prompts are product behavior. They must be versioned, reviewable, and aligned with the investment research boundary.

## Required Elements

Investment research prompts must specify:

* task objective
* input data sources
* output schema or expected sections
* uncertainty handling
* forbidden investment language
* required risk disclaimer

## Forbidden Language

Prompts must not ask models to guarantee:

* profit
* price targets as certainty
* risk-free outcomes
* buy or sell instructions

## Data Grounding

Prompts must instruct the model to:

* cite available data inputs
* distinguish facts from interpretation
* mention missing data
* avoid fabricating financial metrics, filings, or news

## Location

Prompt logic should live with the Agent or Model Layer component that owns it. Shared prompt patterns may be extracted only after reuse exists.
