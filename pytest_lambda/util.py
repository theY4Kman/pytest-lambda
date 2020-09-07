import functools
from typing import Callable, Iterable, Union

from _pytest.compat import getfuncargnames, get_real_func
from _pytest.fixtures import call_fixture_func

__all__ = ['wrap_fixture']


def wrap_fixture(
    fixturefunc: Callable,
    wrapped_param: str = 'wrapped',
    ignore: Union[str, Iterable[str]] = (),
) -> Callable[[Callable], Callable]:
    """Wrap a fixture function, extending its argspec w/ the decorated method

    pytest will prune the fixture dependency graph of any unneeded fixtures. It
    does this by reading the expected arg names of fixtures. When wrapping a
    fixture function, merely currying along **kwargs will cripple pytest's
    pruning.

    This method retains the arg names from the original fixture function, and
    returns a wrapper method that includes those original arg names, as well as
    any fixtures requested by the decorated function.

    The decorated method will be passed a wrapper of the passed fixturefunc
    that can be called with no arguments — the fixtures it requested will
    receive automagical defaults, though these may be overridden. The argument
    name of this wrapped fixturefunc may be customized with the `wrapped_param`
    arg, so as to avoid any collision with other fixture names.

    Example (contrived):

        bare_user = lambda_fixture(lambda user_factory: user_factory(
            username='bare-user',
            password='bare-password',
        ))

        @pytest.fixture
        @wrap_fixture(bare_user)
        def admin_user(team, wrapped):
            user = wrapped()
            team.add_member(user, role_id=TeamRole.Roles.ADMIN)
            return user

    :param fixturefunc:
        The fixture function to wrap

    :param wrapped_param:
        Name of parameter to pass the wrapped fixturefunc as

    :param ignore:
        Name of parameter(s) from fixturefunc to not include in wrapping
        fixture's args (and thus not request as fixtures from pytest)

    """

    if isinstance(ignore, str):
        ignore = (ignore,)

    fixturefunc = get_real_func(fixturefunc)

    def decorator(fn: Callable):
        decorated_arg_names = set(getfuncargnames(fn))
        if wrapped_param not in decorated_arg_names:
            raise TypeError(
                f'The decorated method must include an arg named {wrapped_param} '
                f'as the wrapped fixture func.')

        # Don't include the wrapped param in the argspec we expose to pytest
        decorated_arg_names -= {wrapped_param}

        fixture_arg_names = set(getfuncargnames(fixturefunc)) - set(ignore)
        all_arg_names = fixture_arg_names | decorated_arg_names | {'request'}

        def extension_impl(**all_args):
            request = all_args['request']

            ###
            # kwargs requested by the wrapped fixture
            #
            fixture_args = {
                name: value
                for name, value in all_args.items()
                if name in fixture_arg_names
            }

            ###
            # kwargs requested by the decorated method
            #
            decorated_args = {
                name: value
                for name, value in all_args.items()
                if name in decorated_arg_names
            }

            @functools.wraps(fixturefunc)
            def wrapped(**overridden_args):
                kwargs = {
                    **fixture_args,
                    **overridden_args,
                }
                return call_fixture_func(fixturefunc, request, kwargs)

            decorated_args[wrapped_param] = wrapped
            return call_fixture_func(fn, request, decorated_args)

        extension = build_wrapped_method(fn.__name__, all_arg_names, extension_impl)
        return extension

    return decorator


_WRAPPED_FIXTURE_FORMAT = '''
def {name}({argnames}):
    return {impl_name}({kwargs})
'''


def build_wrapped_method(name: str, argnames: Iterable[str], impl: Callable) -> Callable:
    impl_name = '___extension_impl'
    argnames = tuple(argnames)

    source = _WRAPPED_FIXTURE_FORMAT.format(
        name=name,
        argnames=', '.join(argnames),
        kwargs=', '.join(f'{arg}={arg}' for arg in argnames),
        impl_name=impl_name
    )
    context = {impl_name: impl}
    exec(source, context)

    return context[name]
