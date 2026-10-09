"""blocks 纯投影辅助镜像测试（B6 移植 core 镜像规则新增件）。

覆盖：unit_zh/indicator_of/condition_label（声明面映射与回落）；
anchor_index（design 工况 trace 投影——round(x,10) 键+首现优先）；
ordered_dim_fields/dim_label_unit（manifest out_dims 声明序与回落）；
ordered_units（inlet 起 BFS 工序序+未达单元殿后——确定性）。
"""

from __future__ import annotations

from pathlib import Path

from waterprint.app import discover_units, load_project
from waterprint.contracts.manifest import UnitManifest
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    TraceNode,
    UnitResultSnapshot,
)
from waterprint.report.blocks import (
    anchor_index,
    condition_label,
    dim_label_unit,
    indicator_of,
    ordered_dim_fields,
    ordered_units,
    unit_zh,
)

# 声明面映射样本（blocks._UNIT_NAMES_ZH 在册键）
_KNOWN_UNIT = "municipal_aao"


def _trace_plant() -> PlantResult:
    """合成 trace：design 两节点（同公式不同值）+非 design 工况一节点。"""
    snapshot = UnitResultSnapshot(
        unit_id="u_b",
        outflows={},
        outqualities={},
        dims={},
        warnings=(),
        formula_ids=(),
    )
    design_node = TraceNode(
        formula_id="BF-1",
        inputs={},
        output=1.0,
        norm_ref="合成 §1",
        unit_id="u_a",
        condition_key="design",
    )
    design_node_dup = TraceNode(
        formula_id="BF-2",
        inputs={},
        output=2.0,
        norm_ref="合成 §2",
        unit_id="u_a",
        condition_key="design",
    )
    avg_node = TraceNode(
        formula_id="BF-3",
        inputs={},
        output=3.0,
        norm_ref="合成 §3",
        unit_id="u_a",
        condition_key="avg",
    )
    return PlantResult(
        conditions={"design": {"u_b": snapshot}},
        summary={},
        trace=(design_node, design_node_dup, avg_node),
        repro=ReproTriple(design_hash="h", engine_version="e", data_version="d"),
    )


class TestDisplayNames:
    """unit_zh／indicator_of／condition_label 声明面映射。"""

    def test_known_unit_maps_to_zh(self) -> None:
        assert unit_zh(_KNOWN_UNIT) == "AAO 生物池"

    def test_unknown_unit_falls_back_to_id(self) -> None:
        assert unit_zh("u_ghost") == "u_ghost"

    def test_indicator_strips_unit_prefix(self) -> None:
        assert indicator_of("municipal_aao.out.bod5", "municipal_aao") == "bod5"

    def test_indicator_keeps_foreign_key(self) -> None:
        assert indicator_of("other.out.bod5", "municipal_aao") == "other.out.bod5"

    def test_condition_labels(self) -> None:
        assert condition_label("design") == "最高日最高时设计工况"
        assert condition_label("avg") == "平均时工况"
        offline = condition_label("design_offline_municipal_aao")
        assert "municipal_aao" in offline and "检修" in offline
        assert condition_label("weird") == "weird"


class TestAnchorIndex:
    """anchor_index：design 工况 trace → 单元×值 → 公式 ID。"""

    def test_design_nodes_indexed_by_unit_and_rounded_value(self) -> None:
        index = anchor_index(_trace_plant())
        assert index == {"u_a": {1.0: "BF-1", 2.0: "BF-2"}}

    def test_avg_condition_excluded(self) -> None:
        index = anchor_index(_trace_plant())
        assert 3.0 not in index.get("u_a", {})


class TestDimProjection:
    """ordered_dim_fields／dim_label_unit：manifest 声明序与缺省回落。"""

    def test_declared_fields_first_then_sorted_rest(self) -> None:
        manifests = discover_units()
        manifest, _factory = manifests[_KNOWN_UNIT]
        declared = [spec.field_id for spec in manifest.out_dims]
        assert declared, "AAO manifest 应带 out_dims 声明面"
        dims = dict.fromkeys(declared, 1.0)
        dims["zz_extra"] = 2.0
        dims["aa_extra"] = 3.0
        ordered = ordered_dim_fields(dims, manifest)
        assert ordered[: len(declared)] == declared
        assert ordered[len(declared):] == ["aa_extra", "zz_extra"]

    def test_none_manifest_sorts_all_keys(self) -> None:
        assert ordered_dim_fields({"b": 1.0, "a": 2.0}, None) == ["a", "b"]

    def test_label_unit_declared_and_fallback(self) -> None:
        manifests = discover_units()
        manifest, _factory = manifests[_KNOWN_UNIT]
        spec = manifest.out_dims[0]
        label, unit = dim_label_unit(spec.field_id, manifest)
        assert label  # 声明面直投（label_zh 或字段 ID——非空）
        assert dim_label_unit("no_such_field", manifest) == ("no_such_field", "")
        assert dim_label_unit("any", None) == ("any", "")


class TestOrderedUnits:
    """ordered_units：工序序 BFS+确定性（golden 项目实拓扑）。"""

    def test_bfs_order_excludes_inlet_and_is_deterministic(
        self, golden_project_path: Path
    ) -> None:
        project = load_project(golden_project_path)
        manifests = discover_units()
        snapshot = {
            unit_id: UnitResultSnapshot(
                unit_id=unit_id,
                outflows={},
                outqualities={},
                dims={},
                warnings=(),
                formula_ids=(),
            )
            for unit_id in manifests
            if unit_id != "inlet"
        }
        ordered = ordered_units(project, snapshot)
        assert "inlet" not in ordered
        assert set(ordered) == set(snapshot)
        assert ordered == ordered_units(project, snapshot)  # 确定性
        _assert_manifest_unused_type(manifests[_KNOWN_UNIT][0])


def _assert_manifest_unused_type(manifest: UnitManifest) -> None:
    """类型面锚（mypy strict 下 blocks 消费的 UnitManifest 形态）。"""
    assert isinstance(manifest, UnitManifest)
