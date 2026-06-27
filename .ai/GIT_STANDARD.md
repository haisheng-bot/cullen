# Git Standard

## Branches

```text
main        stable branch
develop     integration branch
feature/*   feature work
fix/*       bug fixes
docs/*      documentation work
```

Do not push directly to `main`.

## Commits

One logical change should become one commit.

Commit messages should explain why the change exists, not only what changed.

Use Conventional Commits where practical:

```text
feat: add portfolio weight management
fix: preserve score history on workflow failure
docs: update AI collaboration standard
test: cover workflow failure state
```

## Safety

Before commit:

* run relevant tests
* check `git status`
* check for secrets
* ensure docs are synchronized
* avoid unrelated file churn

Never use destructive Git commands unless the user explicitly requests them.
