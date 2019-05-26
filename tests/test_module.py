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
