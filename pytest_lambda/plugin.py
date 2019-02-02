import inspect
from typing import List, Tuple

import pytest
from _pytest.python import Module

from pytest_lambda.impl import LambdaFixture


def get_attrs_to_expose_under_pytest() -> dict:
    """Attributes which should be accessible from the root pytest namespace"""
    import pytest_lambda
    return vars(pytest_lambda)


def pytest_addhooks(pluginmanager):
    # No hooks added, but we do monkeypatch the pytest module namespace to
    # expose our goods, a la pytest_namespace — but with less deprecation warnings.

    for name, val in get_attrs_to_expose_under_pytest().items():
        setattr(pytest, name, val)


def pytest_collectstart(collector):
    if isinstance(collector, Module):
        process_lambda_fixtures(collector.module)


def pytest_pycollect_makeitem(collector, name, obj):
    if inspect.isclass(obj):
        process_lambda_fixtures(obj)


def process_lambda_fixtures(parent):
    """Turn all lambda_fixtures in a class/module into actual pytest fixtures
    """
    lfix_attrs: List[Tuple[str, LambdaFixture]] = (
        inspect.getmembers(parent, lambda o: isinstance(o, LambdaFixture)))

    for name, attr in lfix_attrs:
        attr.contribute_to_parent(parent, name)

    return parent
