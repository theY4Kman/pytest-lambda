import pytest

from pytest_lambda import lambda_fixture, static_fixture


unique = lambda_fixture(lambda: 'unique')


def it_processes_toplevel_lambda_fixture(unique):
    expected = 'unique'
    actual = unique
    assert expected == actual


unique_static = static_fixture('unique')


def it_processes_toplevel_static_fixture(unique_static):
    expected = 'unique'
    actual = unique_static
    assert expected == actual


unique_alias = lambda_fixture('unique_static')


def it_processes_toplevel_aliased_lambda_fixture(unique_alias):
    expected = 'unique'
    actual = unique_alias
    assert expected == actual


a = static_fixture('a')
b = static_fixture('b')
c = static_fixture('c')
abc = lambda_fixture('a', 'b', 'c')


def it_processes_toplevel_tuple_lambda_fixture(abc):
    expected = ('a', 'b', 'c')
    actual = abc
    assert expected == actual


x, y, z = lambda_fixture('a', 'b', 'c')


def it_processes_toplevel_destructured_tuple_lambda_fixture(x, y, z):
    expected = ('a', 'b', 'c')
    actual = (x, y, z)
    assert expected == actual


pa, pb, pc, pd = lambda_fixture(params=[
    pytest.param('alfalfa', 'better', 'dolt', 'gamer'),
])


def it_processes_toplevel_destructured_parametrized_lambda_fixture(pa, pb, pc, pd):
    expected = ('alfalfa', 'better', 'dolt', 'gamer')
    actual = (pa, pb, pc, pd)
    assert expected == actual


destructured_id = lambda_fixture(params=[
    pytest.param('muffin', id='muffin'),
])


def it_uses_ids_from_destructured_parametrized_lambda_fixture(destructured_id, request):
    assert destructured_id in request.node.callspec.id


class TestClass:
    a = lambda_fixture()

    def it_processes_implicit_reference_fixture(self, a):
        expected = 'a'
        actual = a
        assert expected == actual
