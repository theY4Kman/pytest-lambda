import inspect
from typing import List, Sequence, Set, Tuple

import pytest
from _pytest.mark import Mark, ParameterSet
from _pytest.python import Metafunc, Module

from pytest_lambda.impl import LambdaFixture, _LambdaFixtureParametrizedIterator


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


@pytest.hookimpl(tryfirst=True)
def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Parametrize all tests using destructured parametrized lambda fixtures

    This is what powers things like:

        a, b, c = lambda_fixture(params=[
            pytest.param(1, 2, 3)
        ])

        def test_my_thing(a, b, c):
            assert a < b < c

    """
    param_sources: Set[LambdaFixture] = set()

    for argname in metafunc.fixturenames:
        # Get the FixtureDefs for the argname.
        fixture_defs = metafunc._arg2fixturedefs.get(argname)
        if not fixture_defs:
            # Will raise FixtureLookupError at setup time if not parametrized somewhere
            # else (e.g @pytest.mark.parametrize)
            continue

        for fixturedef in reversed(fixture_defs):
            param_source = getattr(fixturedef.func, '_self_params_source', None)
            if param_source:
                param_sources.add(param_source)

    if param_sources:
        requested_fixturenames = set(metafunc.fixturenames)

        for param_source in param_sources:
            if param_source.fixture_kwargs['params'] is None:
                continue

            params_iter = param_source._self_iter
            assert isinstance(params_iter, _LambdaFixtureParametrizedIterator)

            # TODO(zk): skip parametrization for args already parametrized by @mark.parametrize
            # XXX(zk): is there a way around falsifying the requested fixturenames to avoid "uses no argument" error?
            for child_name in params_iter.child_names:
                if child_name not in requested_fixturenames:
                    metafunc.fixturenames.append(child_name)
                    requested_fixturenames.add(child_name)

            metafunc.parametrize(
                params_iter.child_names,
                param_source.fixture_kwargs['params'],
                scope=param_source.fixture_kwargs.get('scope'),
                ids=param_source.fixture_kwargs.get('ids'),
            )
