"""Shared test fixtures."""

import os

import pytest


@pytest.fixture
def sample_pdf_path():
    """Return path to data/sample.pdf, skip if not present."""
    path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), os.pardir, "data", "sample.pdf")
    )
    if not os.path.isfile(path):
        pytest.skip("data/sample.pdf not found — skipping PDF tests")
    return path
