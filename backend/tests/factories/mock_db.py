"""Shared mock helpers for SQLAlchemy database results in tests."""


class MockResult:
    """Mocks an SQLAlchemy result object.

    Supports the common chained-call patterns used in the codebase:
        result.scalars().all()
        result.scalar_one_or_none()
        result.one_or_none()
    """

    def __init__(self, data):
        self._data = data

    def scalars(self):
        return self

    def all(self):
        return self._data

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None

    def one_or_none(self):
        return self._data[0] if self._data else None

    def __iter__(self):
        return iter(self._data)
