from __future__ import annotations

import functools
import inspect
from types import ModuleType
from typing import Any, Generic, List, Optional, Tuple, TypeVar, Union, cast

import pytest
import wrapt  # type: ignore[import]
from _pytest.mark import ParameterSet

from .compat import _PytestWrapper
from .types import LambdaFixtureKwargs

try:
    from collections.abc import Iterable, Sized
except ImportError:
    from collections import Iterable, Sized

_IDENTITY_LAMBDA_FORMAT = '''
{name} = lambda {argnames}: ({argnames})
'''

_DESTRUCTURED_PARAMETRIZED_LAMBDA_FORMAT = '''
{name} = lambda {source_name}: {source_name}[{index}]
'''


def create_identity_lambda(name, *argnames):
    source = _IDENTITY_LAMBDA_FORMAT.format(name=name, argnames=', '.join(argnames))
    context: dict[str, Any]  = {}
    exec(source, context)

    fixture_func = context[name]
    return fixture_func


def create_destructured_parametrized_lambda(name: str, source_name: str, index: int):
    source = _DESTRUCTURED_PARAMETRIZED_LAMBDA_FORMAT.format(
        name=name, source_name=source_name, index=index
    )
    context: dict[str, Any] = {}
    exec(source, context)

    fixture_func = context[name]
    return fixture_func


VT = TypeVar('VT')


