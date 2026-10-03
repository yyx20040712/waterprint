"""诊断契约序列化内核（trust.py 拆件承载面——500 行墙前置纯搬迁）。

输入:  DiagnosticsReport 及节点数据类（trust.py 类型面）+ 诊断 JSON 字节
输出:  serialize_diag / deserialize_diag（trust.py 同名再导出——消费方
       import 面零变化；serde 段逐行同文自 trust.py 迁入，零行为变更）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（kbflag 批 2026-10-03 serde 拆件——R2/R3/R4 规格随内核自
# trust.py 迁入，serde 内核为规格主体归属；镜像测试 tests/contracts/
# test_trust.py；拆件恒等钉 tests/contracts/test_trust_serde.py）
#
# 【公开接口】
#   serialize_diag(report) -> bytes     确定性序列化正门
#   deserialize_diag(data: bytes) -> DiagnosticsReport  严格反序列化正门
#   （两者经 trust.py 尾段同名再导出——消费方正门恒为 trust）
#
# 【行为规格】（自 trust.py 原文迁入——语义零变更）
#   R2 序列化确定性：键递归排序、round(x,10)、紧凑分隔符、UTF-8、
#      ensure_ascii=False——同结果双跑字节级相同（R3 同源纪律）。
#   R3 非有限值拒绝（GR-02）：serialize_diag/deserialize_diag 数值通
#      路统一守卫（NaN/±Inf 拒，消息含位置）；巨 int 溢出同收编。
#   R4 严格键集（T3A-03/T3G-01 同精神）：deserialize 各节点缺键拒/
#      未知键拒（消息含键名）；序列化嵌套节点经 dataclasses.fields
#      恒发全键（根树手工五键字面与 _ROOT_KEYS 两处同步——扩字段
#      漂移面由 R4 未知键拒兜底）。
#
# 【装载序契约】本件与 trust.py 互引（contracts 包内互引——trust→
#   result_schema 先例同构）：两侧 import 均置文件尾段（定义先行），
#   trust 首导/trust_serde 直连首导两种装载序均闭环；消费方正门
#   恒为 waterprint.contracts.trust。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 round(x,10) 的 10。
#
# 【测试要求】往返无损、确定性（双跑字节同）、未知/缺失键拒、
#   非有限值拒、iterations 域守卫、空容器恒发（空 tuple 合法序列化
#   为 []——无回路图 convergence 空合法）。
#
# 【参照】contracts/trust.py（数据面+R1/R5/R6 条款归属）；result_
#   schema.py（确定性纪律母本）；conventions §11 GR-02
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from waterprint.contracts.result_schema import ReproTriple

_ROUND_DIGITS: int = 10
_JSON_KWARGS: dict[str, Any] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}
# 各节点合法键集（deserialize 严格键集判据——与 dataclass 字段一一对应）
_ROOT_KEYS: frozenset[str] = frozenset(
    {"convergence", "loop_params", "mass_balance", "effluent", "repro"}
)
_LOOP_RUN_KEYS: frozenset[str] = frozenset(
    {"condition_key", "loop_nodes", "iterations", "final_residual"}
)
_CLOSURE_LINE_KEYS: frozenset[str] = frozenset(
    {"fluid", "q_sources_total", "q_sinks_total", "closure_rel"}
)
_UNIT_IMBALANCE_KEYS: frozenset[str] = frozenset(
    {"unit_id", "fluid", "q_in", "q_out", "delta_rel"}
)
_FLOW_CLOSURE_KEYS: frozenset[str] = frozenset(
    {"condition_key", "lines", "unit_imbalances"}
)
_INDICATOR_MARGIN_KEYS: frozenset[str] = frozenset(
    {"condition_key", "standard_id", "indicator", "value", "limit", "margin"}
)
_FLUIDS: frozenset[str] = frozenset({"WATER", "SLUDGE"})


def _finite_rounded(value: int | float, path: str) -> float:
    """数值守卫：巨 int 溢出与非有限均拒+round(x,10)（R3；result_schema 同款）。"""
    try:
        number = float(value)
    except OverflowError as exc:
        raise InvalidDiagnosticsError(
            f"诊断含超浮点域整数：{path} 处原值类型 {type(value).__name__}"
            "（R3/GR-02——带病诊断禁止序列化）"
        ) from exc
    if not isfinite(number):
        raise InvalidDiagnosticsError(
            f"诊断含非有限值（NaN/±Inf）：{path} 处 {number!r}"
            "（R3/GR-02——带病诊断禁止序列化）"
        )
    return round(number, _ROUND_DIGITS)


def _to_json(value: Any, path: str) -> Any:
    """值 → 确定性 JSON 树（result_schema 同款：数值定点/键限字符串/递归）。"""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int | float):
        return _finite_rounded(value, path)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_json(getattr(value, field.name), f"{path}.{field.name}")
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {
            key if isinstance(key, str) else _str_key(key, path): _to_json(
                item, f"{path}.{key}"
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence):
        return [
            _to_json(item, f"{path}[{index}]") for index, item in enumerate(value)
        ]
    raise InvalidDiagnosticsError(
        f"诊断含不可序列化类型 {type(value).__name__}：{path}（R2 确定性面）"
    )


def _str_key(key: Any, path: str) -> str:
    """JSON 对象键守卫：仅字符串键（R2 同款）。"""
    if not isinstance(key, str):
        raise InvalidDiagnosticsError(
            f"诊断 Mapping 键必须为字符串：{path} 处 {key!r}"
        )
    return key


def serialize_diag(report: DiagnosticsReport) -> bytes:
    """确定性序列化正门：键递归排序、round(x,10)、紧凑分隔符、UTF-8（R2）。"""
    tree: dict[str, Any] = {
        "convergence": _to_json(report.convergence, "convergence"),
        "loop_params": _to_json(report.loop_params, "loop_params"),
        "mass_balance": _to_json(report.mass_balance, "mass_balance"),
        "effluent": _to_json(report.effluent, "effluent"),
        "repro": _to_json(report.repro, "repro"),
    }
    return json.dumps(tree, **_JSON_KWARGS).encode("utf-8")


def _reject_constant(token: str) -> float:
    """JSON 的 NaN/Infinity 字面量 → 拒（R3）。"""
    raise ValueError(f"非有限 JSON 字面量：{token}")


def _parse_float(token: str) -> float:
    """浮点字面量守卫：1e999 等溢出为 inf 同拒（R3）。"""
    value = float(token)
    if not isfinite(value):
        raise ValueError(f"非有限浮点字面量：{token}")
    return value


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    """结构守卫：对象节点。"""
    if not isinstance(value, dict):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为对象，得到 {type(value).__name__}")
    return value


def _require_str(value: Any, path: str) -> str:
    """结构守卫：字符串叶子。"""
    if not isinstance(value, str):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为字符串，得到 {type(value).__name__}")
    return value


def _require_number(value: Any, path: str) -> float:
    """结构守卫：数值叶子（再过有限性守卫，R3）。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为数值，得到 {value!r}")
    return _finite_rounded(value, path)


