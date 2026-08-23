"""run_env 镜像测试：RunEnv 执行环境上下文契约（UF-31 下沉 L0）。

输入:  waterprint.contracts.run_env 公开符号（RunEnv）
输出:  字段完备/不可变/装配确定性断言（实现合入后必须全绿；SENS-B 骨架先行，
       批 C（2026-08-23）收口镜像规则矛盾：源文件入锁即须有同名镜像）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.run_env")
RunEnv = getattr(_mod, "RunEnv", None)

pytestmark = pytest.mark.skipif(
    None in (RunEnv,),
    reason="实现未就绪：waterprint.contracts.run_env 公开符号缺失（RunEnv；"
    "装配正门与字段精确类型实现期冻结，T4/T7）",
)

# 规格头【公开接口】七字段全集（R1 上下文五件 + R2 engine_params）
_FIELDS = {
    "engine_version",
    "data_version",
    "assumptions",
    "coefficients",
    "price_book",
    "trace_sink",
    "engine_params",
}


def _dummy_env() -> object:
    """哑装配：字段精确类型未冻结（规格头声明），仅承载结构断言。"""
    return RunEnv(
        engine_version="0",
        data_version="0",
        assumptions={},
        coefficients={},
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def test_run_env_field_completeness() -> None:
    """字段完备：规格头七字段一一在册（多一少一都是规格漂移）。"""
    assert dataclasses.is_dataclass(RunEnv)
    assert {f.name for f in dataclasses.fields(RunEnv)} == _FIELDS


def test_run_env_immutable() -> None:
    """R3：装配一次、执行期只读——改写字段抛异常（frozen 数据类形态，同 Quantity/TraceNodeSpec 惯例）。"""
    env = _dummy_env()
    with pytest.raises(dataclasses.FrozenInstanceError):
        env.engine_version = "x"  # type: ignore[misc]


def test_run_env_construction_deterministic() -> None:
    """幂等/确定性：同输入两次装配逐字段相等（L0 哑载体无隐藏状态，R5）。"""
    assert _dummy_env() == _dummy_env()
