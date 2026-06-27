# RAG Standard

## Purpose

RAG and knowledge retrieval support financial research by supplying traceable context to models and reports.

## Data Requirements

Retrieved context must preserve:

* source name
* source URL or file path when available
* retrieval time
* document date when available
* symbol or portfolio scope
* confidence or data quality notes

## Rules

* Do not mix unverified generated text into the knowledge base as fact.
* Do not hide missing or stale source data.
* Prefer primary sources for SEC filings, macro data, and official disclosures.
* Keep raw retrieval separate from model interpretation.

## Outputs

RAG-backed AI output must cite retrieved context and include the project risk disclaimer for investment-related analysis.
