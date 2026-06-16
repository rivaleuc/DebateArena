"""Test harness: inject a fake `genlayer` module, then load the real contract.

The fake module is a minimal, deterministic stand-in for the GenLayer SDK:
  * passthrough @gl.public.write / @gl.public.view decorators
  * gl.Contract base that auto-initializes TreeMap fields
  * gl.vm.Return + gl.vm.run_nondet_unsafe (runs leader, then asserts the
    normalized leader output passes the validator, and records both fns so
    tests can probe the validator directly)
  * u256 as an int subclass, TreeMap.__class_getitem__ for annotations
  * gl.message / gl.nondet stubs (exec_prompt is overridable per test)
"""
import os
import sys
import types
import importlib.util

import pytest


def _build_genlayer():
    mod = types.ModuleType("genlayer")

    class u256(int):
        pass

    class TreeMap(dict):
        @classmethod
        def __class_getitem__(cls, item):
            return cls

    class Return:
        def __init__(self, calldata):
            self.calldata = calldata

    class _Web:
        def get(self, url):
            raise RuntimeError("web access is stubbed in tests")

    class _Nondet:
        def __init__(self):
            self.web = _Web()

        def exec_prompt(self, prompt, response_format=None):
            return {}

    class _Message:
        sender_address = "0x0000000000000000000000000000000000000001"

    class _Public:
        @staticmethod
        def write(fn):
            return fn

        @staticmethod
        def view(fn):
            return fn

    class _VM:
        def __init__(self):
            self.Return = Return
            self._last_leader = None
            self._last_validator = None

        def run_nondet_unsafe(self, leader_fn, validator_fn):
            self._last_leader = leader_fn
            self._last_validator = validator_fn
            out = leader_fn()
            if not validator_fn(Return(out)):
                raise AssertionError("validator rejected the normalized leader output")
            return out

    class Contract:
        def __new__(cls, *args, **kwargs):
            obj = super().__new__(cls)
            anns = {}
            for klass in reversed(cls.__mro__):
                anns.update(getattr(klass, "__annotations__", {}) or {})
            for fname, ftype in anns.items():
                if isinstance(ftype, type) and issubclass(ftype, TreeMap):
                    setattr(obj, fname, TreeMap())
            return obj

    gl = types.SimpleNamespace(
        Contract=Contract,
        public=_Public(),
        message=_Message(),
        nondet=_Nondet(),
        vm=_VM(),
    )
    mod.gl = gl
    mod.TreeMap = TreeMap
    mod.u256 = u256
    mod.__all__ = ["gl", "TreeMap", "u256"]
    return mod, gl


_GENLAYER_MOD, _GL = _build_genlayer()
sys.modules["genlayer"] = _GENLAYER_MOD

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONTRACT_PATH = os.path.join(_HERE, "..", "debate_arena.py")


def _load_contract_module():
    spec = importlib.util.spec_from_file_location("contract_under_test", _CONTRACT_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def gl_mod():
    return _GL


@pytest.fixture(autouse=True)
def _reset_gl():
    _GL.nondet.exec_prompt = lambda *a, **k: {}
    _GL.message.sender_address = "0x0000000000000000000000000000000000000001"
    yield


@pytest.fixture
def contract():
    m = _load_contract_module()
    for v in vars(m).values():
        if isinstance(v, type) and issubclass(v, _GL.Contract) and v is not _GL.Contract:
            return v()
    raise RuntimeError("no gl.Contract subclass found in contract module")
