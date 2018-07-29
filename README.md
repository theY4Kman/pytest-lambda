# pytest-lambda

Define pytest fixtures with lambda functions.


# Quickstart

```bash
pip install pytest-lambda
```

```python
# test_the_namerator.py

import pytest

first = pytest.static_fixture('John')
middle = pytest.static_fixture('Jacob')
last = pytest.static_fixture('Jingleheimer-Schmidt')


full_name = pytest.lambda_fixture(lambda first, middle, last: f'{first} {middle} {last}')


def test_the_namerator(full_name):
    assert full_name == 'John Jacob Jingleheimer-Schmidt'
```


# Cheatsheet

 ```python
import pytest

# Basic usage
fixture_name = pytest.lambda_fixture(lambda other_fixture: 'expression', scope='session', autouse=True)

# Request fixtures by name
fixture_name = pytest.lambda_fixture('other_fixture')
fixture_name = pytest.lambda_fixture('other_fixture', 'another_fixture', 'cant_believe_its_not_fixture')

# Reference `self` inside a class
class TestContext:
    fixture_name = pytest.lambda_fixture(lambda self: self.__class__.__name__, bind=True)

# Parametrize
fixture_name = pytest.lambda_fixture(lambda request: request.param, params=['a', 'b'], ids=['A!', 'B!'])
fixture_name = pytest.lambda_fixture(lambda request: request.param, 
                                      params=[pytest.param('a', id='A!'), 
                                              pytest.param('b', id='B!')])

# Use literal value (not lazily evaluated)
fixture_name = pytest.static_fixture(42)
fixture_name = pytest.static_fixture('just six sevens', autouse=True, scope='module')

# Raise an exception if fixture is requested
fixture_name = pytest.error_fixture(lambda: ValueError('my life has no intrinsic value'))

# Or maybe don't raise the exception
fixture_name = pytest.error_fixture(lambda other_fixture: TypeError('nope') if other_fixture else None)

# Create an abstract fixture (to be overridden by the user)
fixture_name = pytest.not_implemented_fixture()
fixture_name = pytest.not_implemented_fixture(autouse=True, scope='session')

# Disable usage of a fixture (fail early to save future head scratching)
fixture_name = pytest.disabled_fixture()
```


# What else is possible?

Of course, you can use lambda fixtures inside test classes:
```python
# test_staying_classy.py

import pytest

class TestClassiness:
    classiness = pytest.lambda_fixture(lambda: 9000 + 1)

    def test_how_classy_we_is(self, classiness):
        assert classiness == 9001
```


### Aliasing other fixtures

You can also pass the name of another fixture, instead of a lambda:
```python
# test_the_bourne_identity.py

import pytest

agent = pytest.static_fixture('Bourne')
who_i_am = pytest.lambda_fixture('agent')

def test_my_identity(who_i_am):
    assert who_i_am == 'Bourne'
```


Even multiple fixture names can be used:
```python
# test_the_bourne_identity.py

import pytest

agent_first = pytest.static_fixture('Jason')
agent_last = pytest.static_fixture('Bourne')
who_i_am = pytest.lambda_fixture('agent_first', 'agent_last')

def test_my_identity(who_i_am):
    assert who_i_am == ('Jason', 'Bourne')
```


#### Annotating aliased fixtures

You can force the loading of fixtures without trying to remember the name of `pytest.mark.usefixtures`
```python
# test_garage.py

import pytest

car = pytest.static_fixture({
    'type': 'Sweet-ass Cadillac',
    'is_started': False,
})
turn_the_key = pytest.lambda_fixture(lambda car: car.update(is_started=True))

preconditions = pytest.lambda_fixture('turn_the_key', autouse=True)

def test_my_caddy(car):
    assert car['is_started']
```


### Declaring abstract things

`not_implemented_fixture` is perfect for labeling abstract parameter fixtures of test mixins
```python
# test_mixinalot.py

import pytest

class Dials1900MixinALot:
    butt_shape = pytest.not_implemented_fixture()
    desires = pytest.not_implemented_fixture()

    def it_kicks_them_nasty_thoughts(self, butt_shape, desires):
        assert butt_shape == 'round' and 'triple X throw down' in desires


@pytest.mark.xfail
class DescribeMissThing(Dials1900MixinALot):
    butt_shape = pytest.static_fixture('flat')
    desires = pytest.static_fixture(['playin workout tapes by Fonda'])


class DescribeSistaICantResista(Dials1900MixinALot):
    butt_shape = pytest.static_fixture('round')
    desires = pytest.static_fixture(['gettin in yo Benz',
                                     'triple X throw down'])
```


Use `disabled_fixture` to mark a fixture as disabled. Go figure.
```python
# test_ada.py

import pytest

wheelchair = pytest.disabled_fixture()

@pytest.mark.xfail(strict=True)
def test_stairs(wheelchair):
    assert wheelchair + 'floats'
```


### Raising exceptions

You can also raise an arbitrary exception when a fixture is requested, using `error_fixture`
```python
# test_bikeshed.py

import pytest

bicycle = pytest.static_fixture('a sledgehammer')

def it_does_sweet_jumps(bicycle):
    assert bicycle + 'jump' >= '3 feet'


class ContextOcean:
    depth = pytest.static_fixture('20,000 leagues')
    bicycle = pytest.error_fixture(lambda bicycle, depth: (
        RuntimeError(f'Now is not the time to use that! ({bicycle})') if depth > '1 league' else None))

    @pytest.mark.xfail(strict=True, raises=RuntimeError)
    def it_doesnt_flip_and_shit(self, bicycle):
        assert bicycle + 'floats'


    class ContextBeach:
        depth = pytest.static_fixture('1 inch')

        def it_gets_you_all_wet_but_otherwise_rides_like_a_champ(self, bicycle):
            assert 'im wet'
```


# Development

How can I build and test the thing locally?

1. Create a virtualenv, however you prefer. Or don't, if you prefer.
2. `pip install -r dev-requirements.txt`
3. `flit install -s` to install setuptools entrypoint, so pytest automatically loads the plugin (otherwise, you'll have to run `py.test -p pytest_lambda.plugin`)
4. Run `py.test`. The tests will be collected from the README.md (thanks to [pytest-markdown](https://github.com/Jc2k/pytest-markdown)).
