"""flows 用例流层镜像测试：编排函数族签名冻结面（AI1 轨道甲，2026-09-13）。

输入:  waterprint.flows 公开符号（任务书 §3 预裁决冻结签名）+ golden 数据
输出:  编排契约断言（env/conditions/standards/calc/persist/validate/
       export/audit/estimate/guard 各流——先红后绿 TDD 承载件）
"""

from __future__ import annotations

import importlib
import json
import warnings
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.flows")

_REPO_DATA = Path(__file__).resolve().parents[3] / "data"


def _load_municipal(golden_data_dir: Path):
    """golden municipal 项目装载（load_project 正门——版本门随行）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / "municipal_34760" / "input_project.json")


# ── build_env_flow / build_condition_flow / build_standards_flow ─────────


def test_build_env_flow_composes_run_env(golden_data_dir: Path) -> None:
    """env 流：DEFAULT_ASSUMPTIONS+overrides 合成、UF-10 版本聚合、七字段。"""
    from waterprint.contracts.run_env import RunEnv

    env = _mod.build_env_flow(_REPO_DATA, _load_municipal(golden_data_dir))
    assert isinstance(env, RunEnv)
    assert env.engine_version  # 非空（core 包根 __version__ 真源）
    assert "coefficients@" in env.data_version  # UF-10 聚合（sorted + 拼接）
    assert env.price_book == {}
    assert env.trace_sink is None
    assert set(env.assumptions)  # DEFAULT_ASSUMPTIONS 全量默认在
    assert env.assumptions["loop.tolerance"] == pytest.approx(1e-10)


def test_build_env_flow_overrides_win(golden_data_dir: Path) -> None:
    """env 流：design.assumption_overrides 覆盖默认（合成视图优先序）。"""
    project = _load_municipal(golden_data_dir)
    patched = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"assumption_overrides": {"loop.damping": 0.5}}
            )
        }
    )
    env = _mod.build_env_flow(_REPO_DATA, patched)
    assert env.assumptions["loop.damping"] == pytest.approx(0.5)


def test_build_condition_flow_baseline_and_checked(golden_data_dir: Path) -> None:
    """conditions 流：keys=None 基线两档；keys=受检单元 2+k 线性（ADR-007）。"""
    from waterprint.contracts.condition import ConditionSet

    project = _load_municipal(golden_data_dir)
    baseline = _mod.build_condition_flow(project, None)
    assert isinstance(baseline, ConditionSet)
    assert [ConditionSet.key(c) for c in baseline.iter_all()] == ["design", "avg"]
    checked = _mod.build_condition_flow(project, ("municipal_aao",))
    assert len(list(checked.iter_all())) == 2 + 1


def test_build_standards_flow_loads_and_warns(golden_data_dir: Path) -> None:
    """standards 流：真数据包装载非空；目录缺失=() + UserWarning（宽容面）。"""
    standards = _mod.build_standards_flow(_REPO_DATA)
    assert standards  # data/constraint_kb/constraints.json 在（真库）
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        empty = _mod.build_standards_flow(golden_data_dir / "no_such_data")
    assert empty == ()
    assert caught and "constraints.json" in str(caught[-1].message)


# ── run_calc_flow / result_persist_flow / validate_flow ───────────────────


def test_run_calc_flow_without_out(golden_data_dir: Path) -> None:
    """calc 流：result_out 缺省=不落盘；digest=design_hash 锚定输入。"""
    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    conditions = _mod.build_condition_flow(project, None)
    result = _mod.run_calc_flow(project, conditions, env, ())
    assert result.result_path is None
    assert result.plant.repro.design_hash == project.metadata.content_hash
    assert result.design_digest == project.metadata.content_hash
    assert set(result.plant.conditions) == {"design", "avg"}


def test_run_calc_flow_persists(golden_data_dir: Path, tmp_path: Path) -> None:
    """calc 流：result_out 给定→serialize 产物落盘可回读（确定性往返）。"""
    from waterprint.contracts.result_schema import deserialize

    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    out = tmp_path / "r.result.json"
    result = _mod.run_calc_flow(
        project, _mod.build_condition_flow(project, None), env, (),
        result_out=out,
    )
    assert result.result_path == out
    assert out.is_file()
    assert deserialize(out.read_bytes()).repro.design_hash == result.design_digest


def test_result_persist_flow_atomic_roundtrip(
    golden_data_dir: Path, tmp_path: Path
) -> None:
    """persist 流：原子落盘（同目录 tmp→replace）+字节往返；重复写幂等。"""
    from waterprint.contracts.result_schema import deserialize, serialize

    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    plant = _mod.run_calc_flow(
        project, _mod.build_condition_flow(project, None), env, ()
    ).plant
    out = tmp_path / "a.result.json"
    assert _mod.result_persist_flow(plant, out) == out
    first = out.read_bytes()
    assert first == serialize(plant)
    assert not list(tmp_path.glob("*.tmp"))  # 半写 tmp 不留（GR-38）
    assert deserialize(first).repro.design_hash == plant.repro.design_hash
    _mod.result_persist_flow(plant, out)  # 幂等重写
    assert out.read_bytes() == first


def test_validate_flow_direct(golden_data_dir: Path) -> None:
    """validate 流：app_assembly.validate_design_structure 直通（清单式）。"""
    project = _load_municipal(golden_data_dir)
    assert _mod.validate_flow(project) == ()
    broken = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "edges": [
                        {
                            "src": {"unit_id": "ghost_unit", "port_id": "out"},
                            "dst": {"unit_id": "municipal_aao", "port_id": "in"},
                        }
                    ]
                }
            )
        }
    )
    errors = _mod.validate_flow(broken)
    assert errors and any("ghost_unit" in e for e in errors)


# ── export_flow / audit_render_flow ───────────────────────────────────────


def _plant(golden_data_dir: Path):
    """golden plant 实跑一次（design+avg 两档——快路径）。"""
    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    return _mod.run_calc_flow(
        project, _mod.build_condition_flow(project, None), env, ()
    ).plant


def test_export_flow_calcbook_renders(golden_data_dir: Path, tmp_path: Path) -> None:
    """export 流 calcbook：正式模板渲染落盘（占位符全展开）。"""
    project = _load_municipal(golden_data_dir)
    out = tmp_path / "cb.xlsx"
    path = _mod.export_flow(
        "calcbook", project, _plant(golden_data_dir),
        template_dir=_REPO_DATA / "templates", out=out,
    )
    assert path == out and out.is_file()


def test_export_flow_calcbook_missing_template(
    golden_data_dir: Path, tmp_path: Path
) -> None:
    """export 流守护：模板缺失→InvalidFlowError（CLI 退出码 3 面）。"""
    project = _load_municipal(golden_data_dir)
    with pytest.raises(_mod.InvalidFlowError, match="calcbook_plant"):
        _mod.export_flow(
            "calcbook", project, _plant(golden_data_dir),
            template_dir=tmp_path / "no_templates", out=tmp_path / "x.xlsx",
        )


def test_export_flow_dxf_unit_drawing(golden_data_dir: Path, tmp_path: Path) -> None:
    """export 流 dxf：单单元出图（unit_id 路由）落盘非空。"""
    project = _load_municipal(golden_data_dir)
    out = tmp_path / "u.dxf"
    path = _mod.export_flow(
        "dxf", project, _plant(golden_data_dir),
        template_dir=_REPO_DATA / "templates", out=out,
        unit_id="municipal_aao", condition_key="design",
    )
    assert path == out and out.stat().st_size > 0


def test_export_flow_rejects_unknown_kind_and_escape(
    golden_data_dir: Path, tmp_path: Path
) -> None:
    """export 流守护：未知 kind→InvalidFlowError；out 含 '..'→InvalidFlowError。"""
    project = _load_municipal(golden_data_dir)
    plant = _plant(golden_data_dir)
    with pytest.raises(_mod.InvalidFlowError, match="kind"):
        _mod.export_flow(
            "estimate", project, plant,
            template_dir=_REPO_DATA / "templates", out=tmp_path / "e.bin",
        )
    with pytest.raises(_mod.InvalidFlowError, match="\\.\\."):
        _mod.export_flow(
            "calcbook", project, plant,
            template_dir=_REPO_DATA / "templates",
            out=tmp_path / ".." / "escape.xlsx",
        )


def test_audit_render_flow_writes_html(golden_data_dir: Path, tmp_path: Path) -> None:
    """audit 流：注册表装载前置+HTML 原子落盘（公式溯源标题在场）。"""
    project = _load_municipal(golden_data_dir)
    out = tmp_path / "a.html"
    path = _mod.audit_render_flow(project, _plant(golden_data_dir), out)
    assert path == out and out.is_file()
    document = out.read_text(encoding="utf-8")
    assert "公式溯源审计报告" in document
    assert "<script" not in document  # R3 自包含零脚本


# ── estimate_summary_flow ─────────────────────────────────────────────────


def test_estimate_summary_flow_builds_sheet_and_report(
    golden_data_dir: Path,
) -> None:
    """estimate 流：cost 四模块链（golden 概算真值口径）+指标校核报告。"""
    outcome = _mod.estimate_summary_flow(
        _plant(golden_data_dir), condition_key="design", data_dir=_REPO_DATA
    )
    sheet, report = outcome.sheet, outcome.report
    assert sheet.condition_key == "design"
    assert sheet.grand_total > 0.0
    assert (
        sheet.subtotal + sheet.reserve_subtotal + sum(line.amount for line in sheet.tax)
        == sheet.grand_total
    )  # 逐级自洽（golden m3 口径同款）
    expected = json.loads(
        (
            golden_data_dir / "municipal_34760" / "expected_summary.json"
        ).read_text(encoding="utf-8")
    )["m3_deferred"]["estimate_total"]
    assert sheet.grand_total == pytest.approx(
        expected["value"], rel=expected["rel"], abs=expected["abs"]
    )
    assert report.checked  # 指标带在（单价包 indicator.*）


# ── params_guard ──────────────────────────────────────────────────────────


def _catalog_params(unit_id: str):
    """目录参数面（discover_units——32 包 manifest）。"""
    from waterprint.app import discover_units

    return discover_units()[unit_id][0].params


def _first_grid_entry(specs: dict) -> tuple[str, float]:
    """首个 grid 声明参数（档位首档值——cass n_pool 等枚举维）。"""
    for field_id, spec in specs.items():
        if spec.grid:
            return field_id, float(spec.grid[0])
    raise AssertionError("municipal_aao 无 grid 参数（目录面漂移——查 manifest）")


def test_params_guard_accepts_known_finite_on_grid(golden_data_dir: Path) -> None:
    """guard 面①②③全过：已知键+有限值+命中档位=accepted 全绿。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    verdicts = _mod.params_guard(project, "municipal_aao", {grid_key: grid_value})
    assert len(verdicts) == 1
    assert verdicts[0].accepted is True
    assert verdicts[0].reason is None
    assert verdicts[0].key == grid_key


