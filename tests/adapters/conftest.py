import pytest

from hermitage.adapters import CQEA


@pytest.fixture
def adapter():
    return CQEA()
