from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Callable, Optional

import mypy
import mypy.types
from mypy import types, nodes
from mypy.checker import TypeChecker
from mypy.plugin import AnalyzeTypeContext, FunctionContext, Plugin

#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
MYPY_BASE_PATH = Path(mypy.__file__).parent

spec = importlib.util.spec_from_file_location('mypy.plugin', str(MYPY_BASE_PATH / 'plugin.py'))
assert spec

mypy_py_plugin = importlib.util.module_from_spec(spec)
loader = spec.loader
assert loader
loader.exec_module(mypy_py_plugin)


def wrap_method(fn):
    signature = inspect.signature(fn)

    def _wrapper(*args, **kwargs):
        call = signature.bind(*args, **kwargs)
        args_str = ', '.join(
            f'{arg}={value!r}'
            for arg, value in call.arguments.items()
            if arg != 'self'
        )
        rval = '<unknown>'
        try:
            rval = fn(*args, **kwargs)
            return rval
        finally:
            print(f'{fn.__name__}({args_str}) == {rval!r}')

    return _wrapper


class DebugPlugin(Plugin):
    for name in dir(mypy_py_plugin.Plugin):
        if not name.startswith('_') and callable(meth := getattr(mypy_py_plugin.Plugin, name)):
            locals()[name] = wrap_method(meth)

#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################
#XXX######################################################################################

QN_LAMBDA_FIXTURE_FUNCTION = 'pytest_lambda.fixtures.lambda_fixture'
QN_LAMBDA_FIXTURE_TYPE = 'pytest_lambda.impl.LambdaFixture'


def lambda_fixture_call_hook(ctx: FunctionContext) -> types.Type:
    assert isinstance(ctx.api, TypeChecker)

    if ctx.args[0] and isinstance(ctx.args[0][0], nodes.FuncItem):
        return ctx.default_return_type

    return ctx.default_return_type
    # return types.NoneType()


def lambda_fixture_type_hook(ctx: AnalyzeTypeContext) -> types.Type:
    return ctx.type


class PytestLambdaPlugin(Plugin):
    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], types.Type] | None:
        if fullname == QN_LAMBDA_FIXTURE_FUNCTION:
            return lambda_fixture_call_hook
        else:
            return None

    def get_type_analyze_hook(
        self, fullname: str
    ) -> Callable[[AnalyzeTypeContext], types.Type] | None:
        if fullname == QN_LAMBDA_FIXTURE_TYPE:
            return lambda_fixture_type_hook
        else:
            return None


def plugin(version: str):
    #XXX######################################################################################
    return PytestLambdaPlugin
    # return DebugPlugin
    #XXX######################################################################################
