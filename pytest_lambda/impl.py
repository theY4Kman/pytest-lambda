import functools


_IDENTITY_LAMBDA_FORMAT = '''
{name} = lambda {argnames}: ({argnames})
'''


def create_identity_lambda(name, *argnames):
    source = _IDENTITY_LAMBDA_FORMAT.format(name=name, argnames=', '.join(argnames))
    context = {}
    exec(source, context)

    fixture_func = context[name]
    return fixture_func


class LambdaFixture:
    def __init__(self, fixture_names_or_lambda, bind=False, **fixture_kwargs):
        self.bind = bind
        self.fixture_kwargs = fixture_kwargs
        self.fixture_func = self._not_implemented
        self.has_fixture_func = False

        if fixture_names_or_lambda is not None:
            self.set_fixture_func(fixture_names_or_lambda)

    def _not_implemented(self):
        raise NotImplementedError(
            'The fixture_func for this LambdaFixture has not been defined. '
            'This is a catastrophic error!')

    def set_fixture_func(self, fixture_names_or_lambda):
        self.fixture_func = self.build_fixture_func(fixture_names_or_lambda)
        self.has_fixture_func = True

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
