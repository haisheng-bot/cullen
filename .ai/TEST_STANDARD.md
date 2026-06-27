# Test Standard

## Required Practice

Run relevant tests for every behavior change.

Default full test command:

```bash
python3 -m unittest discover -s tests
```

Use the project virtual environment when available:

```bash
.venv311/bin/python -m unittest discover -s tests
```

## Coverage Expectations

Add or update tests for:

* new API behavior
* bug fixes
* algorithm changes
* workflow node behavior
* model output validation
* database persistence
* security or compliance boundaries

## Test Data

* Do not require paid API keys for unit tests.
* Mock external services where possible.
* Keep tests deterministic.
* Do not delete failing tests to make a run pass.
