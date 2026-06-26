"""Workflow Layer: orchestrates Universe, Portfolio, Algorithm, Agent and
Model Layer calls into end-to-end flows.

The reusable engine primitives live in `engine.py`; concrete workflows like
AI stock screening stay in separate modules so each flow remains independently
testable.
"""
