from __future__ import annotations

from typing import Any, Callable, Iterable, TYPE_CHECKING

from .compat import TypedDict

if TYPE_CHECKING:
    from _pytest.fixtures import _Scope


class LambdaFixtureKwargs(TypedDict, total=False):
    scope: _Scope
    params: Iterable[object] | None
    autouse: bool
    ids: Iterable[None | str | float | int | bool] | Callable[[Any], object | None]
    name: str | None
