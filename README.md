# pytest-lambda

[![PyPI version](https://badge.fury.io/py/pytest-lambda.svg)](https://badge.fury.io/py/pytest-lambda)

Define pytest fixtures with lambda functions.


# Quickstart

```bash
pip install pytest-lambda
```

```python
# test_the_namerator.py

from pytest_lambda import lambda_fixture, static_fixture

first = static_fixture('John')
middle = static_fixture('Jacob')
last = static_fixture('Jingleheimer-Schmidt')


full_name = lambda_fixture(lambda first, middle, last: f'{first} {middle} {last}')


def test_the_namerator(full_name):
    assert full_name == 'John Jacob Jingleheimer-Schmidt'
```


# Cheatsheet

 ```python
import asyncio
import pytest
from pytest_lambda import (
    disabled_fixture,
    error_fixture,
    lambda_fixture,
    not_implemented_fixture,
    static_fixture,
)

# Basic usage
fixture_name = lambda_fixture(lambda other_fixture: 'expression', scope='session', autouse=True)

# Async fixtures (awaitables automatically awaited) — requires an async plugin, like pytest-asyncio
fixture_name = lambda_fixture(lambda: asyncio.sleep(0, 'expression'), async_=True)

# Request fixtures by name
fixture_name = lambda_fixture('other_fixture')
fixture_name = lambda_fixture('other_fixture', 'another_fixture', 'cant_believe_its_not_fixture')
ren, ame, it = lambda_fixture('other_fixture', 'another_fixture', 'cant_believe_its_not_fixture')

# Reference `self` inside a class
class TestContext:
    fixture_name = lambda_fixture(lambda self: self.__class__.__name__, bind=True)

# Parametrize
fixture_name = lambda_fixture(params=['a', 'b'])
fixture_name = lambda_fixture(params=['a', 'b'], ids=['A!', 'B!'])
fixture_name = lambda_fixture(params=[pytest.param('a', id='A!'),
                                      pytest.param('b', id='B!')])
alpha, omega = lambda_fixture(params=[pytest.param('start', 'end', id='uno'),
                                      pytest.param('born', 'dead', id='dos')])

# Use literal value (not lazily evaluated)
fixture_name = static_fixture(42)
fixture_name = static_fixture('just six sevens', autouse=True, scope='module')

# Raise an exception if fixture is requested
fixture_name = error_fixture(lambda: ValueError('my life has no intrinsic value'))

# Or maybe don't raise the exception
fixture_name = error_fixture(lambda other_fixture: TypeError('nope') if other_fixture else None)

# Create an abstract fixture (to be overridden by the user)
fixture_name = not_implemented_fixture()
fixture_name = not_implemented_fixture(autouse=True, scope='session')

# Disable usage of a fixture (fail early to save future head scratching)
fixture_name = disabled_fixture()
```


# What else is possible?

Of course, you can use lambda fixtures inside test classes:
```python
# test_staying_classy.py

from pytest_lambda import lambda_fixture

class TestClassiness:
    classiness = lambda_fixture(lambda: 9000 + 1)

    def test_how_classy_we_is(self, classiness):
        assert classiness == 9001
```


### Aliasing other fixtures

You can also pass the name of another fixture, instead of a lambda:
```python
# test_the_bourne_identity.py

from pytest_lambda import lambda_fixture, static_fixture

agent = static_fixture('Bourne')
who_i_am = lambda_fixture('agent')

def test_my_identity(who_i_am):
    assert who_i_am == 'Bourne'
```


Even multiple fixture names can be used:
```python
# test_the_bourne_identity.py

from pytest_lambda import lambda_fixture, static_fixture

agent_first = static_fixture('Jason')
agent_last = static_fixture('Bourne')
who_i_am = lambda_fixture('agent_first', 'agent_last')

def test_my_identity(who_i_am):
    assert who_i_am == ('Jason', 'Bourne')
```

Destructuring assignment is also supported, allowing multiple fixtures to be renamed in one statement:
```python
# test_the_bourne_identity.py

from pytest_lambda import lambda_fixture, static_fixture

agent_first = static_fixture('Jason')
agent_last = static_fixture('Bourne')
first, last = lambda_fixture('agent_first', 'agent_last')

def test_my_identity(first, last):
    assert first == 'Jason'
    assert last == 'Bourne'
```


#### Annotating aliased fixtures

You can force the loading of fixtures without trying to remember the name of `pytest.mark.usefixtures`
```python
# test_garage.py

from pytest_lambda import lambda_fixture, static_fixture

car = static_fixture({
    'type': 'Sweet-ass Cadillac',
    'is_started': False,
})
turn_the_key = lambda_fixture(lambda car: car.update(is_started=True))

preconditions = lambda_fixture('turn_the_key', autouse=True)

def test_my_caddy(car):
    assert car['is_started']
```


### Parametrizing

Tests can be parametrized with `lambda_fixture`'s `params` kwarg
```python
# test_number_5.py

from pytest_lambda import lambda_fixture

lady = lambda_fixture(params=[
    'Monica', 'Erica', 'Rita', 'Tina', 'Sandra', 'Mary', 'Jessica'
])

def test_your_man(lady):
    assert lady[:0] in 'my life'
```

Destructuring assignment of a parametrized lambda fixture is also supported
```python
# test_number_5.py

import pytest
from pytest_lambda import lambda_fixture

lady, where = lambda_fixture(params=[
    pytest.param('Monica', 'in my life'),
    pytest.param('Erica', 'by my side'),
    pytest.param('Rita', 'is all I need'),
    pytest.param('Tina', 'is what I see'),
    pytest.param('Sandra', 'in the sun'),
    pytest.param('Mary', 'all night long'),
    pytest.param('Jessica', 'here I am'),
])

def test_your_man(lady, where):
    assert lady[:0] in where
```


### Declaring abstract things

`not_implemented_fixture` is perfect for labeling abstract parameter fixtures of test mixins
```python
# test_mixinalot.py

import pytest
from pytest_lambda import static_fixture, not_implemented_fixture

class Dials1900MixinALot:
    butt_shape = not_implemented_fixture()
    desires = not_implemented_fixture()

    def it_kicks_them_nasty_thoughts(self, butt_shape, desires):
        assert butt_shape == 'round' and 'triple X throw down' in desires


@pytest.mark.xfail
class DescribeMissThing(Dials1900MixinALot):
    butt_shape = static_fixture('flat')
    desires = static_fixture(['playin workout tapes by Fonda'])


class DescribeSistaICantResista(Dials1900MixinALot):
    butt_shape = static_fixture('round')
    desires = static_fixture(['gettin in yo Benz', 'triple X throw down'])
```


Use `disabled_fixture` to mark a fixture as disabled. Go figure.
```python
# test_ada.py

import pytest
from pytest_lambda import disabled_fixture

wheelchair = disabled_fixture()

@pytest.mark.xfail(strict=True)
def test_stairs(wheelchair):
    assert wheelchair + 'floats'
```


### Raising exceptions

You can also raise an arbitrary exception when a fixture is requested, using `error_fixture`
```python
# test_bikeshed.py

import pytest
from pytest_lambda import error_fixture, not_implemented_fixture, static_fixture

bicycle = static_fixture('a sledgehammer')

def it_does_sweet_jumps(bicycle):
    assert bicycle + 'jump' >= '3 feet'


class ContextOcean:
    depth = not_implemented_fixture()
    bicycle = error_fixture(lambda bicycle, depth: (
        RuntimeError(f'Now is not the time to use that! ({bicycle})') if depth > '1 league' else None))


    class ContextDeep:
        depth = static_fixture('20,000 leagues')

        @pytest.mark.xfail(strict=True, raises=RuntimeError)
        def it_doesnt_flip_and_shit(self, bicycle):
            assert bicycle + 'floats'


    class ContextBeach:
        depth = static_fixture('1 inch')

        def it_gets_you_all_wet_but_otherwise_rides_like_a_champ(self, bicycle):
            assert 'im wet'
```


### Async fixtures

By passing `async_=True` to `lambda_fixture`, the fixture will be defined as an async function, and if the returned value is awaitable, it will be automatically awaited before exposing it to pytest. This allows the usage of async things while only being slightly salty that Python, TO THIS DAY, still does not support `await` expressions within lambdas! Yes, only slightly salty!

NOTE: an asyncio pytest plugin is required to use async fixtures, such as [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)

```python
# test_a_sink.py

import asyncio
import pytest
from pytest_lambda import lambda_fixture

async def hows_the_sink():
    await asyncio.sleep(1)
    return 'leaky'

a_sink = lambda_fixture(lambda: hows_the_sink(), async_=True)

class DescribeASink:
    @pytest.mark.asyncio
    async def it_is_leaky(self, a_sink):
        assert a_sink is 'leaky'
```


# Development

How can I build and test the thing locally?

1. Create a virtualenv, however you prefer. Or don't, if you prefer.
2. `pip install poetry`
3. `poetry install` to install setuptools entrypoint, so pytest automatically loads the plugin (otherwise, you'll have to run `py.test -p pytest_lambda.plugin`)
4. Run `py.test --markdown-docs`. The tests will be collected from the README.md (thanks to [pytest-markdown-docs](https://github.com/modal-labs/pytest-markdown-docs)).
