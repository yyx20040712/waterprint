"""纵断接线批 core 测试（PROFILE2 2026-09-08）：sheet=profile 路由真值表+纵断 DXF 产物。

输入:  inlet→cass 全流程夹具（test_app_enumeration 总图用例同源构造）
输出:  路由真值表五组合断言（纵断合法产出/互斥诚实拒绝/未知值拒绝/
       site_design 零消费）+纵断 DXF 实体面断言（四线图层+工况标注+
       meta 图名承载）。

规格（briefs/task-PROFILE2-plan.md PD1/PD8）：
- 真值表：unit_id 有值+sheet=profile=拒（语义互斥）；unit_id 缺省+
  sheet=profile=纵断 DXF（site_design 零消费——传与否皆纵断）；
  既有三组合（单单元/总图/诚实拒绝）字节恒等由既有用例守卫；
- 实体面：四线（LAYER_ELEV×2+LAYER_POOL+LAYER_PIPE）+工况标注
  condition_key 文本+meta.title=「高程纵断图」（DrawingMeta 承载，
  单单元图 meta.title=unit_id 先例同构）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint.app_enumeration import ArtifactKindNotReady, export_artifact

_DATA = Path(__file__).resolve().parents[2].parent / "data" / "coefficients"


def _plant() -> object:
    """inlet→cass 全流程夹具（数值出处=tests/app/test_app_enumeration.py
    总图用例逐字同源——golden municipal_34760 算例 1 值：q=34760.7 m³/d/
    kz=1.4/COD=400/BOD=200/SS=250/TN=43；P2A2-5 出处注记）。"""
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set as _bcs
    from waterprint.contracts.project_schema import (
        DesignState,
        Metadata,
        ProjectFile,
    )
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="p2",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {"kind": "municipal_input", "q_avg_daily": 34760.7 / 86400,
                          "kz": 1.4, "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                          "TN": 43.0},
                "municipal_cass": {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="p2", data_version="p2",
        ),
    )
    return run_full_calc(project, _bcs([]), env).plant  # type: ignore[misc]


def test_profile_route_sheet_value_rejected(tmp_path: Path) -> None:
    """真值表：未知 sheet 取值诚实拒绝（白名单纪律——值域仅 'profile'）。"""
    plant = _plant()
    with pytest.raises(ArtifactKindNotReady, match="未知 sheet 取值 'elevation'"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "x.dxf", sheet="elevation",
        )


def test_profile_route_mutex_with_unit_id(tmp_path: Path) -> None:
    """真值表：unit_id+sheet=profile 互斥诚实拒绝（禁静默忽略任一意图）。"""
    plant = _plant()
    with pytest.raises(ArtifactKindNotReady, match="互斥"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "x.dxf",
            unit_id="municipal_cass", sheet="profile",
        )


def test_profile_route_unknown_condition_rejected(tmp_path: Path) -> None:
    """真值表：纵断工况校验共享 _export_dxf 入口 R1-1（未知工况拒）。"""
    plant = _plant()
    with pytest.raises(ArtifactKindNotReady, match="不在结果"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "x.dxf",
            condition_key="nonexistent", sheet="profile",
        )


def test_profile_dxf_entities_and_meta(tmp_path: Path) -> None:
    """纵断正向：四线图层+工况标注+meta 图名承载（site_design 零消费）。"""
    import ezdxf

    from waterprint.contracts.project_schema import (
        SiteDesign,
        StructurePlacement,
    )

    plant = _plant()
    out = tmp_path / "profile.dxf"
    site_design = SiteDesign(  # 传入亦零消费（PD1 真值表——纵断=流程站位非摆放）
        structures={"municipal_cass": StructurePlacement(x=5.0, y=5.0)}
    )
    payload = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out,
        site_design=site_design, condition_key="design", sheet="profile",
    )
    assert payload  # 禁静默空产物（UF-33）
    assert out.read_bytes() == payload  # 落盘与返回一致
    assert b"AC1032" in payload[:512]  # DXF R2018 头魔面
    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    from collections import Counter

    from waterprint.drafting.styles import LAYER_ELEV, LAYER_PIPE, LAYER_POOL
    line_counts = Counter(e.dxf.layer for e in msp.query("LWPOLYLINE"))
    # 四线齐备按图层计数锁死（P2A2-2——集合断言 LAYER_ELEV 单线假绿盲区）：
    # 地面+水面=LAYER_ELEV 两条、池底=LAYER_POOL、管底=LAYER_PIPE。
    assert line_counts[LAYER_ELEV] >= 2
    assert line_counts[LAYER_POOL] >= 1 and line_counts[LAYER_PIPE] >= 1
    texts = {e.dxf.text for e in msp.query("TEXT")}
    assert "condition=design" in texts  # 工况标注（profile_sheet R5）
    assert "municipal_cass" in texts  # 站名（unit_id 原文——catalog 同款先例）
    # meta 承载精确断言（D1 G1-01——write_dxf L278 写 $PROJECTNAME=meta.title
    # 实证在册；OR 兜底断言拆句钉死唯一承载路径）。
    assert doc.header["$PROJECTNAME"] == "高程纵断图"


def test_profile_dxf_site_design_optional(tmp_path: Path) -> None:
    """真值表：unit_id 缺省+sheet=profile+无 site_design=纵断合法（非总图拒绝路径）。"""
    from waterprint.contracts.project_schema import SiteDesign

    plant = _plant()
    out_a = tmp_path / "a.dxf"
    out_b = tmp_path / "b.dxf"
    payload_a = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out_a,
        condition_key="design", sheet="profile",
    )
    payload_b = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out_b,
        condition_key="design", sheet="profile",
        site_design=SiteDesign(structures={}),
    )
    assert payload_a and payload_a == payload_b  # site_design 零消费=字节恒等
