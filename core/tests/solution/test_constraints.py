"""constraints 镜像测试：布尔约束过滤（pass_matrix 完整性/UI 覆盖/DSL 拒绝）。

输入:  waterprint.solution.constraints 公开符号 + 内存 DataFrame
输出:  过滤语义断言（无解诊断的输入保证）
"""

from __future__ import annotations

import importlib

import pytest

pd = pytest.importorskip("pandas")

_mod = importlib.import_module("waterprint.solution.constraints")
apply_constraints = getattr(_mod, "apply_constraints", None)
Constraint = getattr(_mod, "Constraint", None)

pytestmark = [
    pytest.mark.skipif(
        None in (apply_constraints, Constraint),
        reason="实现未就绪：waterprint.solution.constraints（M1）",
    ),
]


def _df() -> "pd.DataFrame":
    return pd.DataFrame({"pool_length": [8.0, 12.0, 20.0], "id": [0, 1, 2]})


def test_feasible_subset_and_pass_matrix() -> None:
    """R2：可行子集与逐约束通过矩阵同时产出（全 False 也要有矩阵）。"""
    constraint = Constraint(
        key="kb.demo.len_max", expression="pool_length <= 15", source="kb.demo"
    )
    result = apply_constraints(_df(), [constraint])
    assert list(result.feasible) == [0, 1]
    assert len(result.pass_matrix) == 3


def test_all_false_matrix_survives_for_diagnosis() -> None:
    """R2：无解时矩阵完整（诊断依赖——禁止只返回空集丢信息）。"""
    impossible = Constraint(
        key="kb.demo.impossible", expression="pool_length > 999", source="kb.demo"
    )
    result = apply_constraints(_df(), [impossible])
    assert list(result.feasible) == []
    assert result.pass_matrix["pool_length > 999"].tolist() == [False, False, False]


def test_unknown_field_in_expression_rejected() -> None:
    """R1：DSL 白名单——未知字段表达式拒绝（安全与可序列化）。"""
    bad = Constraint(
        key="kb.demo.bad", expression="no_such_field <= 1", source="kb.demo"
    )
    with pytest.raises(Exception, match=".+"):
        apply_constraints(_df(), [bad])


# ══ 批2a 约束带裕度域（test_margins_draft 转正——[HUMAN-LOCK]
#     2026-09-26 用户「全部追认」授权落地 b2a 呈批件）══

from math import isnan  # noqa: E402 （域内追加——NaN 断言用）

band_margin_column = getattr(_mod, "band_margin_column", None)
band_of = getattr(_mod, "band_of", None)


def _frame(rows: list[dict[str, float]]) -> "pd.DataFrame":
    return pd.DataFrame(rows)


# ── band_of：带形解析（DSL 家园面）────────────────────────────────


def test_band_of_two_sided_same_field() -> None:
    """双侧同字段带（>= 与 <= 各一）→ (field, low, high)；子句序无关。"""
    assert band_of("v >= 7.0 and v <= 10.0") == ("v", 7.0, 10.0)  # type: ignore[misc]
    assert band_of("v <= 10.0 and v >= 7.0") == ("v", 7.0, 10.0)  # type: ignore[misc]


def test_band_of_strict_ops_accepted() -> None:
    """严格不等号同构带（>/<）——带缘测度零，距离公式同形。"""
    assert band_of("v > 7.0 and v < 10.0") == ("v", 7.0, 10.0)  # type: ignore[misc]


def test_band_of_non_band_shapes_return_none() -> None:
    """单侧/∈ 档列表/跨字段/单子句/同向双子句 → None（无带宽概念）。"""
    assert band_of("v <= 13.0") is None  # type: ignore[misc]
    assert band_of("n ∈ [2.0, 4.0]") is None  # type: ignore[misc]
    assert band_of("x >= 1.0 and y <= 2.0") is None  # type: ignore[misc]
    assert band_of("v >= 1.0 and v >= 5.0") is None  # type: ignore[misc]


def test_band_of_degenerate_band_returns_none() -> None:
    """退化带（low>=high）→ None 不产出裕度（门一 W1 回炉处置：与过滤面
    行为对称——恒不可行带由 apply_constraints 自然产出空集，low==high 单点
    带可行域不受误杀；裕度面不引入任务级行为回归）。"""
    assert band_of("v >= 5.0 and v <= 3.0") is None  # type: ignore[misc]
    assert band_of("v >= 5.0 and v <= 5.0") is None  # type: ignore[misc]  单点带：无带宽概念


