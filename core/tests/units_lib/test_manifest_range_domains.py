"""FZ-3 批 2026-10-04：硬物理域参数 manifest range 声明（(0,1) 双侧有界型）。

输入:  sludge_hebing manifest（p_primary/p_bio/p_chem 含水率——计算期
       _validate 开区间 (0,1) 硬物理域守卫，fuzz 点名三项；扫描全集余者
       nongsuo p_out/ganhua p_out/tuoshui p_cake/xiaohua eta_vs 均已有
       range 声明不在补面）+ executor 声明带面（importlib getattr 先例）
输出:  ①range 键存在断言（每参数一键——闭区间 [0,1] 近似声明）；
       ②0.0/1.0 端点计算期拒保持（第二道防线不迁移——开区间语义
       端点行为归计算期守卫）；③GR-06 golden 合法值（0.96/0.994/0.98）
       带内零警告+域外值告警归因（声明激活面）。

【声明语义】range=[0,1] 为计算期开区间守卫 (0,1) 的闭区间近似投影
（同值抄录非新数值）；应用通道 params_guard face④ 对闭区间外明显值
（-0.5/2.0）提前 422 拒（终态同拒语义、消息面变化如实记档）；
0.0/1.0 端点应用通道放行 → 计算期 InvalidUnitConfig 拒（双态）。
"""

from __future__ import annotations

import importlib

import pytest

from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.units_lib.sludge.hebing import (
    manifest as hebing_manifest,  # UnitManifest 对象（包白名单导出）
)
from waterprint.units_lib.sludge.hebing.compute import _validate as _hebing_validate

# (0,1) 型双侧有界硬物理域参数全集（扫描实录 2026-10-04——五单元六键
# 中唯一无 range 声明面；计算期守卫 not 0 < value < 1 同值投影）
_MOISTURE_KEYS = ("p_primary", "p_bio", "p_chem")
# golden 市政 34,760 案例三股实值（docs/norms/sludge_hebing.md 主算例逐字）
_GOLDEN_VALUES = {"p_primary": 0.96, "p_bio": 0.994, "p_chem": 0.98}

_bands = getattr(
    importlib.import_module("waterprint.graph.executor"), "_range_band_warnings", None
)


def _specs() -> dict[str, object]:
    return {spec.field_id: spec for spec in hebing_manifest.params}


@pytest.mark.parametrize("key", _MOISTURE_KEYS)
def test_hebing_moisture_params_declare_unit_interval_range(key: str) -> None:
    """①range 键存在断言：含水率三键声明 [0,1] 闭区间近似（FZ-3 补面）。"""
    spec = _specs()[key]
    assert spec.range == (0.0, 1.0), (
        f"{key} range 声明缺失或非 [0,1] 物理域投影：得到 {spec.range!r}"
    )


@pytest.mark.parametrize("key", _MOISTURE_KEYS)
def test_hebing_moisture_endpoints_rejected_at_compute_time(key: str) -> None:
    """②端点语义不迁移：0.0/1.0 计算期守卫拒（开域 (0,1)——闭边界使
    干基反解除零；InvalidUnitConfig 含参数名，第二道防线保持）。"""
    params = {
        spec.field_id: spec.default for spec in hebing_manifest.params
    }
    params.update(_GOLDEN_VALUES)
    for endpoint in (0.0, 1.0):
        bad = dict(params)
        bad[key] = endpoint
        with pytest.raises(InvalidUnitConfig, match=rf"参数 {key!r}"):
            _hebing_validate(bad)


@pytest.mark.skipif(_bands is None, reason="executor 声明带面未就绪（FZ-2 批）")
def test_hebing_moisture_golden_values_in_band_zero_warnings() -> None:
    """③GR-06 golden 零漂移：合法值 0.96/0.994/0.98 ∈ [0,1] 带内零警告
    （A/B serialize 恒等锚——声明激活前后合法值路径无新告警）。"""
    specs = tuple(
        spec for spec in hebing_manifest.params
        if spec.field_id in _MOISTURE_KEYS
    )
    assert len(specs) == 3
    assert _bands(specs, _GOLDEN_VALUES, set()) == ()


@pytest.mark.skipif(_bands is None, reason="executor 声明带面未就绪（FZ-2 批）")
def test_hebing_moisture_out_of_band_warns_with_param_key() -> None:
    """③对偶面：域外值（-0.5 越下界/2.0 越上界）GR-06 告警逐键归因
    （声明激活后中央带告警对硬物理域参数可用——FZ-3 可行域引导盲区收口）。"""
    specs = tuple(
        spec for spec in hebing_manifest.params
        if spec.field_id in _MOISTURE_KEYS
    )
    out = _bands(specs, {"p_primary": -0.5, "p_bio": 2.0, "p_chem": 0.98}, set())
    assert {w.param_key for w in out} == {"p_primary", "p_bio"}
