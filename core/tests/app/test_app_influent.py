"""app_influent 镜像测试：全厂进水负荷供数投影（B4-2c，终裁定案 master-ruling D3）。

输入:  PlantResult 桩（逐工况快照——进水节点 outflows/outqualities）+ edges 桩
       + CoefficientsView 桩（factor.influent.s_per_d/factor.carbon.conv——单元
       测试注入值，不与 factors.yaml 数据耦合）+ summary 六指标面
输出:  influent_summary_of/_with_influent 行为断言（进水节点识别/sparse 键族
       三态缺席/逐工况同值/effluent TN 联动/纯函数双跑恒等/合并语义）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：B4-2c 终裁 D3——IF1 flow=q_avg_daily×s_per_d；IF2/IF3 负荷=
# 浓度×Q×conv（进水声明节点=无入边且 outflows 含 q_avg_daily）；
# IF4 effluent TN 负荷=summary[工况][TN]×Q×conv；sparse=换算键/
# 节点/浓度三态缺席各自跳键；逐工况同值（静态声明面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from waterprint.app_influent import _with_influent, influent_summary_of


class _StubCoefficients:
    """CoefficientsView 协议桩：注入换算键表，keys 前缀列举/get 失联抛错同真源。"""

    def __init__(self, values: dict[str, float]) -> None:
        self._values = values

    @property
    def data_version(self) -> str:
        return "stub"

    def get(self, key: str) -> Any:
        if key not in self._values:
            raise KeyError(f"失联键（领域异常语义）: {key}")
        return SimpleNamespace(
            value=self._values[key], unit="", source="", note="")

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(sorted(k for k in self._values if k.startswith(prefix)))


def _unit(unit_id: str, *, q: float | None, qualities: dict[str, float]) -> SimpleNamespace:
    outflows = {} if q is None else {f"{unit_id}.out.q_avg_daily": q}
    outqualities = {f"{unit_id}.out.{k}": v for k, v in qualities.items()}
    return SimpleNamespace(unit_id=unit_id, outflows=outflows,
                           outqualities=outqualities)


def _plant(conditions: dict[str, dict[str, SimpleNamespace]]) -> SimpleNamespace:
    return SimpleNamespace(conditions=conditions)


def _edge(dst: str) -> SimpleNamespace:
    return SimpleNamespace(dst=SimpleNamespace(unit_id=dst))


_CONV_LIB = _StubCoefficients({
    "factor.influent.s_per_d": 86400.0, "factor.carbon.conv_mg_l_kg_m3": 0.001})

_INLET = _unit("inlet", q=1.0, qualities={"TN": 50.0, "BOD5": 200.0})
_DOWNSTREAM = _unit("aao", q=None, qualities={"TN": 10.0})
_EDGES = (_edge("aao"),)  # aao 有入边；inlet 无入边


def test_inlet_identification_and_full_chain() -> None:
    """进水节点识别（无入边+q_avg_daily——有入边节点不识别）→IF1~IF4 全链。"""
    plant = _plant({"design": {"inlet": _INLET, "aao": _DOWNSTREAM}})
    view = influent_summary_of(
        plant, _EDGES, _CONV_LIB, {"design": {"TN": 10.0}})
    assert view["design"] == {
        "influent_flow_m3_d": 86400.0,        # 1 m3/s × 86400
        "influent_tn_load_kg_d": 4320.0,      # 50 × 86400 × 0.001
        "influent_bod5_load_kg_d": 17280.0,   # 200 × 86400 × 0.001
        "effluent_tn_load_kg_d": 864.0,       # 10 × 86400 × 0.001
    }


def test_sparse_missing_conc_bod5() -> None:
    """浓度缺席（矿井线无 BOD5 语义）→IF3 跳过，其余在场。"""
    inlet = _unit("inlet", q=1.0, qualities={"TN": 50.0})
    plant = _plant({"design": {"inlet": inlet, "aao": _DOWNSTREAM}})
    view = influent_summary_of(
        plant, _EDGES, _CONV_LIB, {"design": {"TN": 10.0}})
    assert "influent_bod5_load_kg_d" not in view["design"]
    assert set(view["design"]) == {
        "influent_flow_m3_d", "influent_tn_load_kg_d", "effluent_tn_load_kg_d"}


def test_sparse_missing_conversion_keys() -> None:
    """换算键缺席两态：s_per_d 缺→全链无键；conv 缺→仅 flow。"""
    only_flow_lib = _StubCoefficients({"factor.carbon.conv_mg_l_kg_m3": 0.001})
    plant = _plant({"design": {"inlet": _INLET}})
    assert influent_summary_of(plant, (), only_flow_lib, {}) == {"design": {}}
    no_conv_lib = _StubCoefficients({"factor.influent.s_per_d": 86400.0})
    view = influent_summary_of(plant, (), no_conv_lib, {"design": {"TN": 10.0}})
    assert set(view["design"]) == {"influent_flow_m3_d"}


def test_no_inlet_node_empty_mapping() -> None:
    """无进水声明节点（无 q_avg_daily 键）→空映射（sparse）。"""
    plant = _plant({"design": {"aao": _DOWNSTREAM}})
    assert influent_summary_of(
        plant, _EDGES, _CONV_LIB, {"design": {"TN": 10.0}}) == {"design": {}}


def test_per_condition_static_same_value() -> None:
    """逐工况同值：进水声明静态面——design/avg 两工况负荷相等。"""
    plant = _plant({
        "design": {"inlet": _INLET, "aao": _DOWNSTREAM},
        "avg": {"inlet": _INLET, "aao": _DOWNSTREAM}})
    view = influent_summary_of(
        plant, _EDGES, _CONV_LIB,
        {"design": {"TN": 10.0}, "avg": {"TN": 8.0}})
    assert (view["design"]["influent_tn_load_kg_d"]
            == view["avg"]["influent_tn_load_kg_d"])
    assert view["design"]["effluent_tn_load_kg_d"] != view["avg"][
        "effluent_tn_load_kg_d"]  # IF4 随 terminal 出水逐工况


def test_effluent_tn_linkage_sparse() -> None:
    """IF4 联动：summary 无 TN 键/工况缺席→effluent 负荷跳过。"""
    plant = _plant({"design": {"inlet": _INLET}, "avg": {"inlet": _INLET}})
    view = influent_summary_of(
        plant, (), _CONV_LIB, {"design": {}})  # design 无 TN；avg 工况缺席
    assert "effluent_tn_load_kg_d" not in view["design"]
    assert "effluent_tn_load_kg_d" not in view["avg"]


def test_pure_function_double_run_and_merge() -> None:
    """纯函数双跑恒等+只读（不 mutate plant/effluent 面）；_with_influent
    同工况 update 注入、缺工况不造键。"""
    plant = _plant({"design": {"inlet": _INLET}})
    effluent = {"design": {"TN": 10.0, "BOD5": 5.0}}
    effluent_frozen = {"design": dict(effluent["design"])}
    first = influent_summary_of(plant, (), _CONV_LIB, effluent)
    second = influent_summary_of(plant, (), _CONV_LIB, effluent)
    assert first == second
    assert effluent == effluent_frozen  # 只读实证
    base = {"design": {"TN": 10.0}, "other": {"SS": 1.0}}
    merged = _with_influent(dict(base), first)
    assert merged["design"]["influent_flow_m3_d"] == 86400.0
    assert merged["design"]["TN"] == 10.0  # base 键族优先并存
    assert "influent_flow_m3_d" not in merged["other"]  # 缺工况不注入
