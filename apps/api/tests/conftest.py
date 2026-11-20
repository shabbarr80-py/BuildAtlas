import os

import pytest

# Keep tests isolated from a developer's runtime DATABASE_URL, while allowing
# CI to opt in to PostgreSQL explicitly with TEST_DATABASE_URL.
if not os.environ.get("TEST_DATABASE_URL"):
    os.environ["TEST_DATABASE_URL"] = "sqlite:///./buildatlas-test.db"

from app.core.database import Base, engine
from app.models import entities  # noqa: F401


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
