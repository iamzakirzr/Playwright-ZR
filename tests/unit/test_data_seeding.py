"""Unit tests for reproducible test data (data/factories.py and the root conftest's reseeding)."""

import os

from data import BookingFactory, UserFactory, seed_factories


def test_same_seed_gives_same_data():
    """Two runs with the same seed build identical objects."""
    seed_factories("123:tests/api/test_x.py::test_y")
    first = BookingFactory.build()
    seed_factories("123:tests/api/test_x.py::test_y")

    assert BookingFactory.build() == first


def test_each_test_gets_its_own_stream():
    """Different test ids under one base seed produce different data (no accidental sharing)."""
    seed_factories("123:test_a")
    a = UserFactory.build()
    seed_factories("123:test_b")

    assert UserFactory.build() != a


def test_base_seed_is_shared_with_xdist_workers(pytestconfig):
    """Regression: every xdist worker drew its own seed, so the header's seed couldn't replay a worker's failure."""
    assert os.environ["FAKER_SEED"] == str(pytestconfig._faker_seed)
