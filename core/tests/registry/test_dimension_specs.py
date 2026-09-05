"""dimension_specs 镜像测试：数据形态契约（B3-R11 裁定件；R 轮 G1-03 强化）。

输入:  waterprint.registry.dimension_specs 数据面（DIMENSION_SPECS）
输出:  转写安全钉面（每项恰五元组且全 str——field_id/dim/unit/i18n_key/
       category 位置序；总数=128 冻结计数+field_id 唯一性。错元数/错型/
       unit·category 互换/整组误删必在此显式红，登记守卫前哨）
"""

from __future__ import annotations

from waterprint.registry.dimension_specs import DIMENSION_SPECS

# 冻结计数（R 轮 G1-03 采纳）：pool_length 1+M1a 18+M2a2 16+M2b2 23+
# M2c 11+M3a2 16+M3a3 16+M3b2 27=128——后续批次增字段须过锁改此锚
# （[HUMAN-LOCK] 摩擦即设计：数据面增删显式化）。
_SPEC_COUNT = 1 + 18 + 16 + 23 + 11 + 16 + 16 + 27


def test_data_contract() -> None:
    """纯五元组序列契约：恰 128 项+逐项五元组全 str+field_id 唯一（B3 笔①+R 轮）。"""
    assert len(DIMENSION_SPECS) == _SPEC_COUNT
    field_ids: set[str] = set()
    for item in DIMENSION_SPECS:
        assert isinstance(item, tuple)
        assert len(item) == 5
        assert all(isinstance(part, str) for part in item)
        field_ids.add(item[0])
    assert len(field_ids) == _SPEC_COUNT  # field_id 唯一（R3 字段重复登记守卫前哨）