def test_params_guard_rejects_each_face(golden_data_dir: Path) -> None:
    """guard 三面逐条拒（清单式不拒整批——CLI/MCP 共用口径）。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    off = grid_value + 1.0  # 档位外（相邻整数必不在档——枚举维离散）
    while off in {float(g) for g in specs[grid_key].grid}:
        off += 1.0
    verdicts = _mod.params_guard(
        project,
        "municipal_aao",
        {
            "ghost_key_never": 3,  # ②键未知
            grid_key: off,  # ③档位外
            "ns": True,  # ①bool 冒充 int（已知键——值面独立命中）
        },
    )
    table = {v.key: v for v in verdicts}
    assert table["ghost_key_never"].accepted is False
    assert "不在" in (table["ghost_key_never"].reason or "")
    assert table[grid_key].accepted is False
    assert "档位" in (table[grid_key].reason or "")
    assert table["ns"].accepted is False
    assert "数值" in (table["ns"].reason or "")


def test_params_guard_string_value_rejected(golden_data_dir: Path) -> None:
    """guard ①面独立证：str 值逐条拒（AUDIT2 C-4 探针场景）。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    verdicts = _mod.params_guard(
        project, "municipal_aao", {grid_key: "垃圾字符串值"}
    )
    assert verdicts[0].accepted is False
    assert "数值" in (verdicts[0].reason or "")


