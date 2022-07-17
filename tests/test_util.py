import pytest
from _pytest.compat import getfuncargnames

from pytest_lambda import wrap_fixture


class DescribeWrapFixture:

    def it_includes_extended_and_wrapped_args_in_spec(self):
        def fixture(fixture_unique):
            pass

        @wrap_fixture(fixture)
        def extended_fixture(extension_unique, wrapped):
            pass

        args = getfuncargnames(extended_fixture)

        expected = {'fixture_unique', 'extension_unique'}
        actual = set(args) - {'request'}
        assert expected == actual

    def it_orders_decorated_method_args_first(self):
        def fixture(fixture_unique):
            pass

        @wrap_fixture(fixture)
        def extended_fixture(extension_unique, wrapped):
            pass

        args = getfuncargnames(extended_fixture)

        expected = ('extension_unique', 'fixture_unique', 'request')
        actual = args
        assert expected == actual


    def it_passes_wrapped_fixture_to_extension(self, request):
        class Called(AssertionError):
            pass

        def fixture():
            raise Called()

        @wrap_fixture(fixture)
        def extended_fixture(wrapped):
            wrapped()

        with pytest.raises(Called):
            extended_fixture(request=request)


    def it_allows_calling_wrapped_fixture_without_args(self, request):
        def fixture(message):
            return message

        @wrap_fixture(fixture)
        def extended_fixture(wrapped):
            return wrapped()

        expected = 'unique message'
        actual = extended_fixture(request=request, message=expected)
        assert expected == actual


    def it_allows_calling_wrapped_fixture_with_overridden_args(self, request):
        def fixture(message):
            return message

        @wrap_fixture(fixture)
        def extended_fixture(wrapped):
            return wrapped(message='overridden message')

        expected = 'overridden message'
        actual = extended_fixture(request=request, message='unique message')
        assert expected == actual


    def it_allows_calling_wrapped_fixture_with_ignored_args(self, request):
        def fixture(message):
            return message

        @wrap_fixture(fixture, ignore='message')
        def extended_fixture(wrapped):
            return wrapped(message='overridden message')

        expected = 'overridden message'
        actual = extended_fixture(request=request)
        assert expected == actual


    def it_passes_extension_args_to_extension(self, request):
        def fixture(*args, **kwargs):
            pass

        @wrap_fixture(fixture)
        def extended_fixture(wrapped, extension_arg):
            return extension_arg

        expected = 'extension'
        actual = extended_fixture(request=request, extension_arg=expected)
        assert expected == actual


    def it_doesnt_pass_extension_args_to_wrapped_fixture(self, request):
        def fixture(*args, **kwargs):
            return args, kwargs

        @wrap_fixture(fixture)
        def extended_fixture(wrapped, extension_arg):
            return wrapped()

        expected = (), {}
        actual = extended_fixture(request=request, extension_arg='stuff')
        assert expected == actual, \
            'Expected no args or kwargs to be passed to wrapped fixture'
