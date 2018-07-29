import inspect
from collections import Callable
from types import ModuleType
from typing import Union

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
    is_lambda_fixture = lambda o: isinstance(o, LambdaFixture)
    for name, attr in inspect.getmembers(parent, is_lambda_fixture):
        if isinstance(attr, LambdaFixture):
            fixture = convert_lambda_fixture(name, attr, parent)
            setattr(parent, name, fixture)

    return parent


def convert_lambda_fixture(name, lfix: LambdaFixture, parent: Union[ModuleType, type]):
    """Convert a LambdaFixture into a pytest.fixture
    """
    is_in_class = isinstance(parent, type)
    is_in_module = isinstance(parent, ModuleType)
    assert is_in_class or is_in_module

    if is_in_module and lfix.bind:
        raise ValueError(
            f'bind=True cannot be used on fixtures defined at the module level. '
            f'Please remove this arg from the {name} fixture in {parent.__file__}')

    if not lfix.has_fixture_func:
        # If no fixture definition was passed to lambda_fixture, it's our
        # responsibility to define it as the name of the attribute. This is
        # handy if ya just wanna force a fixture to be used, e.g.:
        #    do_the_thing = lambda_fixture(autouse=True)
        lfix.set_fixture_func(name)

    fixture_func = lfix.fixture_func
    if is_in_class and not lfix.bind:
        fixture_func = eat_self_param(name, fixture_func)

    if is_in_class:
        fixture_func.__module__ = parent.__module__
    else:
        fixture_func.__module__ = parent.__name__

    kwargs = dict(lfix.fixture_kwargs)
    if kwargs.get('name') is None:
        kwargs['name'] = name

    fixture = pytest.fixture(**kwargs)(fixture_func)
    fixture.__name__ = name
    return fixture


EAT_SELF_FUNCTION_FORMAT = '''
def {name}(self, {args}):
    return fixture_impl({kwargs})
'''


def eat_self_param(name, fn: Callable):
    """Create a new method which ignores self and calls fn with rest of args
    """
    proto = tuple(inspect.signature(fn).parameters)
    args = ', '.join(proto)
    kwargs = ', '.join(f'{arg}={arg}' for arg in proto)

    source = EAT_SELF_FUNCTION_FORMAT.format(
        name=name,
        args=args,
        kwargs=kwargs,
    )

    ctx = {'fixture_impl': fn}
    exec(source, ctx)

    fixture_func = ctx[name]
    return fixture_func
