try:
    from _pytest.compat import _PytestWrapper
except ImportError:  # pytest<4
    # Old pytest versions set the wrapped value directly to __pytest_wrapped__
    _PytestWrapper = lambda obj: obj
