"""UF-33 用例面测试：run_enumeration/export_artifact 经 app 正门 + 装配 grid 校验。

输入:  waterprint.app 公开符号（run_enumeration/export_artifact/assemble/
       EnumerationOptions/ArtifactKindNotReady）+ 真实 coefficients 数据包
输出:  用例契约断言（D2/D3 裁决面：CASS 15 档端到端/档位命中两向/导出两向）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.app")
run_enumeration = getattr(_mod, "run_enumeration", None)
export_artifact = getattr(_mod, "export_artifact", None)
assemble = getattr(_mod, "assemble", None)
InvalidAssemblyError = getattr(_mod, "InvalidAssemblyError", None)
EnumerationOptions = getattr(_mod, "EnumerationOptions", None)
ArtifactKindNotReady = getattr(_mod, "ArtifactKindNotReady", None)

pytestmark = pytest.mark.skipif(
    None
    in (run_enumeration, export_artifact, assemble, EnumerationOptions,
        ArtifactKindNotReady, InvalidAssemblyError),
    reason="实现未就绪：waterprint.app UF-33 用例面（M2-SOL）",
)

_DATA = Path(__file__).resolve().parents[2].parent / "data" / "coefficients"
_UNIT = "municipal_cass"  # 档位最全单元：n_pool [2-6] × t_cycle [4,6,8] = 15 档


def _project(overrides: dict[str, float]) -> object:
    """inlet→CASS 两节点项目（CASS 节点参数可覆盖——档位校验两向载体）。"""
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,  # 三表流量口径
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "TN": 43.0,  # CASS CA-F3/F20 计算前提（包内算例同值）
                },
                _UNIT: dict(overrides),
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": _UNIT, "port_id": "in"},
                }
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m2sol",
            data_version="m2sol",
        ),
    )


def _env() -> object:
    """真实数据包 env（coefficients 0.4.0：factor.cass.*/removal.cass.* 在册）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    return RunEnv(
        engine_version="m2sol",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def test_grid_hit_passes_assembly() -> None:
    """D3 两向·正向：grid 声明参数 design 覆盖命中档（n_pool=3）→ 装配通过。"""
    assembled = assemble(_project({"n_pool": 3.0}), _env())  # type: ignore[misc]
    assert _UNIT in assembled.units


def test_grid_miss_rejected_with_message() -> None:
    """D3 两向·负向：偏离档（n_pool=7 不在 [2,3,4,5,6]）→ 拒且消息四要素齐。"""
    with pytest.raises(InvalidAssemblyError, match="n_pool") as caught:  # type: ignore[misc]
        assemble(_project({"n_pool": 7.0}), _env())  # type: ignore[misc]
    message = str(caught.value)
    for expected in (_UNIT, "n_pool", "7.0", "2.0"):  # unit_id/字段/实际值/档位示例
        assert expected in message


def test_run_enumeration_cass_fifteen_rows() -> None:
    """D2 端到端：CASS 全 grid 15 档——行数/列名/行序/无截断（探针⑤同源）。"""
    from waterprint.contracts.condition import build_condition_set

    outcome = run_enumeration(  # type: ignore[misc]
        _project({}), "municipal_cass", build_condition_set([]), _env()  # type: ignore[misc]
    )
    assert outcome.grid.total == 15
    assert outcome.grid.fields == ("n_pool", "t_cycle")  # field_id 字典序
    assert len(outcome.rows) == 15  # limit 默认取全部（core 侧口径）
    assert outcome.total_feasible == 15  # 无约束=全可行
    assert outcome.truncated is False
    assert outcome.diagnosis is None
    columns = list(outcome.rows.columns)
    assert columns[:2] == ["n_pool", "t_cycle"]  # R4：参数列居首
    for extra in ("margin_min", "nan_flag", "condition_key", "v_plant", "a_pool"):
        assert extra in columns  # 预备/标注/工况列 + dims 结果列
    assert outcome.rows["condition_key"].eq("design").all()  # R3 工况标注
    # R5 行级域拒：t_cycle∈{6,8} 与默认时段 2/1/1 破坏 CA-F13 不变性
    # → 10 行域拒标注（dims 全 NaN），5 行实算（t_cycle=4）
    assert int(outcome.rows["nan_flag"].sum()) == 10
    assert int(outcome.rows["v_plant"].notna().sum()) == 5
    # 行序=grid 序（margin_min 全 NaN → 稳定排序保持原序；n_pool 慢变）
    assert outcome.rows["n_pool"].tolist() == sorted(
        outcome.rows["n_pool"].tolist(), key=float
    )


def test_run_enumeration_sort_and_truncation() -> None:
    """D2 排序/截断：sort_by=v_plant 升序 + limit=5 → 截断显式标注。"""
    from waterprint.contracts.condition import build_condition_set

    options = EnumerationOptions(sort_by="v_plant", ascending=True, limit=5)  # type: ignore[misc]
    outcome = run_enumeration(  # type: ignore[misc]
        _project({}), "municipal_cass", build_condition_set([]), _env(), options  # type: ignore[misc]
    )
    assert outcome.truncated is True
    assert outcome.total_feasible == 15
    assert len(outcome.rows) == 5
    volumes = outcome.rows["v_plant"].dropna().tolist()
    assert volumes == sorted(volumes)  # 升序生效（NaN 行殿后不入前 5）


def test_run_enumeration_unknown_unit_rejected() -> None:
    """D2 单单元语义：unit_id 未命中装配图=InvalidAssemblyError。"""
    from waterprint.contracts.condition import build_condition_set

    with pytest.raises(InvalidAssemblyError, match="no_such_unit"):  # type: ignore[misc]
        run_enumeration(  # type: ignore[misc]
            _project({}), "no_such_unit", build_condition_set([]), _env()  # type: ignore[misc]
        )


def test_export_artifact_calcbook_renders(tmp_path: Path) -> None:
    """D2 导出·正向：calcbook 接 M1b 正门 → 非空 xlsx 字节（模板零标记）。"""
    from openpyxl import Workbook

    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set

    bundle = run_full_calc(_project({}), build_condition_set([]), _env())  # type: ignore[misc]
    template = tmp_path / "tpl.xlsx"
    Workbook().save(template)  # 空白模板（零占位符——渲染即原样）
    payload = export_artifact(  # type: ignore[misc]
        "calcbook", bundle.plant, template, tmp_path / "out.xlsx"
    )
    assert payload[:2] == b"PK"  # xlsx zip 魔数
    assert (tmp_path / "out.xlsx").stat().st_size == len(payload)


@pytest.mark.parametrize("kind,owner", [("audit", "M4"), ("dxf", "M5 site_plan"), ("estimate", "M3")])
def test_export_artifact_not_ready_kinds(kind: str, owner: str) -> None:
    """D2 导出·负向：未就绪 kind 拒且消息注明归属（禁静默空产物）。

    DRAFT 批 D5（2026-08-26）dxf 收口：dxf 单单元出图已就绪（unit_id 必填
    ——缺省拒绝面=全厂总图归 M5 site_plan）；audit/estimate 归属不变。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set

    plant = run_full_calc(
        _project({}), build_condition_set([]), _env()  # type: ignore[misc]
    ).plant
    with pytest.raises(ArtifactKindNotReady, match=owner):  # type: ignore[misc]
        export_artifact(kind, plant, Path("unused.xlsx"), Path("unused_out.xlsx"))  # type: ignore[misc]
