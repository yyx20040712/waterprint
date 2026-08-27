"""drawing_projection_mine 镜像测试：矿井水线表主概念（宪法 §6 镜像）。

输入:  MINE_PROJECTIONS 8 条目（M3D1 D2 落表）+聚合正门对照
输出:  8 行计数与 unit_id 前缀自洽/与市政分线 disjoint/聚合并集相等
       /disk-lamp_row 实例语义标签断言（薄镜像——107 键全量五类对账在
       test_drawing_projection.py）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3D1 R1 薄镜像（总控追加授权 2026-08-27 夜——宪法 §6 镜像
#   规则 CI 强制补齐；只守矿井分线文件主概念，不重复主对账面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.drawing_projection_mine import MINE_PROJECTIONS
from waterprint.contracts.drawing_projection_municipal import (
    MUNICIPAL_PROJECTIONS,
)


def test_mine_table_has_eight_selfconsistent_entries() -> None:
    """8 条目（键=unit_id 自洽，全部 mine_water_ 前缀）。"""
    assert len(MINE_PROJECTIONS) == 8
    assert all(key.startswith("mine_water_") for key in MINE_PROJECTIONS)
    assert all(
        entry.unit_id == key for key, entry in MINE_PROJECTIONS.items()
    )


def test_mine_disjoint_from_municipal_and_union_is_table() -> None:
    """分线 disjoint+聚合并集==正门表键集（静默覆盖守卫的分线侧镜像）。"""
    mine = frozenset(MINE_PROJECTIONS)
    municipal = frozenset(MUNICIPAL_PROJECTIONS)
    assert not mine & municipal
    assert mine | municipal == frozenset(PROJECTION_TABLE)


def test_semantic_instance_labels_registered() -> None:
    """D2 两个实例语义标签：cifenli disk=n_disks/ziwai lamp_row=n_rows。"""
    assert dict(
        MINE_PROJECTIONS["mine_water_cifenli"].instance_counts
    ) == {"disk": "n_disks"}
    assert dict(
        MINE_PROJECTIONS["mine_water_ziwai"].instance_counts
    ) == {"lamp_row": "n_rows"}
    # 其余六单元无实例数（线首注入节点/池体类无台数语义键）
    no_counts = (
        "mine_water_input", "mine_water_tiaojiechi", "mine_water_chenshachi",
        "mine_water_ningjiao", "mine_water_gaomidu", "mine_water_vxinglvchi",
    )
    for unit_id in no_counts:
        assert not MINE_PROJECTIONS[unit_id].instance_counts, unit_id
