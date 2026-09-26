"""params_guard 守护族：方案参数四面守护纯函数（批3b 拆件自 flows/__init__ 迁驻）。

输入:  ProjectFile 目标单元 + 候选 params + discover_units 目录面
输出:  tuple[ParamVerdict, ...]（清单式逐条判定不拒整批）+ builtin 带声明常量
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（AI1-TRACK-A-2026-09-13 §3 签名冻结原文迁驻+批3b face④ 扩面
#   ——主控裁定 B-3b-1 案甲（b3b-blockers.md）；镜像测试 tests/app/
#   test_flows.py 导入面经 flows.__init__ 再导出零变）
#
# 【定位】flows 包内兄弟件（AGENTS §2 预算墙拆件——flows/__init__.py
#   499/500 顶墙实录；graph/cache.py 拆件先例）：仅由本包 __init__ 再
#   导出消费，禁跨包引用。
#
# 【公开接口】（经 flows.__init__ 再导出——签名冻结零变）
#   params_guard(project, unit_id, params) -> tuple[ParamVerdict, ...]
#   ParamVerdict(key, value, accepted, reason, warn=None)
#
# 【行为规格】四面守护（清单式逐条判定，首命中即拒）：
#   ①值=有限数值（bool/str/NaN 拒）②键=单元目录已知参数（kind 通道：
#   节点覆写含 kind 用 kind 查目录，否则 unit_id）③grid 声明时值须
#   命中档位 ④range 声明时值须落闭区间 [min,max]（批3b face④——
#   audit §一「range 声明后无人执法」收口；specs 来自 discover_units
#   目录=天然全量覆盖，无逐包枚举）。builtin kind（municipal_input/
#   quality_edit/junction/recycle_junction 无 manifest）：键面镜像声明
#   _BUILTIN_PARAM_KEYS；q_avg_daily 带=A-1~A-3（ERROR 拒收带+WARN
#   提示带 accepted=True 不阻塞仅提示）；kz 不设带（b3a E 组尾——
#   现行无来源留待手册原册，如实登记）。目录外=前置结构错误
#   InvalidFlowError（server 转调面同消息映射 422）。
#
# 【数值纪律】builtin 带锚值以 m³/d 声明（5184000.0/1000000.0/10.0）
#   经 parse(1.0,"m3/d",DimKey.FLOW) 因子换算（R3 零 m³/s 裸字面量；
#   真源区资格=check_magic_numbers WHITELIST_DECLARATION——主控裁定
#   B-3b-2 案甲；数值权威=b3a-research.md §二 A 组+§七追认 2026-09-26
#   用户「全部追认」，禁自创/改任何数值）。
#
# 【测试要求】tests/app/test_flows.py params_guard 段（face④/builtin
#   带镜像用例——批3b）。
# 【参照】b3b-brief.md 任务①；b3a-research.md §二 A/E 组；graph/cache.py
#   拆件先例；server calculation._validate_apply_params 转调面
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Final, final

from waterprint.app import discover_units
from waterprint.contracts.manifest import ParamSpec
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quality import INDICATORS
from waterprint.contracts.quantity import DimKey, parse

__all__ = ["ParamVerdict", "params_guard"]


@dataclass(frozen=True)
@final
class ParamVerdict:
    """单参数守护判定：键/原值/接受位/拒因/提示文案（清单式不拒整批）。"""

    key: str
    value: object
    accepted: bool
    reason: str | None
    warn: str | None = None  # 提示带文案——accepted=True 时不阻塞仅提示（批3b A-2/A-3）


# builtin kind 参数键面（R4）：graph.nodes 各 __init__ 校验语义镜像声明
# （junction/recycle_junction 零参数；grid 档位面 builtin 恒无——
# server units.py _BUILTIN_PARAM_DIMS 同款声明面先例）。
_BUILTIN_PARAM_KEYS: Final[Mapping[str, frozenset[str]]] = MappingProxyType({
    "municipal_input": frozenset(("q_avg_daily", "kz")) | frozenset(INDICATORS),
    "quality_edit": frozenset(INDICATORS),
    "junction": frozenset(),
    "recycle_junction": frozenset(),
})

# builtin q_avg_daily 带声明（批3b A-1~A-3——真源区声明面，每常量带出处；
# kz 不设带：b3a-research.md §二 E 组尾——变化系数带现行无来源，留待手册
# 原册复核批，如实登记不静默自定）。
# m³/d→m³/s 因子（R3：经 quantity parse 换算——零 m³/s 裸字面量）：
_FLOW_TO_M3D: Final[float] = parse(1.0, "m3/d", DimKey.FLOW)
# A-1 拒收上界=518.4 万 m³/d（建标 198-2022 Ⅰ类顶格类锚×全国最大白龙港
# 350 万×1.48 裕量圆整）→60 m³/s（乘因子二进制精确）：
_Q_REJECT_MAX_M3S: Final[float] = 5184000.0 * _FLOW_TO_M3D
# A-2 提示上沿=100 万 m³/d（超大型厂量级——白龙港级才进入）：
_Q_WARN_LARGE_M3S: Final[float] = 1000000.0 * _FLOW_TO_M3D
# A-3 提示下沿=10 m³/d（市政单体口径下限量级——建标 Ⅴ类下限 0.5 万
# m³/d 量级锚）：
_Q_WARN_SMALL_M3S: Final[float] = 10.0 * _FLOW_TO_M3D


def _guard_reason(
    key: object,
    value: object,
    unit_id: str,
    specs: Mapping[str, ParamSpec],
    known: frozenset[str],
) -> str | None:
    """四面判定单条拒因：①值有限数值 ②键已知 ③grid 档位 ④range 闭区间
    （首命中即返——face④ 批3b：audit §一「range 声明后无人执法」收口）。"""
    if not isinstance(key, str) or not key:
        return f"方案参数 {key!r} 非法（字段 ID: str）"
    if key not in known:
        return (
            f"方案参数 {key!r} 不在单元 {unit_id!r} 目录参数面"
            f"（合法 {sorted(known)}——ADR-005 grid 字段投影语义）"
        )
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not isfinite(value)
    ):
        return (
            f"方案参数 {key!r}={value!r} 非法（数值: int/float 有限值"
            "——bool/字符串/NaN 拒，ADR-005「值全 number」服务端口径）"
        )
    spec = specs.get(key)
    if (
        spec is not None
        and spec.grid is not None
        and float(value) not in {float(g) for g in spec.grid}
    ):
        return (
            f"方案参数 {key!r} 值 {value!r} 未命中 grid 档位 {list(spec.grid)}"
            "（枚举维——§12.4，与 core 装配期同口径前置）"
        )
    if (
        spec is not None
        and spec.range is not None
        and not spec.range[0] <= float(value) <= spec.range[1]
    ):
        return (
            f"方案参数 {key!r} 值 {value!r} 越带 [{spec.range[0]}, {spec.range[1]}]"
            "（闭区间执法——audit §一 range 声明后无人执法，b3a E 组第四面）"
        )
    return None


def _builtin_band_reason(
    catalog_key: str, key: str, value: float
) -> tuple[str | None, str | None]:
    """builtin 带（A-1~A-3）单条判定：拒因与提示文案对（q_avg_daily 专用）。

    返回 (reason, warn)：reason 非 None=拒收（accepted=False）；warn 非
    None=提示带（accepted=True 不阻塞仅提示——E2E-1 软提示面）。"""
    if catalog_key != "municipal_input" or key != "q_avg_daily":
        return None, None
    if value <= 0.0 or value > _Q_REJECT_MAX_M3S:
        return (
            f"进水流量 {value!r} m³/s 越市政厂硬界（(0, {_Q_REJECT_MAX_M3S}]——"
            "A-1/A-3：≤0 非法或超 518.4 万 m³/d 顶格类上界"
            "（b3a-research.md §二 A 组+§七追认 2026-09-26）",
            None,
        )
    if value < _Q_WARN_SMALL_M3S:
        return None, "流量过小——市政单体口径下限复核（<10 m³/d 量级，A-3 提示带）"
    if value > _Q_WARN_LARGE_M3S:
        return None, (
            "超大型厂——请复核规模口径（万 m³/d vs m³/s）与池数分格"
            "（>100 万 m³/d 量级，A-2 提示带）"
        )
    return None, None


def params_guard(
    project: ProjectFile, unit_id: str, params: Mapping[str, float]
) -> tuple[ParamVerdict, ...]:
    """guard 流：四面清单式逐条判定（server 版整批拒——本版不拒整批）。

    kind 通道：design.nodes[unit_id] 覆写含 kind 用 kind 查目录，否则
    unit_id 直查（32 包 manifest）；目录外=前置结构错误 InvalidFlowError
    （server 转调面同消息映射 422）。face④=spec.range 闭区间执法（批3b
    ——audit §一收口）；builtin 面 q_avg_daily 带=A-1~A-3（拒收/提示）。"""
    from waterprint.flows import (  # noqa: PLC0415  # 懒 import 破环（__init__ 装载期先 import 本件——export_batch_lib 先例）
        InvalidFlowError,
    )

    node = project.design.nodes.get(unit_id)
    if node is None:
        raise InvalidFlowError(
            f"方案目标单元 {unit_id!r} 不在项目 design.nodes（不可应用）"
        )
    kind = node.get("kind") if isinstance(node.get("kind"), str) else None
    catalog_key = kind if kind is not None else unit_id
    discovered = discover_units()
    if catalog_key in discovered:
        specs: Mapping[str, ParamSpec] = {
            spec.field_id: spec for spec in discovered[catalog_key][0].params}
        known = frozenset(specs)
    elif catalog_key in _BUILTIN_PARAM_KEYS:
        specs = {}
        known = _BUILTIN_PARAM_KEYS[catalog_key]
    else:
        raise InvalidFlowError(
            f"方案目标单元 {unit_id!r} 无单元目录声明（kind={catalog_key!r}"
            "——META1 目录外不可应用）"
        )
    verdicts: list[ParamVerdict] = []
    for key, value in params.items():
        reason = _guard_reason(key, value, unit_id, specs, known)
        warn: str | None = None
        if (
            reason is None
            and isinstance(value, int | float)
            and not isinstance(value, bool)
        ):
            reason, warn = _builtin_band_reason(catalog_key, key, float(value))
        verdicts.append(
            ParamVerdict(
                key=key if isinstance(key, str) else str(key),
                value=value,
                accepted=reason is None,
                reason=reason,
                warn=warn,
            )
        )
    return tuple(verdicts)
