import functools
from types import ModuleType
from typing import Callable, Union

import pytest
import wrapt

_IDENTITY_LAMBDA_FORMAT = '''
{name} = lambda {argnames}: ({argnames})
'''


def create_identity_lambda(name, *argnames):
    source = _IDENTITY_LAMBDA_FORMAT.format(name=name, argnames=', '.join(argnames))
    context = {}
    exec(source, context)

    fixture_func = context[name]
    return fixture_func


class LambdaFixture(wrapt.ObjectProxy):
    # NOTE: pytest won't apply marks unless the markee has a __call__ and a
    #       __name__ defined.
    __name__ = '<lambda-fixture>'

    bind: bool
    fixture_kwargs: dict
    fixture_func: Callable
    has_fixture_func: bool
    parent: Union[type, ModuleType]

    def __init__(self, fixture_names_or_lambda, bind=False, **fixture_kwargs):
        self.bind = bind
        self.fixture_kwargs = fixture_kwargs
        self.fixture_func = self._not_implemented
        self.has_fixture_func = False
        self.parent = None

        #: pytest fixture info definition
        self._pytestfixturefunction = pytest.fixture(**fixture_kwargs)

        if fixture_names_or_lambda is not None:
            self.set_fixture_func(fixture_names_or_lambda)

        elif fixture_kwargs.get('params'):
            # Shortcut to allow `lambda_fixture(params=[1,2,3])`
            self.set_fixture_func(lambda request: request.param)

    def __call__(self, *args, **kwargs):
        if self.bind:
            args = (self.parent,) + args
        return self.fixture_func(*args, **kwargs)

    def _not_implemented(self):
        raise NotImplementedError(
            'The fixture_func for this LambdaFixture has not been defined. '
            'This is a catastrophic error!')

    def set_fixture_func(self, fixture_names_or_lambda):
        self.fixture_func = self.build_fixture_func(fixture_names_or_lambda)
        self.has_fixture_func = True

        # NOTE: this initializes the ObjectProxy
        super().__init__(self.fixture_func)

    def build_fixture_func(self, fixture_names_or_lambda):
        if callable(fixture_names_or_lambda):
            real_fixture_func = fixture_names_or_lambda

            # We create a new method with the same signature as the passed
            # method, which simply calls the passed method – this is so we can
            # modify __name__ and other properties of the function without fear
            # of overwriting functions unrelated to the fixture. (A lambda need
            # not be used – a method imported from another module can be used.)

            @functools.wraps(real_fixture_func)
            def insulator(*args, **kwargs):
                return real_fixture_func(*args, **kwargs)

            return insulator

        else:
            if self.bind:
                raise ValueError(
                    'bind must be False if requesting a fixture by name')

            fixture_names = fixture_names_or_lambda
            if isinstance(fixture_names, str):
                fixture_names = (fixture_names,)

            # Create a new method with the requested parameter, so pytest can
            # determine its dependencies at parse time. If we instead use
            # request.getfixturevalue, pytest won't know to include the fixture
            # in its dependency graph, and will vomit with "The requested
            # fixture has no parameter defined for the current test."
            name = 'fixture__' + '__'.join(fixture_names)  # XXX: will this conflict in certain circumstances?
            return create_identity_lambda(name, *fixture_names)

    def contribute_to_parent(self, parent: Union[type, ModuleType], name: str, **kwargs):
        """Setup the LambdaFixture for the given class/module

        This method is called during collection, when a LambdaFixture is
        encountered in a module or class. This method is responsible for saving
        any names and setting any attributes on parent as necessary.
        """
        is_in_class = isinstance(parent, type)
        is_in_module = isinstance(parent, ModuleType)
        assert is_in_class or is_in_module

        if is_in_module and self.bind:
            raise ValueError(f'bind=True cannot be used at the module level. '
                             f'Please remove this arg in the {name} fixture in {parent.__file__}')

        if not self.has_fixture_func:
            # If no fixture definition was passed to lambda_fixture, it's our
            # responsibility to define it as the name of the attribute. This is
            # handy if ya just wanna force a fixture to be used, e.g.:
            #    do_the_thing = lambda_fixture(autouse=True)
            self.set_fixture_func(name)

        self.__name__ = name
        self.__module__ = self.fixture_func.__module__ = (
            parent.__module__ if is_in_class else parent.__name__)
        self.parent = parent

    # With --doctest-modules enabled, the doctest finder will enumerate all objects
    # in all relevant modules, and use `isinstance(obj, ...)` to determine whether
    # the object has doctests to collect. Under the hood, isinstance retrieves the
    # value of the `obj.__class__` attribute.
    #
    # When using implicit referential lambda fixtures (e.g. `name = lambda_fixture()`),
    # the LambdaFixture object doesn't initialize its underlying object proxy until the
    # pytest collection phase. Unfortunately, doctest's scanning occurs before this.
    # When doctest attempts `isinstance(lfix, ...)` on an implicit referential
    # lambda fixture and accesses `__class__`, the object proxy tries to curry
    # the access to its wrapped object — but there isn't one, so it raises an error.
    #
    # To address this, we override __class__ to return LambdaFixture when the
    # object proxy has not yet been initialized.

    @property
    def __class__(self):
        try:
            self.__wrapped__
        except ValueError:
            return LambdaFixture
        else:
            return self.__wrapped__.__class__

    @__class__.setter
    def __class__(self, val):
        self.__wrapped__.__class__ = val

    # These properties are required in order to expose attributes stored on the
    # LambdaFixture proxying instance without prefixing them with _self_

    @property
    def bind(self):
        return self._self_bind

    @bind.setter
    def bind(self, value):
        self._self_bind = value

    @property
    def fixture_kwargs(self):
        return self._self_fixture_kwargs

    @fixture_kwargs.setter
    def fixture_kwargs(self, value):
        self._self_fixture_kwargs = value

    @property
    def fixture_func(self):
        return self._self_fixture_func

    @fixture_func.setter
    def fixture_func(self, value):
        self._self_fixture_func = value

    @property
    def has_fixture_func(self):
        return self._self_has_fixture_func

    @has_fixture_func.setter
    def has_fixture_func(self, value):
        self._self_has_fixture_func = value

    @property
    def parent(self):
        return self._self_parent

    @parent.setter
    def parent(self, value):
        self._self_parent = value

    @property
    def _pytestfixturefunction(self):
        return self._self__pytestfixturefunction

    @_pytestfixturefunction.setter
    def _pytestfixturefunction(self, value):
        self._self__pytestfixturefunction = value
