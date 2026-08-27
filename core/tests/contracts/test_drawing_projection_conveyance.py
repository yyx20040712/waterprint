"""drawing_projection_conveyance 镜像测试：输送线表主概念（宪法 §6 镜像）。

输入:  CONVEYANCE_PROJECTIONS 4 条目（M3D3 D1 落表）+聚合正门对照
输出:  4 行计数与 unit_id 前缀自洽/四线 disjoint+聚合并集相等
       /peishuiqu water_depth 唯一语义键与三井 cylinder 槽位断言
       （薄镜像——39 键全量五类对账在 test_drawing_projection.py）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3D3 D4 薄镜像（宪法 §6 镜像规则——M3D1 R1/M3D2 D5 三镜像
#   先例形态；只守输送分线文件主概念，不重复主对账面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.drawing_projection_conveyance import (
    CONVEYANCE_PROJECTIONS,
)
from waterprint.contracts.drawing_projection_mine import MINE_PROJECTIONS
from waterprint.contracts.drawing_projection_municipal import (
    MUNICIPAL_PROJECTIONS,
)
from waterprint.contracts.drawing_projection_sludge import SLUDGE_PROJECTIONS


def test_conveyance_table_has_four_selfconsistent_entries() -> None:
    """4 条目（键=unit_id 自洽，全部 conveyance_ 前缀）。"""
    assert len(CONVEYANCE_PROJECTIONS) == 4
    assert all(key.startswith("conveyance_") for key in CONVEYANCE_PROJECTIONS)
    assert all(
        entry.unit_id == key for key, entry in CONVEYANCE_PROJECTIONS.items()
    )


def test_conveyance_disjoint_from_other_lines_and_union_is_table() -> None:
    """四线 disjoint+聚合并集==正门表键集（静默覆盖守卫的分线侧镜像）。"""
    conveyance = frozenset(CONVEYANCE_PROJECTIONS)
    municipal = frozenset(MUNICIPAL_PROJECTIONS)
    mine = frozenset(MINE_PROJECTIONS)
    sludge = frozenset(SLUDGE_PROJECTIONS)
    assert not conveyance & (municipal | mine | sludge)
    assert conveyance | municipal | mine | sludge == frozenset(PROJECTION_TABLE)


def test_peishuiqu_water_depth_semantic_and_well_cylinder_slots() -> None:
    """D1 语义断言：peishuiqu=输送线唯一 water_depth 语义键（h_water）
    且无 plan/primitive 半槽（渠长是参数——无总长单键，ziwai 同裁）；
    三井 cylinder diameter+depth 两槽全触发；四单元全无实例数
    （穿流单元无台数语义键——n 是分流口数非设备台数）。
    """
    water_depth_units = {
        unit_id for unit_id, entry in CONVEYANCE_PROJECTIONS.items()
        if "water_depth" in entry.section_keys
    }
    assert water_depth_units == {"conveyance_peishuiqu"}
    peishuiqu = CONVEYANCE_PROJECTIONS["conveyance_peishuiqu"]
    assert dict(peishuiqu.section_keys) == {
        "water_depth": "h_water", "pool_depth": "h_total",
    }
    assert not peishuiqu.plan_keys
    assert not peishuiqu.primitive_dims
    for unit_id in (
        "conveyance_jishuijing", "conveyance_peishuijing",
        "conveyance_jipeishuijing",
    ):
        entry = CONVEYANCE_PROJECTIONS[unit_id]
        assert set(entry.primitive_dims) == {"diameter", "depth"}, unit_id
        assert not entry.instance_counts, unit_id
    assert not peishuiqu.instance_counts
