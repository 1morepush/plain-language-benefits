"""Lets the tests `import app`, `import content`, etc. no matter where pytest is run from."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest  # noqa: E402

import content  # noqa: E402

FIXTURE_DATA = Path(__file__).parent / "tests" / "fixtures" / "data"
REAL_DATA = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def use_fixture_data(monkeypatch):
    """Tests run against small fake data in tests/fixtures/data, not the real form questions.

    That keeps the tests stable when questions are added or reworded. Tests that
    check the real data files ask for REAL_DATA by name.
    """
    monkeypatch.setattr(content, "DATA_DIR", FIXTURE_DATA)
