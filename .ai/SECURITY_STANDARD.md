# Security Standard

## Secrets

Never commit:

* API keys
* model provider keys
* broker credentials
* private keys
* account IDs
* tokens
* personal identity data

Use `.env` locally and keep `.env.example` safe and non-secret.

## Financial Safety

OpenStock AI must not:

* automatically place trades
* imply guaranteed returns
* hide risk warnings
* store sensitive broker data without a documented need

## Logging

Logs must not include secrets, full credentials, private keys, or sensitive personal data.

## External Data

* Use official APIs where required.
* Respect provider rate limits and terms.
* Validate and sanitize external responses before using them in AI output.