class LambdaFixture(Generic[VT], wrapt.ObjectProxy):
    # NOTE: pytest won't apply marks unless the markee has a __call__ and a
    #       __name__ defined.
    __name__ = '<lambda-fixture>'

    _self_iter: Iterable | None
    _self_params_source: LambdaFixture | None

    def __init__(
        self,
        fixture_names_or_lambda,
        *,
        bind: bool = False,
        async_: bool = False,
        _params_source: Optional['LambdaFixture'] = None,
        **fixture_kwargs,
    ):
        self.bind = bind
        self.is_async = async_
        self.fixture_kwargs = cast(LambdaFixtureKwargs, fixture_kwargs)
        self.fixture_func = self._not_implemented
        self.has_fixture_func = False
        self.parent = None
        self._self_iter = None
        self._self_params_source = _params_source

        #: pytest fixture info definition
        self._pytestfixturefunction = pytest.fixture(**fixture_kwargs)

        # Instruct pytest not to unwrap our fixture down to its original lambda, but
        # instead treat the LambdaFixture as the fixture function.
        self.__pytest_wrapped__ = _PytestWrapper(self)

        if fixture_names_or_lambda is not None:
            supports_iter = (
                not callable(fixture_names_or_lambda)
                and not isinstance(fixture_names_or_lambda, str)
                and isinstance(fixture_names_or_lambda, Iterable)
            )
            if supports_iter:
                fixture_names_or_lambda = tuple(fixture_names_or_lambda)

            self.set_fixture_func(fixture_names_or_lambda)

            if supports_iter:
                self._self_iter = map(
                    lambda name: LambdaFixture(name),
                    fixture_names_or_lambda,
                )

        elif fixture_kwargs.get('params'):
            # Shortcut to allow `lambda_fixture(params=[1,2,3])`
            self.set_fixture_func(lambda request: request.param)

            params = fixture_kwargs['params'] = tuple(fixture_kwargs['params'])
            self._self_iter = _LambdaFixtureParametrizedIterator(self, params)

    def __call__(self, *args, **kwargs) -> VT:
        if self.bind:
            args = (self.parent,) + args
        return self.fixture_func(*args, **kwargs)

    def __iter__(self):
        if self._self_iter:
            return iter(self._self_iter)

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

            if self.is_async:
                @functools.wraps(real_fixture_func)
                async def insulator(*args, **kwargs):
                    val = real_fixture_func(*args, **kwargs)
                    if inspect.isawaitable(val):
                        val = await val
                    return val

            else:
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
        """Set up the LambdaFixture for the given class/module

        This method is called during collection, when a LambdaFixture is
        encountered in a module or class. This method is responsible for saving
        any names and setting any attributes on parent as necessary.
        """
        is_in_class = isinstance(parent, type)
        is_in_module = isinstance(parent, ModuleType)
        assert is_in_class or is_in_module

        if is_in_module and self.bind:
            source_location = getattr(parent, '__file__', 'the parent')
            raise ValueError(f'bind=True cannot be used at the module level. '
                             f'Please remove this arg in the {name} fixture in {source_location}')

        if self._self_params_source:
            self.set_fixture_func(self._not_implemented)

        elif not self.has_fixture_func:
            # If no fixture definition was passed to lambda_fixture, it's our
            # responsibility to define it as the name of the attribute. This is
            # handy if ya just wanna force a fixture to be used, e.g.:
            #    do_the_thing = lambda_fixture(autouse=True)
            self.set_fixture_func(name)

        self.__name__ = self.fixture_func.__name__ = name
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

    def _get__class__(self):
        try:
            self.__wrapped__
        except ValueError:
            return LambdaFixture
        else:
            return self.__wrapped__.__class__

    def _set__class__(self, val):
        self.__wrapped__.__class__ = val

    # NOTE: @property is avoided on __class__, as it interfered with the PyCharm/pydev debugger
    __class__ = property(_get__class__, _set__class__)  # type: ignore[assignment]
    del _get__class__
    del _set__class__

    # These properties are required in order to expose attributes stored on the
    # LambdaFixture proxying instance without prefixing them with _self_

    @property
    def bind(self) -> bool: return self._self_bind
    @bind.setter
    def bind(self, value: bool) -> None: self._self_bind = value

    @property
    def is_async(self) -> bool: return self._self_is_async
    @is_async.setter
    def is_async(self, value: bool) -> None: self._self_is_async = value

    @property
    def fixture_kwargs(self) -> LambdaFixtureKwargs: return self._self_fixture_kwargs
    @fixture_kwargs.setter
    def fixture_kwargs(self, value) -> None: self._self_fixture_kwargs = value

    @property
    def fixture_func(self): return self._self_fixture_func
    @fixture_func.setter
    def fixture_func(self, value) -> None: self._self_fixture_func = value

    @property
    def has_fixture_func(self) -> bool: return self._self_has_fixture_func
    @has_fixture_func.setter
    def has_fixture_func(self, value: bool) -> None: self._self_has_fixture_func = value

    @property
    def parent(self) -> type | ModuleType | None: return self._self_parent
    @parent.setter
    def parent(self, value: type | ModuleType): self._self_parent = value

    @property
    def _pytestfixturefunction(self) -> bool: return self._self__pytestfixturefunction
    @_pytestfixturefunction.setter
    def _pytestfixturefunction(self, value: bool) -> None: self._self__pytestfixturefunction = value

    @property
    def __pytest_wrapped__(self) -> _PytestWrapper: return self._self___pytest_wrapped__
    @__pytest_wrapped__.setter
    def __pytest_wrapped__(self, value: _PytestWrapper) -> None: self._self___pytest_wrapped__ = value


class _LambdaFixtureParametrizedIterator:
    def __init__(self, source: LambdaFixture, params: Iterable):
        self.source = source
        self.params = tuple(params)

        self.num_params = self._get_param_set_length(self.params[0]) if self.params else 0
        self.destructured: List[LambdaFixture] = []

    def __iter__(self):
        if self.destructured:
            raise RuntimeError('Lambda fixtures may only be destructured once.')

        for i in range(self.num_params):
            child = LambdaFixture(None, _params_source=self.source)
            self.destructured.append(child)
            yield child

    @property
    def child_names(self) -> Tuple[str, ...]:
        return tuple(child.__name__ for child in self.destructured)

    @staticmethod
    def _get_param_set_length(param: Union[ParameterSet, Iterable, Any]) -> int:
        if isinstance(param, ParameterSet):
            return len(param.values)
        elif isinstance(param, Sized) and not isinstance(param, (str, bytes)):
            return len(param)
        else:
            return 1
