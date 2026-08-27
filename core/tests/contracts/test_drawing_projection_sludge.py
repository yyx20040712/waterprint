"""drawing_projection_sludge 镜像测试：污泥线表主概念（宪法 §6 镜像）。

输入:  SLUDGE_PROJECTIONS 7 条目（M3D2 D1 落表）+聚合正门对照
输出:  7 行计数与 unit_id 前缀自洽/四线 disjoint+聚合并集相等
       /pump-machine 实例语义标签断言（薄镜像——112 键全量五类对账在
       test_drawing_projection.py）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3D2 D5 薄镜像（宪法 §6 镜像规则——M3D1 R1 三镜像先例形态；
#   只守污泥分线文件主概念，不重复主对账面）。
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


def test_sludge_table_has_seven_selfconsistent_entries() -> None:
    """7 条目（键=unit_id 自洽，全部 sludge_ 前缀）。"""
    assert len(SLUDGE_PROJECTIONS) == 7
    assert all(key.startswith("sludge_") for key in SLUDGE_PROJECTIONS)
    assert all(
        entry.unit_id == key for key, entry in SLUDGE_PROJECTIONS.items()
    )


def test_sludge_disjoint_from_other_lines_and_union_is_table() -> None:
    """四线 disjoint+聚合并集==正门表键集（静默覆盖守卫的分线侧镜像；
    M3D3 扩输送线——M-2 指引：并集断言随批扩线集，禁回退子集断言）。
    """
    sludge = frozenset(SLUDGE_PROJECTIONS)
    municipal = frozenset(MUNICIPAL_PROJECTIONS)
    mine = frozenset(MINE_PROJECTIONS)
    conveyance = frozenset(CONVEYANCE_PROJECTIONS)
    assert not sludge & (municipal | mine | conveyance)
    assert sludge | municipal | mine | conveyance == frozenset(PROJECTION_TABLE)


def test_semantic_instance_labels_registered() -> None:
    """D1 两个实例语义单元：bengzhan pump 对（镜像市政提升泵房槽位）/
    tuoshui machine 对（脱水机台数——D2 scene 语义登记）。
    """
    assert dict(
        SLUDGE_PROJECTIONS["sludge_bengzhan"].instance_counts
    ) == {"pump": "n_total", "pump_duty": "n_pump_duty"}
    assert dict(
        SLUDGE_PROJECTIONS["sludge_tuoshui"].instance_counts
    ) == {"machine": "n_machine_total", "machine_duty": "n_machine_duty"}
    # 其余五单元无实例数（衡算/管道/池体/消化类无台数语义键）
    no_counts = (
        "sludge_hebing", "sludge_shusong", "sludge_nongsuo",
        "sludge_xiaohua", "sludge_ganhua",
    )
    for unit_id in no_counts:
        assert not SLUDGE_PROJECTIONS[unit_id].instance_counts, unit_id
