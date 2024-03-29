from __future__ import annotations

import inspect
from typing import NoReturn, TYPE_CHECKING, Callable, Any, Iterable, Tuple, TypeVar

from pytest_lambda.exceptions import DisabledFixtureError, NotImplementedFixtureError
from pytest_lambda.impl import LambdaFixture

if TYPE_CHECKING:
    from _pytest.fixtures import _Scope

__all__ = ['lambda_fixture', 'static_fixture', 'error_fixture',
           'disabled_fixture', 'not_implemented_fixture']


VT = TypeVar('VT')


def lambda_fixture(
    fixture_name_or_lambda: str | Callable[..., VT] | None = None,
    *other_fixture_names: str,
    bind: bool = False,
    async_: bool = False,
    scope: _Scope = 'function',
    params: Iterable[object] | None = None,
    autouse: bool = False,
    ids: Iterable[None | str | float | int | bool] | Callable[[Any], object | None] | None = None,
    name: str | None = None,
) -> LambdaFixture[VT]:
    """Use a fixture name or lambda function to compactly declare a fixture

    Usage:

        class DescribeMyTests:
            url = lambda_fixture('list_url')
            updated_name = lambda_fixture(lambda vendor: vendor.name + ' updated')


    :param fixture_name_or_lambda:
        Either the name of another fixture, or a lambda function, which can request other fixtures
        with its params. If None, this defaults to the name of the attribute containing the
        lambda_fixture.

    :param bind:
        Set this to True to pass self to your fixture. It must be the first parameter in your
        fixture. This cannot be True if using a fixture name.

    :param async_:
        If True, the lambda will be wrapped in an async function; if the lambda evaluates to an
        awaitable value, it will be awaited. If False, the lambda's return value will be returned
        verbatim, regardless of whether it's awaitable.

    :param scope:
    :param params:
    :param autouse:
    :param ids:
    :param name:
        Options to pass to pytest.fixture()

    """
    fixture_names_or_lambda: Tuple[str | Callable, ...] | str | Callable | None

    if other_fixture_names:
        if fixture_name_or_lambda is None:
            raise ValueError('If specified, all fixture names must be non-null.')
        fixture_names_or_lambda = (fixture_name_or_lambda,) + other_fixture_names
    else:
        fixture_names_or_lambda = fixture_name_or_lambda

    return LambdaFixture(
        fixture_names_or_lambda,
        bind=bind,
        async_=async_,
        scope=scope, params=params, autouse=autouse, ids=ids, name=name,
    )


def static_fixture(value: VT, **fixture_kwargs) -> LambdaFixture[VT]:
    """Compact method for defining a fixture that returns a static value
    """
    return lambda_fixture(lambda: value, **fixture_kwargs)


RAISE_EXCEPTION_FIXTURE_FUNCTION_FORMAT = '''
def raise_exception({args}):
    exc = error_fn({kwargs})
    if exc is not None:
        raise exc
'''


def error_fixture(error_fn: Callable, **fixture_kwargs) -> LambdaFixture[NoReturn]:
    """Fixture whose usage results in the raising of an exception

    Usage:

        class DescribeMyTests:
            url = error_fixture(lambda request: Exception(
                f'Please override the {request.fixturename} fixture!'))

    :param error_fn:
        Fixture method which returns an exception to raise. It may request pytest fixtures
        in its arguments.

    """
    proto = tuple(inspect.signature(error_fn).parameters)
    args = ', '.join(proto)
    kwargs = ', '.join(f'{arg}={arg}' for arg in proto)

    source = RAISE_EXCEPTION_FIXTURE_FUNCTION_FORMAT.format(
        args=args,
        kwargs=kwargs,
    )

    ctx = {'error_fn': error_fn}
    exec(source, ctx)

    raise_exception = ctx['raise_exception']
    raise_exception.__module__ = getattr(error_fn, '__module__', raise_exception.__module__)
    return lambda_fixture(raise_exception, **fixture_kwargs)


def disabled_fixture(**fixture_kwargs) -> LambdaFixture[NoReturn]:
    """Mark a fixture as disabled – using the fixture will raise an error

    This is useful when you know any usage of a fixture would be in error. When
    using disabled_fixture, pytest will raise an error if the fixture is
    requested, so errors can be detected early, and faulty assumptions may be
    avoided.

    Usage:

        class DescribeMyListOnlyViewSet(ViewSetTest):
            list_route = lambda_fixture(lambda: reverse('...'))
            detail_route = disabled_fixture()

            class DescribeRetrieve(UsesDetailRoute):
                def test_that_should_throw_error():
                    print('I should never be executed!')

    """
    def build_disabled_fixture_error(request):
        msg = (f'Usage of the {request.fixturename} fixture has been disabled '
               f'in the current context.')
        return DisabledFixtureError(msg)

    return error_fixture(build_disabled_fixture_error, **fixture_kwargs)


def not_implemented_fixture(**fixture_kwargs) -> LambdaFixture[NoReturn]:
    """Mark a fixture as abstract – requiring definition/override by the user

    This is useful when defining abstract base classes requiring implementation
    to be used correctly.

    Usage:

        class MyBaseTest:
            list_route = not_implemented_fixture()

        class TestThings(MyBaseTest):
            list_route = lambda_fixture(lambda: reverse(...))

    """
    def build_not_implemented_fixture_error(request):
        msg = (f'Please define/override the {request.fixturename} fixture in '
               f'the current context.')
        return NotImplementedFixtureError(msg)

    return error_fixture(build_not_implemented_fixture_error, **fixture_kwargs)
