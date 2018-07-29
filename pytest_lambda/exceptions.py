__all__ = ['DisabledFixtureError', 'NotImplementedFixtureError']


class DisabledFixtureError(Exception):
    """Thrown when a disabled fixture has been requested by a test or fixture

    See pytest_lambda.fixtures.disabled_fixture
    """


class NotImplementedFixtureError(NotImplementedError):
    """Thrown when an abstract fixture has been requested

    See pytest_lambda.fixtures.not_implemented_fixture
    """
