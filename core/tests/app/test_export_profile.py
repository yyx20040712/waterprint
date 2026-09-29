"""纵断接线批 core 测试（PROFILE2 2026-09-08）：sheet=profile 路由真值表+纵断 DXF 产物。

输入:  inlet→cass 全流程夹具（test_app_enumeration 总图用例同源构造）
输出:  路由真值表断言（纵断合法产出/互斥诚实拒绝/未知值拒绝/
       station_overrides 组合闸）+纵断 DXF 实体面断言（四线图层+工况
       标注+meta 图名承载+批6i 桩号轴/K 标注/站距源注记）。

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
    site_design = SiteDesign(  # 批6i：摆放进入桩号轴消费面（单站=首站
        # 桩号 0；两站布置对拍见批6i 桩号轴专项用例）
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
    assert "K0+000.000" in texts  # 批6i 首站桩号 K 图式标注
    assert any(t.startswith("站距源：") for t in texts)  # 图脚三态注记
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
    assert payload_a and payload_a == payload_b  # 空布置=无 site 等价


def test_profile_station_overrides_route(tmp_path: Path) -> None:
    """批6i 站距覆盖 DSL 路由真值表：首站键/非 profile 传/畸形 DSL 拒；
    空 DSL=未传语义合法产出。"""
    from waterprint.elevation.profile import InvalidProfileError

    plant = _plant()  # 单站纵断（cass=首站无入边——覆盖键必拒）
    # 键位闸=elevation 领域异常直上（site_plan.InvalidSitePlanError
    # 不捕获直上先例——server 侧映射归 exception handler 链）
    with pytest.raises(InvalidProfileError, match="无入边站或未知键"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "x.dxf",
            condition_key="design", sheet="profile",
            station_overrides="municipal_cass=30.5",
        )
    with pytest.raises(ArtifactKindNotReady, match="仅在 sheet='profile'"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "y.dxf",
            condition_key="design", station_overrides="a=30.5",
        )
    for bad in ("no_equals_sign", "unit=", "=30.5", "a=30.5,a=44",
                "a=thirty",
                # k1-W2 数值形态白名单：科学记数/下划线分组/全角拒
                "a=1e3", "a=1_000", "a=１２３", "a=-30.5", "a=.5",
                "a=nan", "a=inf", "a=0", "a=0.000"):
        with pytest.raises(ArtifactKindNotReady):
            export_artifact(  # type: ignore[misc]
                "dxf", plant, Path("unused"), tmp_path / "z.dxf",
                condition_key="design", sheet="profile",
                station_overrides=bad,
            )
    payload = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), tmp_path / "ok.dxf",
        condition_key="design", sheet="profile", station_overrides="  ",
    )
    assert payload and b"AC1032" in payload[:512]  # 空 DSL=未传


def _plant_two_station():
    """两站纵断夹具（inlet→a→b 线性链——站 a/b 有真实推算桩位；
    节点参数与 _plant 同源数值〔golden municipal_34760 算例 1 值〕）。"""
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
                "inlet": {"kind": "municipal_input",
                          "q_avg_daily": 34760.7 / 86400,
                          "kz": 1.4, "CODCR": 400.0, "BOD5": 200.0,
                          "SS": 250.0, "TN": 43.0},
                "municipal_chenshachi": {},
                "municipal_chuchenchi": {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_chenshachi", "port_id": "in"}},
                {"src": {"unit_id": "municipal_chenshachi", "port_id": "out"},
                 "dst": {"unit_id": "municipal_chuchenchi", "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="p2", data_version="p2",
        ),
    )
    return run_full_calc(project, _bcs([]), env).plant  # type: ignore[misc]


def test_profile_chainage_layout_two_station(tmp_path: Path) -> None:
    """批6i 端到端对拍（master plan 验收字面）：金样布置→纵断桩号与
    连线长度一致——桩号 K 标注=布置连线欧氏距离逐段累计（3-4-5 三角
    50 m）。"""
    import ezdxf

    from waterprint.contracts.project_schema import (
        SiteDesign,
        StructurePlacement,
    )

    plant = _plant_two_station()  # 站序：chenshachi→chuchenchi
    site = SiteDesign(structures={
        "municipal_chenshachi": StructurePlacement(x=0.0, y=0.0),
        "municipal_chuchenchi": StructurePlacement(x=30.0, y=40.0),
    })
    out = tmp_path / "profile.dxf"
    export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out,
        site_design=site, condition_key="design", sheet="profile",
    )
    doc = ezdxf.readfile(out)
    texts = [e for e in doc.modelspace().query("TEXT")
             if e.dxf.text.startswith("K0+")]
    # 桩号标注：首站 K0+000.000、次站 K0+050.000（布置连线 50 m 累计）
    assert {e.dxf.text for e in texts} == {"K0+000.000", "K0+050.000"}
    # 手动覆盖例外通道（两源不互斥）：次站边覆盖 44 m → K0+044.000
    out2 = tmp_path / "profile2.dxf"
    export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out2,
        site_design=site, condition_key="design", sheet="profile",
        station_overrides="municipal_chuchenchi=44",
    )
    doc2 = ezdxf.readfile(out2)
    texts2 = [e for e in doc2.modelspace().query("TEXT")
              if e.dxf.text.startswith("K0+")]
    assert {e.dxf.text for e in texts2} == {"K0+000.000", "K0+044.000"}


def test_profile_scale_overrides_bytes(tmp_path: Path) -> None:
    """PD3 正向：h/v 透传覆盖常量——产物字节≠默认比例（缺省=None 结构性
    恒等锚的逆命题：显式定制必改字节）。"""
    plant = _plant()
    default = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), tmp_path / "d.dxf",
        condition_key="design", sheet="profile",
    )
    custom = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), tmp_path / "c.dxf",
        condition_key="design", sheet="profile", h_scale="2000", v_scale="200",
    )
    assert custom and custom != default  # 定制比例必改图面几何（字节面）


def test_profile_scale_invalid_rejected(tmp_path: Path) -> None:
    """PD3 终闸：非法比例拒（strip 后全数字+1≤值≤100000）——空/字母/0/
    负数/越上限五形态（与 server 422 同判定语义；域上限防浮点除法溢出）。"""
    plant = _plant()
    # R 轮（D1-G1-01/A2-G1-01）：Unicode 数字（"②" isdigit 真而 int 炸）与
    # 超长串（≥3.11 int 4300 位上限 ValueError 逃逸）双逃逸面入册。
    for bad in ("", "abc", "0", "-100", "999999", "②", "9" * 5000):
        with pytest.raises(ArtifactKindNotReady, match="比例分母"):
            export_artifact(  # type: ignore[misc]
                "dxf", plant, Path("unused"), tmp_path / "x.dxf",
                condition_key="design", sheet="profile", h_scale=bad,
            )


def test_profile_scale_requires_profile_sheet(tmp_path: Path) -> None:
    """PD3 组合真值表：h/v 仅 sheet=profile 可传——单单元形态传=诚实拒。"""
    plant = _plant()
    with pytest.raises(ArtifactKindNotReady, match="仅在 sheet='profile'"):
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "x.dxf",
            unit_id="municipal_cass", h_scale="2000",
        )


def test_profile_scale_rejected_on_other_kinds(tmp_path: Path) -> None:
    """R 轮（D1-G1-04）：h/v 仅 kind=dxf 可传——ifc/calcbook 分支零消费
    选项面，传=意图错配诚实拒（禁静默吞）。"""
    plant = _plant()
    for kind in ("ifc", "calcbook"):
        with pytest.raises(ArtifactKindNotReady, match="仅 kind='dxf'"):
            export_artifact(  # type: ignore[misc]
                kind, plant, Path("unused"), tmp_path / "x.out", h_scale="2000",
            )
