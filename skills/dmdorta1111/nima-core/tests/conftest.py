"""Shared fixtures for NIMA Core tests."""
import pytest
import numpy as np
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test persistence."""
    return tmp_path


@pytest.fixture
def sample_baseline():
    """Standard baseline vector for testing."""
    return np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)


@pytest.fixture
def high_care_input():
    """High CARE emotion input."""
    return {"CARE": 0.9}


@pytest.fixture
def high_fear_input():
    """High FEAR emotion input."""
    return {"FEAR": 0.8}


@pytest.fixture
def mixed_input():
    """Mixed emotion input."""
    return {"SEEKING": 0.7, "CARE": 0.6, "PLAY": 0.5}


AFFECT_NAMES = ["SEEKING", "RAGE", "FEAR", "LUST", "CARE", "PANIC", "PLAY"]
