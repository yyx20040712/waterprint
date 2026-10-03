"""openapi 导出保真镜像测试：契约枚举 ⊇ server 白名单（1A2 批·memo⑤）。

输入:  api-contracts/openapi.json（ConstraintEntry kind/enforcement 枚举现位
       ——只读对照，禁动本体）+waterprint_server.services.constraints
       （_KINDS/_ENFORCEMENTS 白名单）
输出:  守卫断言——openapi kind 枚举 ⊇ _KINDS ∧ enforcement 枚举 ⊇
       _ENFORCEMENTS（防「代码扩枚举、契约面滞后」静默漂移——1A1 kind
       欠账事件〔input_band 漏重导出〕流程缺口根治，k1-N5）+红证 canary
       （参数化注入假枚举缺失一员→守卫同路必红）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：1A2 校验骨架批（1a2-20261004）§3.4 memo⑤——openapi 导出保真
#   守卫（1A6 轮门一 k1 新发现追加项）。方向性=单侧 ⊇：契约面允许领先
#   server（先行扩枚举），滞后即红；红证形态=断言侧参数化注入假枚举
#   缺失一员（禁动 openapi.json 本体——1a6 批 d0399b6 先例的检测器面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from waterprint_server.services.constraints import _ENFORCEMENTS, _KINDS

_REPO = Path(__file__).resolve().parents[3]  # server/tests/services/→仓库根
_OPENAPI = _REPO / "api-contracts" / "openapi.json"
_ENTRY_PATH = ("components", "schemas", "ConstraintEntry", "properties")


def _openapi_enum(field: str) -> frozenset[str]:
    """openapi ConstraintEntry.<field> 的枚举面（路径缺失=KeyError 响亮红）。"""
    node: Any = json.loads(_OPENAPI.read_text(encoding="utf-8"))
    for key in (*_ENTRY_PATH, field):
        node = node[key]
    return frozenset(str(member) for member in node["enum"])


def _assert_covered(
    contract: frozenset[str], server: frozenset[str], field: str
) -> None:
    """守卫单源：契约枚举必须覆盖 server 白名单（缺失即 AssertionError）。"""
    missing = sorted(server - contract)
    assert not missing, (
        f"openapi {field} 枚举滞后于 server 白名单：缺 {missing}"
        "（「代码扩枚举、契约面滞后」静默漂移——1A1 kind 欠账事件根治守卫）")


@pytest.mark.parametrize(
    ("field", "server_face"),
    [("kind", _KINDS), ("enforcement", _ENFORCEMENTS)],
)
def test_openapi_enums_cover_server_whitelists(
    field: str, server_face: frozenset[str]
) -> None:
    """主守卫：openapi 枚举 ⊇ server 白名单（双枚举面——契约面允许领先）。"""
    contract = _openapi_enum(field)
    assert contract  # 契约面在场非空（形态崩坏=KeyError/空集双路红）
    assert server_face  # 白名单非空（d1-N5：_KINDS/_ENFORCEMENTS 退化空集→主守卫失效防线）
    _assert_covered(contract, frozenset(server_face), field)


@pytest.mark.parametrize("dropped", sorted(_KINDS))
def test_guard_catches_missing_kind_member(dropped: str) -> None:
    """红证 canary（kind 面）：注入缺失一员的假枚举→守卫同路必红——
    openapi 真枚举若滞后一员，主守卫以同一断言路径红（灵敏度实证）。"""
    lagging = _openapi_enum("kind") - {dropped}
    with pytest.raises(AssertionError):
        _assert_covered(lagging, frozenset(_KINDS), "kind")


@pytest.mark.parametrize("dropped", sorted(_ENFORCEMENTS))
def test_guard_catches_missing_enforcement_member(dropped: str) -> None:
    """红证 canary（enforcement 面）：同 kind 面——假枚举缺一员必红。"""
    lagging = _openapi_enum("enforcement") - {dropped}
    with pytest.raises(AssertionError):
        _assert_covered(lagging, frozenset(_ENFORCEMENTS), "enforcement")
