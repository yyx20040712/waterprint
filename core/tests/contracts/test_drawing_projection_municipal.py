"""drawing_projection_municipal 镜像测试：市政线表主概念（宪法 §6 镜像）。

输入:  MUNICIPAL_PROJECTIONS 13 条目+共享常量（M3D1 D1 逐字迁移）
输出:  13 行计数与 unit_id 自洽/键前缀/cugeshan-xigeshan 共享常量一致
       （同构不合并——两行各自声明）断言（薄镜像——全量五类对账在
       test_drawing_projection.py）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3D1 R1 薄镜像（总控追加授权 2026-08-27 夜——宪法 §6 镜像
#   规则 CI 强制补齐；只守市政分线文件主概念，不重复主对账面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint.contracts.drawing_projection_municipal import (
    MUNICIPAL_PROJECTIONS,
)


def test_municipal_table_has_thirteen_selfconsistent_entries() -> None:
    """13 条目（键=unit_id 自洽，全部 municipal_ 前缀）。"""
    assert len(MUNICIPAL_PROJECTIONS) == 13
    assert all(key.startswith("municipal_") for key in MUNICIPAL_PROJECTIONS)
    assert all(
        entry.unit_id == key for key, entry in MUNICIPAL_PROJECTIONS.items()
    )


def test_screen_twins_share_constants_but_stay_two_rows() -> None:
    """cugeshan/xigeshan 同构不合并：两行各自在表，键面与共享常量一致。"""
    cu = MUNICIPAL_PROJECTIONS["municipal_cugeshan"]
    xi = MUNICIPAL_PROJECTIONS["municipal_xigeshan"]
    # 同构键面（共享 _SCREEN_NON_DRAWN/_SCREEN_DIM_OF——两行声明不合并）
    assert cu.non_drawn == xi.non_drawn
    assert dict(cu.dim_of) == dict(xi.dim_of)
    assert dict(cu.plan_keys) == dict(xi.plan_keys)
    assert dict(cu.section_keys) == dict(xi.section_keys)
    assert dict(cu.primitive_dims) == dict(xi.primitive_dims)
    # 两行各自独立声明（unit_id 各归其位——非同一对象复用）
    assert cu is not xi
    assert cu.unit_id == "municipal_cugeshan"
    assert xi.unit_id == "municipal_xigeshan"


def test_screen_dim_of_matches_screen_non_drawn_keys() -> None:
    """格栅共享量纲列覆盖其共享校核键集（共享常量互洽）。"""
    for unit_id in ("municipal_cugeshan", "municipal_xigeshan"):
        entry = MUNICIPAL_PROJECTIONS[unit_id]
        assert set(entry.non_drawn) <= set(entry.dim_of), unit_id
        # 共享常量 14 键全量在量纲列（B/B1/H/L/h1/mech_clean/n_gap/q/
        # ds_slag/v1_checked/v_checked/v_concrete/w_slag/xi）
        assert set(entry.dim_of) == entry.drawn_keys() | set(entry.non_drawn)
