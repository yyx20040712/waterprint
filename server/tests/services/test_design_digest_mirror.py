"""design_digest 双胞胎镜像测试：server 摘要 == core 真源逐字节（CP2 D6②）。

输入:  waterprint_server.services.projects.design_digest +
       waterprint.project.content_hash.design_hash（core 真源——测试面
       专用 import，产品码禁直连 waterprint.project 属 import-linter
       D7 契约域，两域互不涉）
输出:  逐字节相等断言（services/projects.py 头注宣称「镜像测试与 core
       真源逐字节对照断言锁死不漂移」——E §三勘察实缺，本件补齐
       清偿头注诚实债；CP2「勾选计入设计哈希」的直接证据锚）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.projects")
design_digest = getattr(_mod, "design_digest")
_core = importlib.import_module("waterprint.project.content_hash")
design_hash = getattr(_core, "design_hash")
_schema = importlib.import_module("waterprint.contracts.project_schema")
DesignState = getattr(_schema, "DesignState")

pytestmark = [
    pytest.mark.skipif(
        None in (design_digest, design_hash, DesignState),
        reason="实现未就绪：design_digest 双胞胎面（server B4/core T7a）",
    ),
]


def test_mirror_default_empty_design_identical() -> None:
    """默认空 DesignState（七字段全空容器——新建项目面）逐字节同。"""
    assert design_digest(DesignState()) == design_hash(DesignState())


def test_mirror_with_constraint_choices_identical() -> None:
    """带约束勾选（CP2 载荷形态 {key:"on"}——D1 复用既有字段）逐字节同
    +勾选参与哈希面（变必变——空档与勾选档摘要互异）。"""
    empty = DesignState()
    checked = DesignState(constraint_choices={"vxinglvchi.v_filter_band": "on"})
    assert design_digest(checked) == design_hash(checked)
    assert design_digest(checked) != design_digest(empty)
    assert design_hash(checked) != design_hash(empty)


def test_mirror_full_design_state_and_change_identical() -> None:
    """七字段多形态逐字节同+变更后（勾选增键）仍同——双胞胎同步漂移面。

    数值出处（R-4/DS-07——宪法 §14 数值出处纪律测试面）：0.4023229167
    =core/tests/golden/golden_data/municipal_34760 的 inlet q_avg_daily
    原样（与 webapp designParams.test 夹具同源）；1.5/200.0 系测试自造
    合理值（assumption_overrides/influent 形态面——非工程断言值）。
    """
    design = DesignState(
        nodes={"inlet": {"kind": "municipal_input", "q_avg_daily": 0.4023229167}},
        edges=[
            {
                "src": {"unit_id": "inlet", "port_id": "out"},
                "dst": {"unit_id": "municipal_cass", "port_id": "in"},
            }
        ],
        constraint_choices={"ganhua.moisture_out_band": "on"},
        checked_units=["design"],
        assumption_overrides={"influent.kz": 1.5},
        influent={"BOD5": 200.0},
        standard_binding={"effluent": "gb18918.level_a"},
    )
    assert design_digest(design) == design_hash(design)
    changed = design.model_copy(
        update={
            "constraint_choices": {
                "ganhua.moisture_out_band": "on",
                "nongsuo.solid_load_band": "on",
            }
        }
    )
    assert design_digest(changed) == design_hash(changed)
    assert design_digest(changed) != design_digest(design)
    assert design_hash(changed) != design_hash(design)
