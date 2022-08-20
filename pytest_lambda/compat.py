try:
    from typing import TypedDict
except ImportError:  # Python < 3.8
    from typing_extensions import TypedDict

try:
    from _pytest.compat import _PytestWrapper
except ImportError:  # pytest<4
    # Old pytest versions set the wrapped value directly to __pytest_wrapped__
    class _PytestWrapper:  # type: ignore[no-redef]
        def __new__(cls, obj):
            return obj
