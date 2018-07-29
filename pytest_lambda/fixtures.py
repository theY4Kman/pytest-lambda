import inspect
from typing import Union, Callable, Any, Iterable

from pytest_lambda.exceptions import DisabledFixtureError, NotImplementedFixtureError
from pytest_lambda.impl import LambdaFixture

__all__ = ['lambda_fixture', 'static_fixture', 'error_fixture',
           'disabled_fixture', 'not_implemented_fixture']


def lambda_fixture(fixture_name_or_lambda: Union[str, Callable]=None,
                   *other_fixture_names: Iterable[str],
                   bind=False,
                   scope="function", params=None, autouse=False, ids=None, name=None):
    """Use a fixture name or lambda function to compactly declare a fixture

    Usage:

        class DescribeMyTests:
            url = lambda_fixture('list_url')
            updated_name = lambda_fixture(lambda vendor: vendor.name + ' updated')


    :param fixture_name_or_lambda: Either the name of another fixture, or a
        lambda function, which can request other fixtures with its params. If
        None, this defaults to the name of the attribute containing the lambda_fixture.

    :param bind: Set this to true to pass self to your fixture. It must be the
        first parameter in your fixture. This cannot be true if using a fixture
        name.

    """
    if other_fixture_names:
        fixture_names_or_lambda = (fixture_name_or_lambda,) + other_fixture_names
    else:
        fixture_names_or_lambda = fixture_name_or_lambda

    return LambdaFixture(fixture_names_or_lambda, bind=bind, scope=scope,
                         params=params, autouse=autouse, ids=ids, name=name)


def static_fixture(value: Any, **fixture_kwargs):
    """Compact method for defining a fixture that returns a static value
    """
    return lambda_fixture(lambda: value, **fixture_kwargs)


RAISE_EXCEPTION_FIXTURE_FUNCTION_FORMAT = '''
def raise_exception({args}):
    raise error_fn({kwargs})
'''


def error_fixture(error_fn: Callable, **fixture_kwargs):
    """Fixture whose usage results in the raising of an exception

    Usage:

        class DescribeMyTests:
            url = error_fixture(lambda request: Exception(
                f'Please override the {request.fixturename} fixture!'))

    :param error_fn: fixture method which returns an exception to raise. It may
        request pytest fixtures in its arguments

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
    return lambda_fixture(raise_exception, **fixture_kwargs)


def disabled_fixture(**fixture_kwargs):
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


def not_implemented_fixture(**fixture_kwargs):
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