def _require_str_list(value: Any, path: str) -> list[Any]:
    """结构守卫：数组节点（元素由上层重建）。"""
    if not isinstance(value, list):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为数组，得到 {type(value).__name__}")
    return value


def _reject_keys(
    raw: Mapping[str, Any], required: frozenset[str], path: str
) -> None:
    """结构守卫：缺键拒+未知键拒（R4——消息含键名）。"""
    missing = sorted(key for key in required if key not in raw)
    if missing:
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 缺失必需键 {missing}"
            "（R4——serialize 恒发全键，缺失即数据源缺陷）"
        )
    unknown = sorted(set(raw) - required)
    if unknown:
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 含未知键 {unknown}（合法键 {sorted(required)}）"
            "（R4——未知键拒）"
        )


def _require_fluid(value: Any, path: str) -> str:
    """fluid 叶子守卫：WATER/SLUDGE 枚举域。"""
    text = _require_str(value, path)
    if text not in _FLUIDS:
        raise InvalidDiagnosticsError(
            f"fluid 非法：{text!r}（合法 {sorted(_FLUIDS)}）"
        )
    return text


def _require_iterations(value: Any, path: str) -> int:
    """iterations 叶子守卫：int 直收；float 须整值归一 int（serialize int
    归一纪律——result_schema R3 同款往返前提）；bool 拒。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为整数，得到 {value!r}"
        )
    number = _finite_rounded(value, path)
    if number != int(number):
        raise InvalidDiagnosticsError(
            f"诊断数据结构非法：{path} 应为整数值，得到 {value!r}"
        )
    return int(number)


def _loop_run_of(value: Any, path: str) -> LoopRunStats:
    """LoopRunStats 节点重建（iterations 域守卫复用构造面）。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, _LOOP_RUN_KEYS, path)
    return LoopRunStats(
        condition_key=_require_str(raw["condition_key"], f"{path}.condition_key"),
        loop_nodes=tuple(
            _require_str(item, f"{path}.loop_nodes[{index}]")
            for index, item in enumerate(
                _require_str_list(raw["loop_nodes"], f"{path}.loop_nodes")
            )
        ),
        iterations=_require_iterations(raw["iterations"], f"{path}.iterations"),
        final_residual=_require_number(raw["final_residual"], f"{path}.final_residual"),
    )


