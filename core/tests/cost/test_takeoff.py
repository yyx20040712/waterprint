"""takeoff 镜像测试：工程量提取（字段 ID 取数、单位一致、溯源完整）。

输入:  waterprint.cost.takeoff 公开符号
输出:  提取语义断言（中文匹配零容忍——§3 保证 4）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.cost.takeoff")
takeoff_quantities = getattr(_mod, "takeoff_quantities", None)
TakeoffItem = getattr(_mod, "TakeoffItem", None)

pytestmark = pytest.mark.skipif(
    None in (takeoff_quantities, TakeoffItem),
    reason="实现未就绪：waterprint.cost.takeoff（M3）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：takeoff_quantities(plant_result, condition_key)。"""
    assert callable(takeoff_quantities)


def test_takeoff_item_carries_audit_fields() -> None:
    """R3：清单条目必含 price_key/quantity/unit/source_field_ids（可审计四件）。"""
    names = {f.name for f in dataclasses.fields(TakeoffItem)}
    assert {"price_key", "quantity", "unit", "source_field_ids"} <= names


def test_unit_mismatch_wiring_assertion() -> None:
    """R2 接线断言：量单位与单价单位不一致 → 领域异常（不得静默换算）。

    需要 PriceBook 与 PlantResult 可构造（M3）后接线；实现者不得删除。
    """
    import tempfile
    from pathlib import Path

    from waterprint.contracts.result_schema import (
        PlantResult,
        ReproTriple,
        UnitResultSnapshot,
    )
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import (
        FieldMapping,
        InvalidTakeoffError,
        QuantityRule,
        takeoff_quantities,
    )

    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "unit_prices"
        pkg.mkdir()
        (pkg / "manifest.yaml").write_text(
            "price_data_version: '1.0.0-test'\nunit_scales:\n  m3: 1\n",
            encoding="utf-8",
        )
        (pkg / "buildings.yaml").write_text("\n".join([
            "- key: C30-TEST",
            "  name: 测试混凝土",
            "  unit: m3",
            "  price: 100.0",
            "  source: 测试定额",
        ]), encoding="utf-8")
        book = load_prices(pkg)
    mapping = FieldMapping(rules=(
        QuantityRule(
            price_key="C30-TEST",
            unit="t",
            mode="direct",
            source_field_ids=("v_concrete",),
            cost_class="civil",
            source="测试映射（单位故意与单价条目 m3 不一致）",
            unit_id="municipal_chuchenchi",
        ),
    ))
    snapshot = UnitResultSnapshot(
        unit_id="municipal_chuchenchi",
        outflows={},
        outqualities={},
        dims={"v_concrete": 100.0},
        warnings=(),
        formula_ids=(),
    )
    plant = PlantResult(
        conditions={"design": {"municipal_chuchenchi": snapshot}},
        summary={},
        trace=(),
        repro=ReproTriple("", "", ""),
    )
    with pytest.raises(InvalidTakeoffError, match="不一致"):
        takeoff_quantities(
            plant, "design", price_book=book, field_mapping=mapping
        )


# ══ 批6d AAO capex 区分度数据面（takeoff 对拍——b6d-design §四；
#     [HUMAN-LOCK] 2026-09-26 预授权①随批落地）══


def test_aao_aerator_row_resolves_per_series_count() -> None:
    """批6d 对拍：真包+真链 municipal_aao 明细含曝气系统行——量=池数 n
    （台=组口径：cass 组 quantity=池数同款；dims 回显字段直取）。n=3 档
    取数（d1 W-1：默认 n=2 与包内参考 quantity=2 同值——无判别力）。"""
    from pathlib import Path

    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import load_field_mapping, takeoff_quantities

    data_dir = Path(__file__).resolve().parents[3] / "data" / "unit_prices"
    book = load_prices(data_dir)
    mapping = load_field_mapping(data_dir / "field_mapping.yaml")

    from tests.solution.test_beam import _AAO, _conditions, _env, _project
    from waterprint.app_assembly import assemble
    from waterprint.solution.joint_enumeration import execute_graph
    from waterprint.solution.joint_enumeration.final_eval import completed_env

    env = completed_env(_env())
    project = _project().model_copy(deep=True)
    project.design.nodes[_AAO]["n"] = 3.0  # 异于包内参考 quantity=2 的档
    plant = execute_graph(
        project.design, assemble(project, env).units, _conditions(), env
    )
    items = takeoff_quantities(
        plant, "design", price_book=book, field_mapping=mapping
    )
    rows = [it for it in items if it.price_key == "aao.microporous_aerator_piping"]
    assert len(rows) == 1, "aao 曝气系统行恰一行（unit_id 限定）"
    row = rows[0]
    assert row.unit == "万元/台"
    assert row.quantity == pytest.approx(3.0)  # 池数 n=3（≠参考 quantity=2——direct 生效判别）
    assert row.source_field_ids == ("municipal_aao.n",)  # 溯源=dims 回显字段
    assert row.cost_class == "equipment"
