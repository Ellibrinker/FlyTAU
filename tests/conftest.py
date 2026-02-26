import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import main

@pytest.fixture
def app():
    main.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret",
    )
    return main.app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def fake_db(monkeypatch):

    class FakeCursor:
        def __init__(self):
            self.last_query = None
            self.last_params = None
            self._one = None
            self._all = []

        def execute(self, query, params=None):
            self.last_query = query
            self.last_params = params

        def fetchone(self):
            return self._one

        def fetchall(self):
            return self._all

        def set_one(self, value):
            self._one = value

        def set_all(self, value):
            self._all = value

    class FakeDBCur:
        def __init__(self, cursor):
            self.cursor = cursor
        def __enter__(self):
            return self.cursor
        def __exit__(self, exc_type, exc, tb):
            return False

    cursor = FakeCursor()

    def fake_db_cur():
        return FakeDBCur(cursor)

    monkeypatch.setattr(main, "db_cur", fake_db_cur)
    return cursor