def _closure_line_of(value: Any, path: str) -> ClosureLine:
    """ClosureLine 节点重建。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, _CLOSURE_LINE_KEYS, path)
    return ClosureLine(
        fluid=_require_fluid(raw["fluid"], f"{path}.fluid"),
        q_sources_total=_require_number(
            raw["q_sources_total"], f"{path}.q_sources_total"
        ),
        q_sinks_total=_require_number(raw["q_sinks_total"], f"{path}.q_sinks_total"),
        closure_rel=_require_number(raw["closure_rel"], f"{path}.closure_rel"),
    )


def _unit_imbalance_of(value: Any, path: str) -> UnitImbalance:
    """UnitImbalance 节点重建。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, _UNIT_IMBALANCE_KEYS, path)
    return UnitImbalance(
        unit_id=_require_str(raw["unit_id"], f"{path}.unit_id"),
        fluid=_require_fluid(raw["fluid"], f"{path}.fluid"),
        q_in=_require_number(raw["q_in"], f"{path}.q_in"),
        q_out=_require_number(raw["q_out"], f"{path}.q_out"),
        delta_rel=_require_number(raw["delta_rel"], f"{path}.delta_rel"),
    )


def _flow_closure_of(value: Any, path: str) -> FlowClosure:
    """FlowClosure 节点重建。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, _FLOW_CLOSURE_KEYS, path)
    return FlowClosure(
        condition_key=_require_str(raw["condition_key"], f"{path}.condition_key"),
        lines=tuple(
            _closure_line_of(item, f"{path}.lines[{index}]")
            for index, item in enumerate(
                _require_str_list(raw["lines"], f"{path}.lines")
            )
        ),
        unit_imbalances=tuple(
            _unit_imbalance_of(item, f"{path}.unit_imbalances[{index}]")
            for index, item in enumerate(
                _require_str_list(raw["unit_imbalances"], f"{path}.unit_imbalances")
            )
        ),
    )


def _indicator_margin_of(value: Any, path: str) -> IndicatorMargin:
    """IndicatorMargin 节点重建。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, _INDICATOR_MARGIN_KEYS, path)
    return IndicatorMargin(
        condition_key=_require_str(raw["condition_key"], f"{path}.condition_key"),
        standard_id=_require_str(raw["standard_id"], f"{path}.standard_id"),
        indicator=_require_str(raw["indicator"], f"{path}.indicator"),
        value=_require_number(raw["value"], f"{path}.value"),
        limit=_require_number(raw["limit"], f"{path}.limit"),
        margin=_require_number(raw["margin"], f"{path}.margin"),
    )


def _repro_of(value: Any, path: str) -> ReproTriple:
    """repro 节点重建（复用 result_schema.ReproTriple 三键纪律）。"""
    raw = _require_mapping(value, path)
    _reject_keys(raw, frozenset({"design_hash", "engine_version", "data_version"}), path)
    return ReproTriple(
        design_hash=_require_str(raw["design_hash"], f"{path}.design_hash"),
        engine_version=_require_str(raw["engine_version"], f"{path}.engine_version"),
        data_version=_require_str(raw["data_version"], f"{path}.data_version"),
    )


def deserialize_diag(data: bytes) -> DiagnosticsReport:
    """严格反序列化正门：UTF-8+JSON+结构/有限性全量守卫（R3/R4）。"""
    try:
        tree = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InvalidDiagnosticsError(f"诊断数据非法 JSON（UTF-8/NaN 面）：{exc}") from exc
    root = _require_mapping(tree, "$")
    _reject_keys(root, _ROOT_KEYS, "$")
    loop_params_raw = _require_mapping(root["loop_params"], "$.loop_params")
    return DiagnosticsReport(
        convergence=tuple(
            _loop_run_of(item, f"$.convergence[{index}]")
            for index, item in enumerate(
                _require_str_list(root["convergence"], "$.convergence")
            )
        ),
        loop_params={
            key: _require_number(item, f"$.loop_params.{key}")
            for key, item in loop_params_raw.items()
        },
        mass_balance=tuple(
            _flow_closure_of(item, f"$.mass_balance[{index}]")
            for index, item in enumerate(
                _require_str_list(root["mass_balance"], "$.mass_balance")
            )
        ),
        effluent=tuple(
            _indicator_margin_of(item, f"$.effluent[{index}]")
            for index, item in enumerate(
                _require_str_list(root["effluent"], "$.effluent")
            )
        ),
        repro=_repro_of(root["repro"], "$.repro"),
    )


# trust 类型面 import（装载序契约双尾形态：本件函数体对 trust 数据类/
# 异常类的引用经调用期名字解析——定义先于 import 使 trust_serde 直连
# 首导亦不撞部分初始化窗口；与 trust.py 尾段再导出互为对向尾段边）。
from waterprint.contracts.trust import (  # noqa: E402
    ClosureLine,
    DiagnosticsReport,
    FlowClosure,
    IndicatorMargin,
    InvalidDiagnosticsError,
    LoopRunStats,
    UnitImbalance,
)
