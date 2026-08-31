"""constraints 服务用例：约束知识库装载投影（CP1——ConstraintPicker 数据面前置）。

输入:  data/constraint_kb/constraints.json（kb 1.0.0 起草态——AI 起草待追认）
输出:  ConstraintCatalog（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（CP1 D1~D5 2026-08-31；镜像测试 server/tests/services/test_constraints.py）
#
# 【公开接口】
#   list_constraints(data_dir: Path) -> ConstraintCatalog（18 条=过滤 6+
#      出水参考 12——kb 声明序；D6 不分页整发）
#   ConstraintCatalog/ConstraintEntry（响应模型面——routers response_model
#      直用，units 服务先例：禁协议层重复声明漂移面）
#
# 【行为规格】
#   R1 真源投影：条目八键逐字来自 constraints.json——服务层零数值字面量
#      （数值真源=coefficients factors.yaml 同值投影，value_basis 逐条
#      溯源注记；kb README「数值不另立权威」纪律）。
#   R2 fail-visible 装载（kb 缺失/损坏 JSON/条目缺键/kind 越界/key 重复
#      →RuntimeError 显式拒——禁静默空表：与 units D1 缺名显式拒同族；
#      单条坏档=整库拒[库级完整性]，非逐条跳过[恢复流 registry 面差异]）。
#   R3 确定性/缓存：静态只读 catalog——路径键缓存（同路径单例；data_dir
#      变更=新键自然重载；返回 frozen 实例——main R1 工厂可重复构建不破）；
#      双跑 sort_keys 字节同（端点测试常驻断言）。
#   R4 DSL 校验边界：表达式语法/字段合法性归 core apply_constraints
#      运行期守卫（未知字段即拒 InvalidConstraintError——枚举行字段命名
#      空间无静态注册表，加载期不重复校验；kb README 差异记档同面）。
#
# 【测试要求】真源投影（18 条/两类 kind/unit_kinds 面/key 唯一）、
#   fail-visible 四路（缺失/损坏/缺键/重复）、缓存单例、双跑字节同、
#   路由 200 形态（client 面）。
#
# 【参照】data/constraint_kb/README.md（schema+收录边界）；CP1 简报
#   D1~D5；META1 units.py 同构模板；explore-CP1-freeze.md §二
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ConstraintCatalog",
    "ConstraintEntry",
    "list_constraints",
]

# kb 条目键面（八键齐全——README schema；缺一即库级拒）。
_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "key",
        "kind",
        "unit_kinds",
        "label",
        "expression",
        "source",
        "severity",
        "value_basis",
    }
)
_KINDS: frozenset[str] = frozenset({"enumeration_filter", "effluent_standard"})


class ConstraintEntry(BaseModel):
    """约束条目：八键齐全投影（value_basis=数值溯源——UI tooltip 面）。"""

    model_config = ConfigDict(frozen=True)

    key: str
    kind: Literal["enumeration_filter", "effluent_standard"]
    unit_kinds: tuple[str, ...]
    label: str
    expression: str
    source: str
    severity: str
    value_basis: str


class ConstraintCatalog(BaseModel):
    """约束目录响应体（D6 不分页整发——kb 声明序）。"""

    model_config = ConfigDict(frozen=True)

    entries: tuple[ConstraintEntry, ...]


@lru_cache(maxsize=None)  # 无字面量纪律（maxsize 数值面=魔法数字门禁）——路径键单例：生产恰 1 键，测试临时目录逐键微量
def _load(data_dir_str: str) -> ConstraintCatalog:
    """装载正门（路径键缓存单例——R2 fail-visible/R3 确定性）。"""
    path = Path(data_dir_str) / "constraint_kb" / "constraints.json"
    if not path.is_file():
        raise RuntimeError(
            f"约束知识库未就绪：{path} 不存在（constraint_kb 归数据包面——"
            "CP1 D4 装载显式拒，禁静默空表）"
        )
    try:
        raw = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"约束知识库损坏：{path}（{type(exc).__name__}: {exc}——CP1 D4）"
        ) from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list):
        raise RuntimeError(f"约束知识库形态非法：{path}（须为 {{entries: […]}}）")
    entries: list[ConstraintEntry] = []
    seen: set[str] = set()
    for position, item in enumerate(raw["entries"]):
        where = f"条目[{position}]"
        if not isinstance(item, dict):
            raise RuntimeError(f"约束知识库{where}非对象：{item!r}")
        missing = _REQUIRED_KEYS - item.keys()
        if missing:
            raise RuntimeError(f"约束知识库{where}缺键 {sorted(missing)}：{item.get('key')!r}")
        key = str(item["key"])
        if key in seen:
            raise RuntimeError(f"约束知识库 key 重复：{key!r}（README 硬规则——key 稳定唯一）")
        seen.add(key)
        if item["kind"] not in _KINDS:
            raise RuntimeError(
                f"约束知识库{where} kind 越界：{item['kind']!r}（合法面 {sorted(_KINDS)}）"
            )
        if not isinstance(item["unit_kinds"], list) or not all(
            isinstance(u, str) for u in item["unit_kinds"]
        ):
            raise RuntimeError(
                f"约束知识库{where} unit_kinds 须为字符串列表：{item['unit_kinds']!r}"
            )
        entries.append(
            ConstraintEntry(
                key=key,
                kind=item["kind"],
                unit_kinds=tuple(str(u) for u in item["unit_kinds"]),
                label=str(item["label"]),
                expression=str(item["expression"]),
                source=str(item["source"]),
                severity=str(item["severity"]),
                value_basis=str(item["value_basis"]),
            )
        )
    return ConstraintCatalog(entries=tuple(entries))


def list_constraints(data_dir: Path) -> ConstraintCatalog:
    """约束目录正门（D6 不分页整发；data_dir 键缓存——测试真源/临时目录双态）。"""
    return _load(str(data_dir))
