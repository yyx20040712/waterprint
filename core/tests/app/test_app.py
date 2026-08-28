"""app 镜像测试：用例编排（装配失败清单/双跑 diff=0/三元组传播——golden 承载）。

输入:  waterprint.app 公开符号
输出:  编排契约断言
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import ClassVar

import pytest

_mod = importlib.import_module("waterprint.app")
run_full_calc = getattr(_mod, "run_full_calc", None)
assemble = getattr(_mod, "assemble", None)

pytestmark = pytest.mark.skipif(
    None in (run_full_calc, assemble),
    reason="实现未就绪：waterprint.app（M1 三单元切片）",
)


def test_entrypoints_frozen() -> None:
    """入口冻结：assemble(project, env) / run_full_calc(project, conditions, env)。"""
    assert callable(assemble)
    assert callable(run_full_calc)


class _Coefficients:
    """系数视图夹具：键值逐字取自 data/coefficients 0.1.0（factors/
    removal_rates yaml），供 app._unit_params 投影（D4 通道）。"""

    data_version = "m1b"

    _ENTRIES: ClassVar[dict[str, float]] = {
        # factors.yaml —— 格栅共用（粗/细）
        "factor.screen.beta.rect": 2.42,
        "factor.screen.beta.semicircle": 1.97,
        "factor.screen.beta.circle": 1.83,
        "factor.screen.headloss.k": 3.0,
        "factor.screen.superheight": 0.3,
        "factor.screen.trough_width_margin": 0.2,
        "factor.screen.trough_length.l3_fixed": 1.0,
        "factor.screen.trough_length.l4_fixed": 0.5,
        "factor.screen.trough_length.drop_constant": 0.2,
        "factor.screen.slag.moisture": 0.80,
        "factor.screen.mech_clean_threshold": 0.2,
        "factor.screen.velocity_band.v.min": 0.6,
        "factor.screen.velocity_band.v.max": 1.0,
        "factor.screen.velocity_band.v1.min": 0.4,
        "factor.screen.velocity_band.v1.max": 0.9,
        "factor.screen.wall_thickness_coef": 0.3,
        # factors.yaml —— 单元键
        "factor.cugeshan.w1_slag": 0.02,
        "factor.xigeshan.w1_slag": 0.08,
        "factor.chenshachi.sand_yield_x": 30.0,
        "factor.chenshachi.hopper.safety": 1.5,
        "factor.chenshachi.buffer_h3": 0.5,
        "factor.chenshachi.superheight": 0.3,
        "factor.chenshachi.grit.moisture": 0.60,
        "factor.chenshachi.grit.density": 1600.0,
        "factor.chenshachi.channel.straight_mult": 7.0,
        "factor.chenshachi.channel.straight_min": 4.5,
        "factor.chenshachi.channel.outlet_mult": 2.0,
        "factor.chenshachi.surface_load_band.min": 150.0,
        "factor.chenshachi.surface_load_band.max": 200.0,
        "factor.chenshachi.retention_band.min": 25.0,
        "factor.chenshachi.retention_band.max": 60.0,
        "factor.chenshachi.h2_band.min": 1.0,
        "factor.chenshachi.h2_band.max": 2.0,
        "factor.chenshachi.ratio_dh2_band.min": 2.0,
        "factor.chenshachi.ratio_dh2_band.max": 2.5,
        "factor.chenshachi.wall_thickness_coef": 0.4,
        "factor.chenshachi.hopper_upper_ratio": 0.5,
        # removal_rates.yaml —— mod_default 档
        "removal.cugeshan.bod5.mod_default": 0.05,
        "removal.cugeshan.cod.mod_default": 0.05,
        "removal.cugeshan.ss.mod_default": 0.05,
        "removal.xigeshan.bod5.mod_default": 0.08,
        "removal.xigeshan.cod.mod_default": 0.08,
        "removal.xigeshan.ss.mod_default": 0.08,
        "removal.chenshachi.bod5.mod_default": 0.05,
        "removal.chenshachi.cod.mod_default": 0.05,
        "removal.chenshachi.ss.mod_default": 0.10,
    }

    def get(self, key: str) -> object:
        return SimpleNamespace(value=self._ENTRIES[key])

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(sorted(k for k in self._ENTRIES if k.startswith(prefix)))

    def require_keys(self, keys: object) -> None:
        return None


def _project() -> object:
    """三真实单元链载体：municipal_input（三表流量口径）→粗格栅→细格栅→沉砂池。"""
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,  # 三表：34760.7 m³/d
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                },
                "municipal_cugeshan": {},
                "municipal_xigeshan": {},
                "municipal_chenshachi": {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cugeshan", "port_id": "in"},
                },
                {
                    "src": {"unit_id": "municipal_cugeshan", "port_id": "out"},
                    "dst": {"unit_id": "municipal_xigeshan", "port_id": "in"},
                },
                {
                    "src": {"unit_id": "municipal_xigeshan", "port_id": "out"},
                    "dst": {"unit_id": "municipal_chenshachi", "port_id": "in"},
                },
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m1b",
            data_version="m1b",
        ),
    )


def _env() -> object:
    from waterprint.contracts.run_env import RunEnv

    return RunEnv(
        engine_version="m1b",
        data_version="m1b",
        assumptions={},
        coefficients=_Coefficients(),
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def test_double_run_byte_identical_wiring() -> None:
    """R3 接线断言：同 (project, conditions, env) 双跑序列化字节相同。

    与 golden 端到端互补：golden 给数值对照，本断言给可复算性。
    载体=M1b 升级的三真实单元链（municipal_input[34760.7 m³/d、Kz=1.4，
    三表流量口径]→municipal_cugeshan→municipal_xigeshan→municipal_
    chenshachi，后三者经 discover_units 注册表装配无 kind 键）；断言=
    双跑 serialize 字节同 + 三真实 UNIT_ID 在册 + 三表量级数值对照
    （cugeshan w_slag≈0.6952 / xigeshan w_slag≈2.7809 / chenshachi
    ds_grit≈667.4，docs/norms 三表签字值，approx 合理容差）。
    """
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.result_schema import serialize
    from waterprint.units_lib import discover_units

    project = _project()
    env = _env()
    conditions = build_condition_set([])
    assembled = assemble(project, env)  # type: ignore[misc]
    assert set(assembled.units) == {
        "inlet",
        "municipal_cugeshan",
        "municipal_xigeshan",
        "municipal_chenshachi",
    }
    assert {"municipal_cugeshan", "municipal_xigeshan", "municipal_chenshachi"} <= set(
        discover_units()
    )  # 三真实 UNIT_ID 在册（替换原三内置 id 断言）
    first = run_full_calc(project, conditions, env)  # type: ignore[misc]
    second = run_full_calc(project, conditions, env)  # type: ignore[misc]
    assert serialize(first.plant) == serialize(second.plant)  # 含 trace 双跑字节同
    assert first.repro == second.repro
    assert first.repro.design_hash
    # 三表量级数值对照（design 工况 dims）
    dims = {
        unit_id: first.plant.conditions["design"][unit_id].dims
        for unit_id in ("municipal_cugeshan", "municipal_xigeshan", "municipal_chenshachi")
    }
    assert dims["municipal_cugeshan"]["w_slag"] == pytest.approx(0.6952, abs=1e-4)
    assert dims["municipal_xigeshan"]["w_slag"] == pytest.approx(2.7809, abs=1e-4)
    assert dims["municipal_chenshachi"]["ds_grit"] == pytest.approx(667.4, abs=0.1)


def test_scene_reexports_on_facade() -> None:
    """FE1 接线断言：app 正门再导出 build_scene/SceneGraph（server scene 端点唯一取用口）。

    geometry 包正门同步补类型面（SceneGraph/Node/Primitive/SCENE_VERSION——
    前端渲染器 SCENE_VERSION 校验的取用通道）；server 侧经 waterprint.app
    消费（UF-33 单入口铁律，本批 scene 数据通道前提）。
    """
    from waterprint import geometry

    for symbol in ("build_scene", "SceneGraph"):
        assert hasattr(_mod, symbol), f"waterprint.app 缺 scene 再导出 {symbol!r}"
    for symbol in ("build_scene", "SceneGraph", "Node", "Primitive", "SCENE_VERSION"):
        assert hasattr(geometry, symbol), f"waterprint.geometry 缺正门导出 {symbol!r}"