# ── band_margin_column：归一距离列─────────────────────────────────


def test_band_margin_in_band_values() -> None:
    """带 [7,10]：带缘=0、带中心=0.5、偏侧=距近缘比例（R1 归一距离）。"""
    frame = _frame([{"v": 7.0}, {"v": 8.5}, {"v": 9.25}, {"v": 10.0}])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert column.name == "margin_min"
    assert column.iloc[0] == pytest.approx(0.0)
    assert column.iloc[1] == pytest.approx(0.5)
    assert column.iloc[2] == pytest.approx(0.25)  # min(2.25, 0.75)/3
    assert column.iloc[3] == pytest.approx(0.0)


def test_band_margin_out_of_band_negative() -> None:
    """越带行为负（随后被约束过滤剔除——数学一致不留消费面）。"""
    frame = _frame([{"v": 11.0}, {"v": 5.0}])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert column.iloc[0] == pytest.approx(-1.0 / 3.0)  # min(4, -1)/3
    assert column.iloc[1] == pytest.approx(-2.0 / 3.0)  # min(-2, 5)/3


def test_band_margin_multiple_bands_take_tightest() -> None:
    """多带适用 → 行级取最紧（min——最紧指标优先，与旧 margin_* 语义同口径）。"""
    frame = _frame([
        {"v": 8.5, "p": 0.3},   # 带1=0.5 带2=0.5 → 0.5
        {"v": 8.5, "p": 0.22},  # 带1=0.5 带2=0.1 → 0.1（带2 更紧）
        {"v": 7.1, "p": 0.3},   # 带1≈0.033 带2=0.5 → 0.033
    ])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)
    assert column.iloc[1] == pytest.approx(0.1)
    assert column.iloc[2] == pytest.approx(0.1 / 3.0)


def test_band_margin_non_band_constraints_excluded() -> None:
    """单侧/∈ 约束不产出裕度（无带宽概念——覆盖面随 kb 扩条渐进）。"""
    frame = _frame([{"v": 8.5}])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.one_sided", expression="v <= 13.0", source="kb:test"),
        Constraint(key="kb.discrete", expression="n ∈ [2.0, 4.0]", source="kb:test"),
    ])
    assert isnan(column.iloc[0])


def test_band_margin_field_absent_from_frame_skipped() -> None:
    """带字段不在枚举行列=不适用（跳过；字段合法性由 apply_constraints 统一执法）。"""
    frame = _frame([{"v": 8.5}])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)  # 仅带 v 适用


def test_band_margin_empty_constraints_all_nan() -> None:
    """空约束集 → 全 NaN（「无裕度信息」诚实语义——旧行为兼容面）。"""
    frame = _frame([{"v": 8.5}, {"v": 9.0}])
    column = band_margin_column(frame, [])  # type: ignore[misc]
    assert all(isnan(value) for value in column)


