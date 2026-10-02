"""conveyance golden 端到端（首个集配水 golden 图——UF-61④ 缺口闭）。

输入:  golden_data/municipal_34760_conveyance/{input_project.json,
       expected_summary.json, notes.md}
输出:  基线帧对照（effluent 5 帧逐项+design_dims 22 单元逐键+serialize
       双锚+m3 双断言）+ offline 行为锚三面（a 分化/b 位串恒等/c summary
       零漂移）+汇流分流守恒锚+上下游浓度位串透传锚+拒检面锚
       （conv-golden 批 2026-10-02；offline 帧=conveyance 引擎计算链
       首个行为载体——修复面 executor_assembly.forward_stocks 检修
       饥饿边零股承接，镜像锚=tests/graph/test_executor_starved_edge.py
       饥饿边三用例）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格：期望值两类来源严格分开（§16 A9——notes.md §1 全文）：
#   直引面=基案 municipal_34760 期望值（零去除穿流+流量恒等 UF-61①
#   数学性质——生成脚本逐键 struct.pack 对拍 0 diff 实证）；
#   实跑面=本案例 HEAD=e0f0a94bf 实跑录制（conveyance 四单元 dims/
#   generated serialize 双锚/m3_deferred）。实现者零自编数字。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (
            Path(__file__).parent / "golden_data" / "municipal_34760_conveyance"
            / "expected_summary.json"
        ).is_file(),
        reason="golden 数据未整理（conv-golden 批：conveyance 集配水案例）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_REPO_PRICES = Path(__file__).resolve().parents[3] / "data" / "unit_prices"
_TERMINAL = "municipal_bashi_jiliangcao"
# 受检三配水类单元（jishuijing 不勾——condition_mappings=() 拒检面）
_CHECKED = (
    "conveyance_peishuijing",
    "conveyance_jipeishuijing",
    "conveyance_peishuiqu",
)
# 六指标（浓度面——穿流/位串透传锚的逐指标迭代面）
_INDICATORS = ("BOD5", "CODCR", "SS", "NH3N", "TN", "TP")


def _bits(value: float) -> bytes:
    """IEEE 双精度位串（位串级恒等断言的判别面——cond2 T4 先例）。"""
    return struct.pack("<d", value)


def _m3_real_values(plant: Any, expected: dict[str, Any]) -> None:
    """M3 面真值：概算总数+全厂总泥量实跑对照（基案 e2e 同款双断言）。

    estimate_total=全图（23 节点）design 档工程量→概算——takeoff field-wide
    v_concrete 行自动计入 conveyance peishuijing/jishuijing/jipeishuijing
    三口新工程量（peishuiqu 无该键不计入）→值≠基案（实跑录制面）。
    total_sludge=hebing ds_total（干基 kg/d）；湿基 q_total 以 design_dims
    ["sludge_hebing"]["q_total"] 直引锚承载双断言。"""
    from waterprint.cost.estimate import build_estimate, load_fee_rules
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import takeoff_quantities

    book = load_prices(_REPO_PRICES)
    fees = load_fee_rules(_REPO_PRICES / "field_mapping.yaml", book)
    sheet = build_estimate(
        takeoff_quantities(plant, "design", price_book=book), book, fees)
    assert (sheet.subtotal + sheet.reserve_subtotal
            + sum(line.amount for line in sheet.tax)) == sheet.grand_total
    m3 = expected["m3_deferred"]
    for key in ("estimate_total", "total_sludge"):
        assert set(m3[key]) == {"value", "source", "abs", "rel"}, key
    estimate = m3["estimate_total"]
    assert sheet.grand_total == pytest.approx(
        estimate["value"], rel=estimate["rel"], abs=estimate["abs"]
    ), "m3_deferred.estimate_total（23 节点 design 档——conveyance 新工程量计入）"
    sludge = m3["total_sludge"]
    hebing = plant.conditions["design"]["sludge_hebing"].dims
    assert hebing["ds_total"] == pytest.approx(
        sludge["value"], rel=sludge["rel"], abs=sludge["abs"]
    ), "m3_deferred.total_sludge（hebing ds_total 干基 kg/d 主口径）"
    wet = expected["design_dims"]["sludge_hebing"]["q_total"]
    assert hebing["q_total"] == pytest.approx(
        wet["value"], rel=wet["rel"], abs=wet["abs"]
    ), "hebing q_total（湿基 m³/d——m3 双断言第二锚）"


def _manifest_defaults(unit_id: str) -> dict[str, float]:
    """manifest 参数默认值单源读取（ceil 档步长锚不写测试字面量）。"""
    from waterprint.units_lib import discover_units

    return {spec.field_id: spec.default
            for spec in discover_units()[unit_id][0].params}


def _assert_effluent(plant: Any, expected: dict[str, Any], keys: list[str]) -> None:
    """② 逐工况逐项终水对照（双容差按 expected 内标注——不放宽）。

    键集钳制：expected 工况块恰等 5 工况键集，防删块静默绿；B4-2a
    聚合键（power_*/dose_*）走 summary 双路由（基案同款判别）。"""
    assert set(expected["effluent"]) == set(keys)
    for condition_key, fields in expected["effluent"].items():
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            quality_key = f"{_TERMINAL}.out.{indicator}"
            actual = (
                snapshot.outqualities[quality_key]
                if quality_key in snapshot.outqualities
                else plant.summary[condition_key][indicator]
            )
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"


def _assert_design_dims(
    plant: Any, expected: dict[str, Any], project: Any
) -> None:
    """③ design 档主尺寸逐键对照（22 单元=19 基案节点+conveyance 四节点减
    inlet；单元覆盖钳制：恰等 nodes−inlet，防删块静默绿）。"""
    assert set(expected["design_dims"]) == set(project.design.nodes) - {"inlet"}
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"


def _assert_target_differentiation(
    plant: Any, target: str, anchors: tuple[tuple[str, str, float | None], ...],
    diff_keys: tuple[str, ...], same_keys: tuple[str, ...],
) -> None:
    """offline a 面前半：目标单元 n 派生 dims 分化（公式语义精确锚）。

    linear=线性入式键（q_design/n 族）恰 ×2；sqrt=面积→直径键 ×√2；
    power=幂律键（PQ-F4 堰顶水头——指数=表串原文 0.66666667 近似 2/3）。
    分化键集恰等（分化面=且仅为 n 入式键族——方向+全集锚）；非入式键
    （q_design/参数系数族）IEEE 位串恒等（分化不外渗）。"""
    off_key = f"design_offline_{target}"
    design = plant.conditions["design"][target].dims
    offline = plant.conditions[off_key][target].dims
    assert set(offline) == set(design), f"{target} design↔offline dims 键集漂移"
    for key, kind, ratio in anchors:
        if kind == "linear":
            assert offline[key] == pytest.approx(2.0 * design[key], rel=1e-12), (
                target, key)
        elif kind == "sqrt":
            assert offline[key] == pytest.approx(
                math.sqrt(2.0) * design[key], rel=1e-12), (target, key)
        else:
            assert offline[key] == pytest.approx(
                design[key] * 2.0 ** ratio, rel=1e-12), (target, key)
    differentiated = {key for key in design
                      if _bits(design[key]) != _bits(offline[key])}
    assert differentiated == set(diff_keys), (target, differentiated)
    for key in same_keys:
        assert _bits(offline[key]) == _bits(design[key]), (target, key)


def _assert_offline_frame(plant: Any, target: str) -> None:
    """offline b/c 面：其余全部单元 dims 与 design 帧位串恒等+键集对称
    （inlet 恒空显式——ADR-007「该单元 n−1、其余全池」）；summary 面零
    漂移（逐键==——UF-61① 性质在 conveyance 面复锚）。"""
    off_key = f"design_offline_{target}"
    for unit_id, snapshot in plant.conditions["design"].items():
        if unit_id == target:
            continue
        other = plant.conditions[off_key][unit_id].dims
        assert set(other) == set(snapshot.dims), f"{off_key}/{unit_id} 键集漂移"
        if unit_id == "inlet":
            assert other == snapshot.dims == {}, "inlet dims 两帧恒等且恒空"
            continue
        for key, value in snapshot.dims.items():
            assert isinstance(value, float) and isinstance(other[key], float), (
                off_key, unit_id, key)
            assert not math.isnan(value) and not math.isnan(other[key]), (
                off_key, unit_id, key)
            assert _bits(other[key]) == _bits(value), f"{off_key}/{unit_id}.{key} 位串漂移"
    offline_summary = plant.summary[off_key]
    design_summary = plant.summary["design"]
    assert set(offline_summary) == set(design_summary), f"{off_key} summary 键集漂移"
    for key, value in design_summary.items():
        other = offline_summary[key]
        assert isinstance(value, float) and isinstance(other, float), (
            off_key, key)
        assert not math.isnan(value) and not math.isnan(other), (off_key, key)
        assert _bits(other) == _bits(value), f"{off_key}.summary.{key} 位串漂移"


def _assert_offline_anchors(plant: Any) -> None:
    """offline 行为锚（本批核心）——三 offline 帧 a/b/c 三面+PJ 复合锚。

    分化键集=实跑分化面全量（peishuijing 8 键/peishuiqu 4 键/
    jipeishuijing 2 键——n 入式族精确清点）；PJ 出流口径径 ceil 档语义
    （步长=manifest 默认单源读）+v_act/h_head 复合比例锚（v_act=q_each/
    a_act——a_act 随 d 档变；h_head=v_act²/(2gμ²) 平方传递）。"""
    _assert_target_differentiation(
        plant, "conveyance_peishuijing",
        anchors=(("q_each", "linear", None), ("a_out", "linear", None),
                 ("q_series", "linear", None), ("d_raw", "sqrt", None)),
        diff_keys=("a_act", "a_out", "d", "d_raw", "h_head", "q_each",
                   "q_series", "v_act"),
        same_keys=("a_well", "a_well_act", "d_well", "d_well_raw",
                   "h_total", "v_concrete"),
    )
    _assert_target_differentiation(
        plant, "conveyance_jipeishuijing",
        anchors=(("q_each", "linear", None), ("q_series", "linear", None)),
        diff_keys=("q_each", "q_series"),
        same_keys=("a_act", "a_well", "d", "d_raw", "h_total", "t_act",
                   "v_concrete", "v_well"),
    )
    _assert_target_differentiation(
        plant, "conveyance_peishuiqu",
        anchors=(("q_each", "linear", None), ("q_series", "linear", None),
                 ("v_end", "linear", None), ("h_weir", "power", 0.66666667)),
        diff_keys=("h_weir", "q_each", "q_series", "v_end"),
        same_keys=("a_channel", "h_total", "h_water"),
    )
    for target in _CHECKED:
        _assert_offline_frame(plant, target)
    # PJ ceil 档+方向+复合比例锚
    step = _manifest_defaults("conveyance_peishuijing")["length_disc_step"]
    design = plant.conditions["design"]["conveyance_peishuijing"].dims
    offline = plant.conditions["design_offline_conveyance_peishuijing"][
        "conveyance_peishuijing"].dims
    assert design["d"] == math.ceil(design["d_raw"] / step) * step
    assert offline["d"] == math.ceil(offline["d_raw"] / step) * step
    assert offline["d"] > design["d"]  # 单口加大方向锚
    assert offline["v_act"] == pytest.approx(
        2.0 * design["v_act"] * design["a_act"] / offline["a_act"], rel=1e-12)
    assert offline["h_head"] == pytest.approx(
        design["h_head"] * (offline["v_act"] / design["v_act"]) ** 2, rel=1e-12)


def _assert_conservation(plant: Any) -> None:
    """汇流/分流守恒锚：三配水类单元均匀分流（q/2 半除精确，位串级）+
    Σ口==入流+jishuijing 汇流守恒；offline 饥饿边帧=在运口全流量+
    零股守恒（executor_assembly.forward_stocks 承接口径的行为锚）。"""
    def q(cond: str, unit: str, port: str) -> float:
        return plant.conditions[cond][unit].outflows[f"{unit}.{port}.q_avg_daily"]

    design = "design"
    for unit, upstream in (
        ("conveyance_peishuijing", "municipal_xigeshan"),
        ("conveyance_peishuiqu", "municipal_chuchenchi"),
        ("conveyance_jipeishuijing", "municipal_erchunchi"),
    ):
        inflow = plant.conditions[design][upstream].outflows[
            f"{upstream}.out.q_avg_daily"]
        o1, o2 = q(design, unit, "out_1"), q(design, unit, "out_2")
        half = _bits(inflow / 2)
        assert _bits(o1) == _bits(o2) == half, (unit, "分流均匀（位串级）")
        assert _bits(o1 + o2) == _bits(inflow), (
            unit, "Σ口==入流（q/2+q/2==q 精确——位串级）")
    q_xige = plant.conditions[design]["municipal_xigeshan"].outflows[
        "municipal_xigeshan.out.q_avg_daily"]
    assert _bits(q(design, "conveyance_jishuijing", "out")) == _bits(q_xige), "汇流守恒"
    off = "design_offline_conveyance_peishuijing"
    assert _bits(q(off, "conveyance_peishuijing", "out_1")) == _bits(q_xige), "在运口全流量"
    assert _bits(q(off, "conveyance_jishuijing", "out")) == _bits(q_xige), "饥饿边零股守恒"


def _assert_passthrough(plant: Any) -> None:
    """上下游浓度恒等透传锚（位串级——六指标×穿流链四段+offline 零股
    不稀释）：xigeshan→peishuijing.out_1/out_2→jishuijing.out 整簇；
    chuchenchi→peishuiqu.out_1；erchunchi→jipeishuijing.out_1。"""
    design = "design"
    off = "design_offline_conveyance_peishuijing"
    for indicator in _INDICATORS:
        xige = plant.conditions[design]["municipal_xigeshan"].outqualities[
            f"municipal_xigeshan.out.{indicator}"]
        for unit, port in (("conveyance_peishuijing", "out_1"),
                           ("conveyance_peishuijing", "out_2"),
                           ("conveyance_jishuijing", "out")):
            value = plant.conditions[design][unit].outqualities[
                f"{unit}.{port}.{indicator}"]
            assert _bits(value) == _bits(xige), (unit, port, indicator)
        chuchen = plant.conditions[design]["municipal_chuchenchi"].outqualities[
            f"municipal_chuchenchi.out.{indicator}"]
        assert _bits(
            plant.conditions[design]["conveyance_peishuiqu"].outqualities[
                f"conveyance_peishuiqu.out_1.{indicator}"]
        ) == _bits(chuchen), ("conveyance_peishuiqu", indicator)
        erchun = plant.conditions[design]["municipal_erchunchi"].outqualities[
            f"municipal_erchunchi.out.{indicator}"]
        assert _bits(
            plant.conditions[design]["conveyance_jipeishuijing"].outqualities[
                f"conveyance_jipeishuijing.out_1.{indicator}"]
        ) == _bits(erchun), ("conveyance_jipeishuijing", indicator)
        assert _bits(
            plant.conditions[off]["conveyance_jishuijing"].outqualities[
                f"conveyance_jishuijing.out.{indicator}"]
        ) == _bits(xige), ("offline 零股稀释", indicator)


def test_municipal_conveyance_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：基线帧对照+offline 行为锚+守恒锚+serialize 双锚+m3 双断言。"""
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set
    from waterprint.contracts.result_schema import serialize
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case_dir = golden_data_dir / "municipal_34760_conveyance"
    project = load_project(case_dir / "input_project.json")
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )
    assert project.design.checked_units == expected["checked_units"]  # 双录面
    conditions = build_condition_set(expected["checked_units"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == expected["condition_keys"]  # ⑤ 2+k 索引（k=3）
    assert len(keys) == 2 + len(expected["checked_units"]) == 5

    lib = load_coefficients(_REPO_DATA)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib, price_book={}, trace_sink=None, engine_params={},
    )
    plant = run_full_calc(project, conditions, env).plant  # ① 正门实跑
    assert set(plant.conditions) == set(keys)  # 全 5 工况各出整图结果
    assert plant.repro.design_hash == project.metadata.content_hash  # 绑定输入
    assert set(plant.summary) == set(keys)  # 全工况注入口径

    _assert_effluent(plant, expected, keys)  # ②
    _assert_design_dims(plant, expected, project)  # ③
    _m3_real_values(plant, expected)  # M3 面（conveyance 新工程量计入）
    _assert_offline_anchors(plant)  # offline a/b/c 三面（本批核心）
    _assert_conservation(plant)  # 汇流/分流守恒
    _assert_passthrough(plant)  # 浓度位串透传

    first = serialize(run_full_calc(project, conditions, env).plant)  # ⑥
    second = serialize(run_full_calc(project, conditions, env).plant)
    assert first == second  # 双跑字节同（确定性 R3）
    assert len(first) == expected["generated"]["serialize_bytes"]
    assert hashlib.sha256(first).hexdigest()[:16] == (
        expected["generated"]["serialize_sha256_head"]
    )


def test_conveyance_jishuijing_checked_rejected(golden_data_dir: Path) -> None:
    """拒检面锚：checked_units 含 jishuijing → InvalidAssemblyError（装配期
    拒——condition_mappings=() 空映射锁定面，cond3 批明示不映射的诚实行为）。

    jishuijing=单井容蓄无并联系列数（非不合格设计面——D4 语义=该单元
    无检修降级映射可声明）；基案三受检单元追加 jishuijing 即拒（混合
    集形态：任一空映射单元在列即整体拒）。"""
    from waterprint.app import InvalidAssemblyError, assemble, load_project
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case_dir = golden_data_dir / "municipal_34760_conveyance"
    project = load_project(case_dir / "input_project.json")
    poisoned = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "checked_units": [
                        *project.design.checked_units, "conveyance_jishuijing",
                    ]
                }
            )
        }
    )
    env = RunEnv(
        engine_version="waterprint-server 0.1.0",
        data_version="coefficients@1.8.0+unit_prices@1.2.0",
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={}, trace_sink=None, engine_params={},
    )
    with pytest.raises(InvalidAssemblyError, match="须声明检修降级映射"):
        assemble(poisoned, env)
