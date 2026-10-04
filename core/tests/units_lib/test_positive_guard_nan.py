"""FZ-4 批 2026-10-04：30 单元正性守卫 NaN 归因镜像（集中参数化件）。

输入:  units_lib 30 单元包（conveyance 4/mine_water 8/municipal 11/
       sludge 7——`value <= 0` 句式扫描实录全集；chuchenchi 先例已收紧不在此列）
输出:  逐单元注入 NaN 于一个正性守卫参数 → 断言单元级 _validate 即拒：
       InvalidUnitConfig 且消息含「参数 '键'」归因（一致率 100%）

【病灶】旧句式 `if value is None or value <= 0:`（NaN 与任何数比较恒
False → 正性检查穿透）；收紧后 `not value > 0`（chuchenchi L96 先例
逐字同构——NaN>0 为 False → not → True → 拒）。旧句式下 NaN 流入
公式引擎由 GR-02 批量绑定校验以 InvalidFormulaError 拒（无参数名、
registry 层异常族——较单元级守卫晚一层，FZ-4 病灶定义）。

【选择口径】每单元取正性守卫元组中一个具名参数（避开前置枚举/边界
专项检查的键——如 tuoshui 取 dose_pam 而非 machine_type，确保红面
落在正性循环本身）。参数基底=manifest 默认值全量+系数正键投影 1.0
（五单元 _validate 含 _FACTORS_POSITIVE 段——不投影会以「缺系数键」
假红，非本件病灶面；合法值路径不动，FZ-4 只收紧 NaN 面）。
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from waterprint.contracts.manifest import InvalidUnitConfig

# 30 单元 ×（包名，注入参数键）——`grep -rn "value <= 0" units_lib/*/*/compute.py`
# 扫描时点全集（2026-10-04，排除先例 chuchenchi 的 `not value > 0` 形态）。
_NAN_CASES: tuple[tuple[str, str], ...] = (
    # conveyance（4）
    ("waterprint.units_lib.conveyance.jishuijing", "t_well"),
    ("waterprint.units_lib.conveyance.peishuijing", "v"),
    ("waterprint.units_lib.conveyance.jipeishuijing", "t_well"),
    ("waterprint.units_lib.conveyance.peishuiqu", "b_channel"),
    # mine_water（8）
    ("waterprint.units_lib.mine_water.input", "q_avg_daily"),
    ("waterprint.units_lib.mine_water.tiaojiechi", "n"),
    ("waterprint.units_lib.mine_water.chenshachi", "n"),
    ("waterprint.units_lib.mine_water.ningjiao", "n"),
    ("waterprint.units_lib.mine_water.cifenli", "n_units"),
    ("waterprint.units_lib.mine_water.gaomidu", "n"),
    ("waterprint.units_lib.mine_water.vxinglvchi", "v_filter"),
    ("waterprint.units_lib.mine_water.ziwai", "n"),
    # municipal（11）
    ("waterprint.units_lib.municipal.cugeshan", "n"),
    ("waterprint.units_lib.municipal.xigeshan", "n"),
    ("waterprint.units_lib.municipal.chenshachi", "n"),
    ("waterprint.units_lib.municipal.tiaojiechi", "n"),
    ("waterprint.units_lib.municipal.aao", "n"),
    ("waterprint.units_lib.municipal.cass", "n_pool"),
    ("waterprint.units_lib.municipal.gaomidu", "n"),
    ("waterprint.units_lib.municipal.vxinglvchi", "n"),
    ("waterprint.units_lib.municipal.ziwai", "n_channel"),
    ("waterprint.units_lib.municipal.erchunchi", "n"),
    ("waterprint.units_lib.municipal.wushui_tisheng", "h_static"),
    # sludge（7）
    ("waterprint.units_lib.sludge.hebing", "ds_primary"),
    ("waterprint.units_lib.sludge.shusong", "v_press"),
    ("waterprint.units_lib.sludge.bengzhan", "n_standby"),
    ("waterprint.units_lib.sludge.nongsuo", "q_solid"),
    ("waterprint.units_lib.sludge.xiaohua", "t_digest"),
    ("waterprint.units_lib.sludge.tuoshui", "dose_pam"),
    ("waterprint.units_lib.sludge.ganhua", "t_op"),
)


def _case_ids() -> list[str]:
    return [f"{pkg.rsplit('.', 1)[-1]}-{key}" for pkg, key in _NAN_CASES]


@pytest.mark.parametrize(
    ("package", "key"),
    _NAN_CASES,
    ids=_case_ids(),
)
def test_positive_guard_rejects_nan_with_param_name(package: str, key: str) -> None:
    """NaN 入正性守卫参数 → 单元级 InvalidUnitConfig 且消息含参数名。

    旧句式 `value <= 0` 下 NaN 比较恒 False 穿透（本用例红面）；
    `not value > 0` 收紧后单元级即拒——归因一致率 100%（30/30）。"""
    pkg = importlib.import_module(package)
    compute = importlib.import_module(f"{package}.compute")
    params = {spec.field_id: spec.default for spec in pkg.manifest.params}
    # 系数正键投影（五单元 _validate 含系数段——缺键「缺系数键」假红规避）
    for factor_key in getattr(compute, "_FACTORS_POSITIVE", ()):
        params.setdefault(factor_key, 1.0)
    params[key] = float("nan")
    validate = compute._validate  # noqa: SLF001  # 守卫面直调（FZ-4 归因镜像——私有 _validate 纯函数）
    takes_unit_id = "unit_id" in inspect.signature(validate).parameters
    with pytest.raises(InvalidUnitConfig, match=rf"参数 {key!r}") as excinfo:
        if takes_unit_id:
            validate(params, pkg.manifest.unit_id)
        else:
            validate(params)
    assert str(pkg.manifest.unit_id) in str(excinfo.value)


def test_positive_guard_nan_case_count_is_thirty() -> None:
    """面锚：扫描全集 30 单元（30 文件 `value <= 0` 句式实录数）。"""
    assert len(_NAN_CASES) == 30
