"""市政真环 golden 端到端（34,760 m³/d+产泥真边+sup/filtrate 真回流；GOLDEN4b 批）。

输入:  golden_data/municipal_34760_loop/{input_project,expected_summary}.json
输出:  21 节点真环图全流程对照断言（D1~D4：主线 19 节点+hebing 三 IN 口
       产泥真边×3[GOLDEN4a 双模的入流直值模式]+sup/filtrate 两 recycle
       边+rj 两出边 forward[2+2 校正——D1 原四边全 recycle 触 executor
       冻结覆盖式语义，见 notes §2.1]——16 节点大 SCC 经 solve_loop 阻尼
       迭代收敛；5 工况终水逐项+20 单元主尺寸+水量真闭合逐工况+收敛
       元数据锚+迁移对照+m3 双锚+serialize 双跑——2026-08-28 GOLDEN4b）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：GOLDEN4b D4 断言族照 v1 recycle 先例六段同构（工况集/effluent
#   键集钳制/design_dims 键集/summary/serialize 双跑）+真环专属四面：
#   ①图形态断言（input 侧——3 产泥边 forward+sup/filtrate recycle=true
#     +rj 出边 forward 的 2+2 校正形态+hebing 产率链六键收缩）；
#   ②水量真闭合逐工况（bashi 出流=inlet+该工况 q_sup/86400+
#     q_filtrate/86400——v1 位级口径在阻尼迭代下放松至 <1e-10 容差带，
#     实测闭合差 <2e-13）；
#   ③迁移对照断言（与 v1 recycle 案例同名锚机器 diff——ds_total
#     +8.728188%/q_total +4.402958%[真环迭代收敛>单程预告 +3.862%/
#     +1.972%——回流 SS 逐级传播二阶效应，4a-final N-1 预告为单程
#     真边口径，呈报记档 notes §4]；终水 SS 实值方向断言）；
#   ④收敛元数据锚（serialize trace 面逐工况 NS-F9 迹节点数=17=
#     16 次 solve_loop 迭代+1 次收敛解终跑——iterations<200 且 <20
#     步预判的机器实证）。
#   期望值真源=app 正门一次实跑落盘（禁手打——生成脚本实录见实现报告）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (
            Path(__file__).parent
            / "golden_data"
            / "municipal_34760_loop"
            / "expected_summary.json"
        ).is_file(),
        reason="golden 数据未整理（GOLDEN4b：真环案例由领域专家录入）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_REPO_PRICES = Path(__file__).resolve().parents[3] / "data" / "unit_prices"
_TERMINAL = "municipal_bashi_jiliangcao"
_V1_CASE = "municipal_34760_recycle"
_SECS_PER_DAY = 86400.0
# 真环收敛迭代实数（solve_loop 计数探针实录 2026-08-28）：16 次/工况；
# 收敛解终跑+1 → 单工况 nongsuo（NS-F9 每跑一次）迹节点=17。
_LOOP_TRACE_APPLYINGS = 17
# 迁移比实值（探针实录）：ds_total ×1.087281878803 / q_total ×1.044029575012。
_MIGRATION_DS_RATIO = (1.08728187, 1.08728189)
_MIGRATION_Q_RATIO = (1.04402957, 1.04402958)
# 4a-final N-1 单程预告下界（真环迭代收敛必超单程口径——二阶效应方向机证）。
_FORECAST_DS_RATIO = 1.03862


def _conditions(expected: dict[str, Any]):
    """工况集正门（checked_units 承载于 expected——市政先例 §2.2）。"""
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set(expected["checked_units"])


def _front_door(case_dir: Path, expected: dict[str, Any]):
    """正门三件：load_project → RunEnv → run_full_calc（env 口径=generated 实录）。"""
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    project = load_project(case_dir / "input_project.json")
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    return project, env, run_full_calc(project, _conditions(expected), env)


def _assert_graph_shape(case_dir: Path) -> None:
    """真环专属①：input 侧图形态（2+2 回流链+3 产泥真边+hebing 六键收缩）。"""
    raw = json.loads(
        (case_dir / "input_project.json").read_text(encoding="utf-8")
    )
    edges = raw["design"]["edges"]
    by_mark = {
        (
            e["src"]["unit_id"],
            e["src"]["port_id"],
            e["dst"]["unit_id"],
            e["dst"]["port_id"],
        ): e.get("recycle", False)
        for e in edges
    }
    assert len(raw["design"]["nodes"]) == 21 and len(edges) == 24  # D1 拓扑全同
    for src, sp, dst, dp in (
        ("municipal_chuchenchi", "sludge_out", "sludge_hebing", "in_primary"),
        ("municipal_aao", "sludge_out", "sludge_hebing", "in_bio"),
        ("municipal_gaomidu", "sludge_out", "sludge_hebing", "in_chem"),
    ):
        assert by_mark[(src, sp, dst, dp)] is False, f"产泥真边 {src}（forward）"
    assert by_mark[("sludge_nongsuo", "sup", "rj_sup", "in")] is True
    assert by_mark[("sludge_tuoshui", "filtrate", "rj_filtrate", "in")] is True
    # 2+2 校正：rj 出边 forward（recycle 股覆盖式赋值不参与 propagate 合并
    # ——executor 冻结语义，D1 全 recycle 形态被拒后入流直值/合并面校正）
    assert by_mark[("rj_sup", "out", "municipal_wushui_tisheng", "in")] is False
    assert (
        by_mark[("rj_filtrate", "out", "municipal_wushui_tisheng", "in")] is False
    )
    hebing = raw["design"]["nodes"]["sludge_hebing"]
    assert set(hebing) == {
        "q_avg_daily", "s0_bod", "se_bod", "v_bio", "x_vss", "t_design"
    }, "hebing 产率链六键收缩（ds/p 撤出——三股由真边供）"


def _assert_effluent_and_dims(
    plant: Any, project: Any, expected: dict[str, Any], keys: list[str]
) -> None:
    """② 逐工况终水+③ design 主尺寸（键集钳制防删块静默绿）+summary 真值。"""
    assert set(expected["effluent"]) == set(keys)
    for condition_key, fields in expected["effluent"].items():
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            actual = snapshot.outqualities[f"{_TERMINAL}.out.{indicator}"]
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"
    assert set(expected["design_dims"]) == set(project.design.nodes) - {"inlet"}
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"
    # app 层 summary 真值投影：真环调度下泥线汇点 ganhua（非组成员，层 15）
    # 后于水线 bashi（层 11）完成——terminal（快照序末位无出边单元）=泥线
    # ganhua，无水质键→空映射合法（_summary_of 契约原文"污泥线终端无水质
    # 键→空映射合法"；v1 前向回流使 rj 居深层水线被推后、bashi 恰居末——
    # 真环形态下该启发式取泥线汇点，终水六指标面由 effluent 锚承载）
    for condition_key in keys:
        assert plant.summary[condition_key] == {}, condition_key


def _assert_water_closure(plant: Any, keys: list[str]) -> None:
    """真环专属②：水量真闭合逐工况（收敛解上断言——该工况回流量自洽）。"""
    for condition_key in keys:
        snapshot = plant.conditions[condition_key]
        inlet_q = snapshot["inlet"].outflows["inlet.out.q_avg_daily"]
        q_sup = snapshot["sludge_nongsuo"].dims["q_sup"]
        q_filtrate = snapshot["sludge_tuoshui"].dims["q_filtrate"]
        balanced = inlet_q + q_sup / _SECS_PER_DAY + q_filtrate / _SECS_PER_DAY
        q_bashi = snapshot[_TERMINAL].outflows[f"{_TERMINAL}.out.q_avg_daily"]
        assert q_bashi == pytest.approx(
            balanced, rel=1e-12, abs=1e-11
        ), f"水量真闭合 {condition_key}：{q_bashi!r} != {balanced!r}"


def _assert_migration(golden_data_dir: Path, expected: dict[str, Any]) -> None:
    """真环专属③：与 v1 recycle 案例同名锚机器 diff（迁移量机证）。"""
    v1 = json.loads(
        (
            golden_data_dir / _V1_CASE / "expected_summary.json"
        ).read_text(encoding="utf-8")
    )
    loop_hb = expected["design_dims"]["sludge_hebing"]
    v1_hb = v1["design_dims"]["sludge_hebing"]
    ds_ratio = loop_hb["ds_total"]["value"] / v1_hb["ds_total"]["value"]
    q_ratio = loop_hb["q_total"]["value"] / v1_hb["q_total"]["value"]
    assert _MIGRATION_DS_RATIO[0] < ds_ratio < _MIGRATION_DS_RATIO[1], (
        f"ds_total 迁移比 {ds_ratio!r}（真环收敛 vs v1 前向叠加）"
    )
    assert _MIGRATION_Q_RATIO[0] < q_ratio < _MIGRATION_Q_RATIO[1], (
        f"q_total 迁移比 {q_ratio!r}"
    )
    # 真环迭代收敛必超单程预告（+3.862%）——回流 SS 逐级传播二阶效应方向机证
    assert ds_ratio > _FORECAST_DS_RATIO, "真环 ds_total 必超单程真边预告"
    loop_ss = expected["effluent"]["design"]["SS"]["value"]
    v1_ss = v1["effluent"]["design"]["SS"]["value"]
    assert loop_ss > v1_ss, "终水 SS 真环>前向叠加（回流 SS 增益方向）"


def _assert_m3(plant: Any, expected: dict[str, Any]) -> None:
    """m3 断言（cost 三正门直调+逐级自洽+hebing 双锚）。"""
    from waterprint.cost.estimate import build_estimate, load_fee_rules
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import takeoff_quantities

    book = load_prices(_REPO_PRICES)
    fees = load_fee_rules(_REPO_PRICES / "field_mapping.yaml", book)
    items = takeoff_quantities(plant, "design", price_book=book)
    sheet = build_estimate(items, book, fees)
    assert (
        sheet.subtotal + sheet.reserve_subtotal + sum(line.amount for line in sheet.tax)
        == sheet.grand_total
    )
    m3 = expected["m3_deferred"]
    for key in ("estimate_total", "total_sludge"):
        assert set(m3[key]) == {"value", "source", "abs", "rel"}, key
    estimate = m3["estimate_total"]
    assert sheet.grand_total == pytest.approx(
        estimate["value"], rel=estimate["rel"], abs=estimate["abs"]
    ), "m3_deferred.estimate_total（21 节点真环图 design 档 grand_total）"
    hebing = plant.conditions["design"]["sludge_hebing"].dims
    assert hebing["ds_total"] == pytest.approx(
        m3["total_sludge"]["value"],
        rel=m3["total_sludge"]["rel"],
        abs=m3["total_sludge"]["abs"],
    ), "m3_deferred.total_sludge（hebing ds_total——真边实跑口径）"
    wet = expected["design_dims"]["sludge_hebing"]["q_total"]
    assert hebing["q_total"] == pytest.approx(
        wet["value"], rel=wet["rel"], abs=wet["abs"]
    ), "hebing q_total（湿基 m³/d——m3 双断言第二锚）"


def test_municipal_loop_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：真环图 5 工况终水+20 单元主尺寸+水量真闭合+迁移对照+m3+serialize。"""
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet
    from waterprint.contracts.result_schema import serialize

    case_dir = golden_data_dir / "municipal_34760_loop"
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )
    keys = [ConditionSet.key(c) for c in _conditions(expected).iter_all()]
    assert keys == expected["condition_keys"]
    assert len(keys) == 2 + len(expected["checked_units"]) == 5  # ⑤ 工况 2+k

    _assert_graph_shape(case_dir)  # ① 图形态（input 侧）

    project, env, bundle = _front_door(case_dir, expected)
    plant = bundle.plant
    assert set(plant.conditions) == set(keys)  # ① 正门三断言
    assert plant.repro.design_hash == project.metadata.content_hash
    assert set(plant.summary) == set(keys)

    _assert_effluent_and_dims(plant, project, expected, keys)
    _assert_water_closure(plant, keys)  # ② 水量真闭合（逐工况）
    _assert_migration(golden_data_dir, expected)  # ③ 迁移对照（机器实证）
    _assert_m3(plant, expected)

    first = serialize(run_full_calc(project, _conditions(expected), env).plant)
    second = serialize(run_full_calc(project, _conditions(expected), env).plant)
    assert first == second  # ⑥ serialize 双跑字节同（确定性 R3）
    assert len(first) == expected["generated"]["serialize_bytes"]
    assert hashlib.sha256(first).hexdigest()[:16] == (
        expected["generated"]["serialize_sha256_head"]
    )
    # ④ 收敛元数据锚：trace 面逐工况 NS-F9 迹节点数（16 迭代+1 终跑=17）
    tree = json.loads(first)["trace"]
    per_condition = {
        condition_key: sum(
            1
            for node in tree
            if node.get("condition_key") == condition_key
            and node.get("formula_id") == "NS-F9"
        )
        for condition_key in keys
    }
    assert set(per_condition.values()) == {_LOOP_TRACE_APPLYINGS}, (
        per_condition
    )
