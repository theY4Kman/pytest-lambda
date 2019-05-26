import inspect
from typing import List, Tuple

from _pytest.python import Module

from pytest_lambda.impl import LambdaFixture


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