def test_band_margin_nan_field_propagation() -> None:
    """域拒行（字段 NaN）：单带→NaN；他带有效→取有效（skipna 口径——
    双源可行判定仍由 nan_flag 承载，裕度列不重复判）。"""
    frame = _frame([
        {"v": float("nan"), "p": 0.3},
        {"v": 8.5, "p": float("nan")},
    ])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)  # v 带 NaN，p 带 0.5 有效
    assert column.iloc[1] == pytest.approx(0.5)  # v 带 0.5 有效，p 带 NaN
    only_v = band_margin_column(frame, [Constraint(key="kb.band_v",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert isnan(only_v.iloc[0])
    assert only_v.iloc[1] == pytest.approx(0.5)


def test_band_margin_index_follows_frame() -> None:
    """列索引随 frame（调用面 attach 对齐前提——run_enumeration concat 整帧）。"""
    frame = _frame([{"v": 7.0}, {"v": 8.5}, {"v": 9.5}])
    frame.index = pd.Index([10, 20, 30])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert list(column.index) == [10, 20, 30]


# ══ 批3b geometry_guard 几何过滤域（kb 1.5.0 truth 投影——b3b）══

import json  # noqa: E402 （域内追加——kb truth 读取用，isnan 先例同位）
from pathlib import Path  # noqa: E402

from waterprint.contracts.unit_api import Severity  # noqa: E402

_REPO_DATA = Path(__file__).resolve().parents[3] / "data"


def _geometry_constraints() -> list:
    """kb 1.5.0 geometry_guard 8 条 → Constraint 集（真源投影——severity 随行）。

    极性注记（门一 B1 勘正后）：geometry_guard 表达式=门内合规条件（单侧
    `field <= <float>`，真=在门内），与 enumeration_filter 可行带极性统一
    ——勾选即过滤越门行（feasible=合规保留集）。
    """
    raw = json.loads((_REPO_DATA / "constraint_kb" / "constraints.json").read_bytes())
    return [
        Constraint(  # type: ignore[misc]
            key=str(item["key"]),
            expression=str(item["expression"]),
            source=str(item["source"]),
            severity=Severity(str(item["severity"])),
        )
        for item in raw["entries"]
        if item["kind"] == "geometry_guard"
    ]


def test_geometry_gates_reject_absurd_pool_dimensions() -> None:
    """批3b（B1 勘正）：audit AUD-B3 病例几何（l=27779/b=11111.5/v=15.43 亿/
    n_aerator=1.87 亿）——8 门全假=荒诞组合全拒（越门行被滤除——批次目的
    「防荒诞几何静默通过」的过滤面实证）。"""
    gates = _geometry_constraints()
    assert len(gates) == 8  # kb 1.5.0 geometry_guard 全量（真源投影前提）
    frame = _frame([{
        "l_pool": 27779.0, "b_pool": 11111.5,
        "v_pool": 1.543e9, "n_aerator": 1.87e8,
    }])
    result = apply_constraints(frame, gates)
    assert list(result.feasible) == []  # 荒诞行全门假→被滤
    assert not result.pass_matrix.to_numpy().any()


def test_geometry_gates_pass_golden_like_dimensions() -> None:
    """批3b（B1 勘正）：golden 量级单池（l=95/b=38/v=18050/n_aerator≈2165）
    ——8 门全真=合规行保留（工程常用域零误杀——b3a §三复算「全绿」行）。"""
    frame = _frame([{
        "l_pool": 95.0, "b_pool": 38.0, "v_pool": 18050.0, "n_aerator": 2165.0,
    }])
    result = apply_constraints(frame, _geometry_constraints())
    assert list(result.feasible) == [0]
    assert result.pass_matrix.to_numpy().all()


def test_geometry_gate_edge_value_kept_strict_semantics() -> None:
    """批3b（门一 N2）：恰等值不触发——l_pool=300.0 对 `l_pool <= 300.0`
    为真=恰值行保留（严格越门语义：仅 >300 被滤，闭门内含端点）。"""
    frame = _frame([
        {"l_pool": 300.0},   # 恰等=门内（保留）
        {"l_pool": 300.001},  # 严格越门（滤除）
    ])
    gate = next(
        c for c in _geometry_constraints() if c.key == "geometry.l_pool_hint"
    )
    result = apply_constraints(frame, [gate])
    assert list(result.feasible) == [0]


# ══ uf61-axes 批 2026-10-02：kb 装载器域（fail-fast 三态拒+DSL 单源列举）══
# 回炉轮 1 R3：实现已落地——直 import 撤 getattr 脚手架；三态拒+坏 DSL 四处
# 钉 InvalidConstraintError（假绿通道封堵——泛 Exception 会被任意意外异常染绿）

from waterprint.solution.constraints import (  # noqa: E402 （域内追加直 import）
    InvalidConstraintError,
    KbConstraint,
    expression_fields,
    load_kb_constraints,
)


def test_kb_loader_loads_all_entries_with_unit_kinds() -> None:
    """装载正门：151 条计数+首末键锚+unit_kinds/kind 透传+source=kb 键/severity 随行。"""
    loaded = load_kb_constraints(_REPO_DATA / "constraint_kb" / "constraints.json")
    assert len(loaded) == 151  # kb 2.0.0 全量（真源计数锚——1A3 批 42+1A4 批 param_band 109）
    assert loaded[0].constraint.key == "vxinglvchi.v_filter_band"  # 首键
    assert loaded[-1].constraint.key == "param.z_water_inlet.positive"  # 末键（1A4
    # 批尾挂 param_band 109 条按字段名字典序——末位 z_water_inlet）
    assert isinstance(loaded[0].unit_kinds, tuple)
    assert "municipal_aao" in loaded[33].unit_kinds  # unit_kinds 透传（旧末键位）
    assert loaded[0].kind == "enumeration_filter"  # kind 透传（回炉 R2）
    assert loaded[34].kind == "input_band"  # 1A1 kind 透传（装载器零拒零裁）
    assert loaded[41].kind == "mass_balance"  # 1A3 新 kind 透传（宽容面不动）
    assert loaded[-1].kind == "param_band"  # 1A4 新 kind 透传（宽容面不动）
    assert loaded[-1].unit_kinds == ("mine_water_input",)  # 1A4 unit_kinds 非空
    # 透传（节点 ID 选条判据面——geometry_guard 非空先例同族）
    assert loaded[-1].constraint.source == loaded[-1].constraint.key  # source=kb 键
    assert loaded[-1].constraint.severity == Severity("WARN")  # severity 随行（param_band WARN）


def test_kb_loader_missing_file_rejected() -> None:
    """fail-fast①：文件缺失显式拒（InvalidConstraintError 钉型——禁静默空表）。"""
    with pytest.raises(InvalidConstraintError, match="constraint_kb"):
        load_kb_constraints(_REPO_DATA / "constraint_kb" / "absent.json")


def test_kb_loader_corrupt_json_rejected(tmp_path: Path) -> None:
    """fail-fast②：损坏 JSON 显式拒（宽容面归 CLI/未来调用方——装载器拒）。"""
    broken = tmp_path / "broken_constraints.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(InvalidConstraintError, match="JSON"):
        load_kb_constraints(broken)


def test_kb_loader_empty_entries_rejected(tmp_path: Path) -> None:
    """fail-fast③：entries 空表显式拒（GR-14 空集显式语义）。"""
    empty = tmp_path / "empty_constraints.json"
    empty.write_text(json.dumps({"comment": "x", "entries": []}), encoding="utf-8")
    with pytest.raises(InvalidConstraintError, match="entries"):
        load_kb_constraints(empty)


def test_kb_loader_bad_dsl_rejected(tmp_path: Path) -> None:
    """装载期 DSL 校验：坏档（未知算符）fail-visible 拒（装载即验零延迟爆）。"""
    bad = tmp_path / "bad_dsl.json"
    bad.write_text(json.dumps({"entries": [{
        "key": "kb.bad.dsl", "kind": "geometry_guard", "unit_kinds": ["x"],
        "expression": "v_pool ~= 100.0", "source": "stub", "severity": "ERROR",
    }]}), encoding="utf-8")
    with pytest.raises(InvalidConstraintError, match="约束子句语法非法"):
        load_kb_constraints(bad)


def test_kb_loader_reserved_key_rejected(tmp_path: Path) -> None:
    """回炉轮 1 R2：key=any_fail 保留字拒（face 汇总键
    maint.<node>.kb.any_fail 命名域冲突防护——数据面门禁前置到装载面）。"""
    clash = tmp_path / "reserved_key.json"
    clash.write_text(json.dumps({"entries": [{
        "key": "any_fail", "kind": "geometry_guard", "unit_kinds": ["x"],
        "expression": "v_pool <= 100.0", "source": "stub", "severity": "ERROR",
    }]}), encoding="utf-8")
    with pytest.raises(InvalidConstraintError, match="保留字"):
        load_kb_constraints(clash)


def test_expression_fields_dedup_ordered() -> None:
    """DSL 单源字段列举（kb 适用判据消费）：去重保持现序+band/∈ 档两形态
    （回炉 R8 补测——kb 真源两种表达式形态的列举面）。"""
    assert expression_fields("v >= 7.0 and v <= 10.0 and v > 3") == ("v",)
    assert expression_fields("l_pool <= 300.0 and b_pool >= 4") == (
        "l_pool", "b_pool")
    assert expression_fields("x >= 2.0 and x <= 4.0") == ("x",)  # band 形态
    assert expression_fields("n ∈ [2.0, 4.0]") == ("n",)  # ∈ 档列表形态
