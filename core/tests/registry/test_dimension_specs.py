"""dimension_specs 镜像测试：数据形态契约（B3-R11 裁定件）。

输入:  waterprint.registry.dimension_specs 数据面（DIMENSION_SPECS）
输出:  转写安全钉面（每项恰五元组且全 str——field_id/dim/unit/i18n_key/
       category 位置序；序列非空。错元数/错型必在此显式红，登记守卫前哨）
"""

from __future__ import annotations

from waterprint.registry.dimension_specs import DIMENSION_SPECS


def test_data_contract() -> None:
    """纯五元组序列契约：全组展平后逐项恰五元组、全 str、组数>0（B3 笔①）。"""
    assert len(DIMENSION_SPECS) > 0
    for item in DIMENSION_SPECS:
        assert isinstance(item, tuple)
        assert len(item) == 5
        assert all(isinstance(part, str) for part in item)
