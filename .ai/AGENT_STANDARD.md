# Agent Development Standard

## Role

Agents define research tasks and reasoning goals. They do not own model provider integration.

## Required Pipeline

Agents should follow this pipeline:

```text
Policy Guard
Data Context Builder
Workflow Executor
Model Layer
Output Validator
Audit Logger
```

## Boundaries

Agents must not:

* directly call OpenAI, Anthropic, Google, DeepSeek, Qwen, Ollama, or other model SDKs
* read model API keys
* skip output validation
* skip audit logging for AI outputs
* produce trading commands

## Outputs

Agent outputs must include:

* symbol or portfolio identifier
* data sources
* analysis time
* model metadata when applicable
* citations when available
* confidence or uncertainty
* risk disclaimer

## New Agents

Before adding an Agent, check whether an existing workflow, algorithm, or report agent can be extended with a smaller change.
