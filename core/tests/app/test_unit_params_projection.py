"""D1 线感知短名投影测试（M3a1）：矿井水 mine_ 限定键投影+撞键守卫+市政零回退。

输入:  waterprint.app._unit_params（装配期纯函数）+ 撞键面系数视图夹具
输出:  三断言——①mine_water_gaomidu 投影命中 factor.mine_gaomidu.*；
       ②撞键守卫：环境含 factor.gaomidu.*（市政同名键）时矿井水单元
       params 不含该键；③municipal_chuchenchi 投影行为不回退。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import ClassVar

from waterprint.app import _unit_params


class _Coefficients:
    """撞键面夹具：矿井水限定键+市政同名键（0.3.0 既有）并存+市政既有键。

    键值形态逐字取自 data/coefficients 0.3.0/0.5.0 撞键面代表键
    （factor.gaomidu.* 市政 18 键/新 factor.mine_gaomidu.* 键族），
    只保留断言所需最小集——投影按前缀过滤，与库中其余键无关。
    """

    data_version = "0.5.0-probe"

    _ENTRIES: ClassVar[dict[str, float]] = {
        # 矿井水限定键（0.5.0 起的键形态）
        "factor.mine_gaomidu.elevation_loss": 0.5,
        "removal.mine_gaomidu.ss.mod_default": 0.90,
        # 撞键面：市政同名构筑物键与矿井水键并存（0.3.0 既有）
        "factor.gaomidu.surface_load_band.min": 10.0,
        "factor.gaomidu.elevation_loss": 0.8,
        "removal.gaomidu.ss.mod_default": 0.85,
        # 市政既有键（③不回退断言面）
        "factor.chuchenchi.surface_load_band.min": 1.5,
        "removal.chuchenchi.bod5.mod_default": 0.25,
        # 格栅共用键（格栅共用前缀照旧并入各线单元）
        "factor.screen.beta.rect": 2.42,
    }

    def get(self, key: str) -> object:
        return SimpleNamespace(value=self._ENTRIES[key])

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(sorted(k for k in self._ENTRIES if k.startswith(prefix)))

    def require_keys(self, keys: object) -> None:
        return None


def test_mine_water_projection_hits_qualified_keys() -> None:
    """①线感知剥离+mine_ 限定投影：修正前短名=water_gaomidu（单段 split 只
    剥 "mine"）对 factor.water_gaomidu.* 查无键；修正后命中 mine_ 限定键。"""
    params = _unit_params("mine_water_gaomidu", _Coefficients())
    assert set(params) == {
        "factor.mine_gaomidu.elevation_loss",
        "removal.mine_gaomidu.ss.mod_default",
        "factor.screen.beta.rect",  # 格栅共用键照旧并入（四线全前缀剥离不扰共用面）
    }
    assert params["factor.mine_gaomidu.elevation_loss"] == 0.5
    assert params["removal.mine_gaomidu.ss.mod_default"] == 0.90


def test_collision_guard_municipal_keys_not_projected() -> None:
    """②撞键守卫（§14.3 数据键面镜像）：环境存在市政 factor.gaomidu.*/,
    removal.gaomidu.* 时，矿井水高密池 params 不含这些键。"""
    params = _unit_params("mine_water_gaomidu", _Coefficients())
    assert "factor.gaomidu.surface_load_band.min" not in params
    assert "factor.gaomidu.elevation_loss" not in params
    assert "removal.gaomidu.ss.mod_default" not in params


def test_municipal_projection_unchanged() -> None:
    """③市政线不回退：短名剥离=裸短名（split 语义等价），0.1.0~0.4.0 既有
    290 键投影行为零扰动（factor.chuchenchi.*/removal.chuchenchi.* 照旧）。"""
    params = _unit_params("municipal_chuchenchi", _Coefficients())
    assert set(params) == {
        "factor.chuchenchi.surface_load_band.min",
        "removal.chuchenchi.bod5.mod_default",
        "factor.screen.beta.rect",
    }
    assert params["factor.chuchenchi.surface_load_band.min"] == 1.5
    assert params["removal.chuchenchi.bod5.mod_default"] == 0.25