def test_params_guard_builtin_kind_channel(golden_data_dir: Path) -> None:
    """guard kind 通道：node 含 kind→builtin 参数面（inlet.kz 与 server 版同径）。"""
    project = _load_municipal(golden_data_dir)
    verdicts = _mod.params_guard(project, "inlet", {"kz": 1.5})
    assert len(verdicts) == 1 and verdicts[0].accepted is True
    unknown = _mod.params_guard(project, "inlet", {"ghost_builtin_key": 1.5})
    assert unknown[0].accepted is False


def test_params_guard_unknown_unit_and_node(golden_data_dir: Path) -> None:
    """guard 守护前置：unit_id 不在 nodes / catalog 目录外→InvalidFlowError。"""
    project = _load_municipal(golden_data_dir)
    with pytest.raises(_mod.InvalidFlowError, match="design.nodes"):
        _mod.params_guard(project, "ghost_unit", {"any": 1.0})
    stranger = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "nodes": {
                        **project.design.nodes,
                        "not_in_catalog": {},  # 无 kind 且不在注册表
                    }
                }
            )
        }
    )
    with pytest.raises(_mod.InvalidFlowError, match="目录"):
        _mod.params_guard(stranger, "not_in_catalog", {"any": 1.0})


# ── enumeration_flow / design_map_flow（直通冒烟） ────────────────────────


def test_enumeration_flow_direct(golden_data_dir: Path) -> None:
    """enumeration 流：run_enumeration 直通（小 limit 冒烟）。"""
    from waterprint.app import EnumerationOptions

    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    outcome = _mod.enumeration_flow(
        project, "municipal_aao", _mod.build_condition_flow(project, None), env,
        options=EnumerationOptions(limit=3),
    )
    assert len(outcome.rows) <= 3 and outcome.total_feasible >= 1


def test_design_map_flow_direct(golden_data_dir: Path) -> None:
    """design_map 流：run_design_map 直通（单轴 ns 连续区间冒烟）。"""
    from waterprint.app import DesignMapOptions

    project = _load_municipal(golden_data_dir)
    env = _mod.build_env_flow(_REPO_DATA, project)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    assert specs["ns"].range is not None  # 连续区间轴前提（FD 契约）
    low, high = specs["ns"].range
    design_map = _mod.design_map_flow(
        project, "municipal_aao", _mod.build_condition_flow(project, None), env,
        options=DesignMapOptions(
            axes=({"field_id": "ns", "range": {"min": low, "max": high}},),
            fixed_params={},
        ),
    )
    assert design_map is not None
