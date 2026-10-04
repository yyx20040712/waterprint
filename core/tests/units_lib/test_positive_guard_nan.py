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


# ── 1A4 批 T2 顺手清偿：相邻同病 NaN 面八处（1a7 g1-dispositions §二
#    W1 表挂账扩列四类——aao 差值比较/hebing 入流工程量/bashi 变量名不
#    匹配/五单元 _factor 内联；句式收紧=FZ-4 `not x > 0` 同款机械面）────


def _params_of(package: str) -> dict[str, float]:
    """manifest 默认参数基底+系数正键投影 1.0（上方 30 例同款）。"""
    import importlib

    pkg = importlib.import_module(package)
    compute = importlib.import_module(f"{package}.compute")
    params = {spec.field_id: spec.default for spec in pkg.manifest.params}
    for factor_key in getattr(compute, "_FACTORS_POSITIVE", ()):
        params.setdefault(factor_key, 1.0)
    return params


# 五单元 _factor 内联守卫（#4~#8——NaN 系数经 _factor 路径：float(nan)
# 直返→`<=0` 恒 False 穿透旧句式/`not >0` 拒；消息含系数键名）。
_NAN_FACTOR_CASES: tuple[tuple[str, str], ...] = (
    ("waterprint.units_lib.mine_water.tiaojiechi",
     "factor.mine_tiaojiechi.stir.power_density"),
    ("waterprint.units_lib.municipal.gaomidu", "factor.gaomidu.g_mix"),
    ("waterprint.units_lib.municipal.tiaojiechi",
     "factor.tiaojiechi.stir.power_density"),
    ("waterprint.units_lib.municipal.vxinglvchi",
     "factor.vxinglvchi.selfuse_coef"),
    ("waterprint.units_lib.municipal.ziwai", "factor.ziwai.q_per_lamp"),
)


@pytest.mark.parametrize(
    ("package", "factor_key"),
    _NAN_FACTOR_CASES,
    ids=[f"{p.rsplit('.', 1)[-1]}-{k.rsplit('.', 1)[-1]}"
         for p, k in _NAN_FACTOR_CASES],
)
def test_factor_guard_rejects_nan_with_key_name(
    package: str, factor_key: str
) -> None:
    """NaN 系数键入 _FACTORS_POSITIVE 守卫 → InvalidUnitConfig 消息含键名
    （归因一致率 8/8——旧句式 `_factor(...) <= 0` 下 NaN 比较恒 False
    穿透＝本用例红面；`not _factor(...) > 0` 收紧后即拒）。"""
    import importlib
    import inspect

    pkg = importlib.import_module(package)
    compute = importlib.import_module(f"{package}.compute")
    assert factor_key in getattr(compute, "_FACTORS_POSITIVE", ())  # 键在册锚
    params = _params_of(package)
    params[factor_key] = float("nan")
    validate = compute._validate  # noqa: SLF001  # 守卫面直调（纯函数）
    takes_unit_id = "unit_id" in inspect.signature(validate).parameters
    with pytest.raises(
        InvalidUnitConfig, match=rf"系数键 {factor_key!r}"
    ) as excinfo:
        if takes_unit_id:
            validate(params, pkg.manifest.unit_id)
        else:
            validate(params)
    assert str(pkg.manifest.unit_id) in str(excinfo.value)


def test_aao_delta_n_guard_rejects_nan_upstream() -> None:
    """#1 aao 差值比较：NaN tn_in 入流上游值 →`not (tn_in - tn_eff) > 0`
    拒（消息含 delta_n/TN_in/tn_eff 归因；旧句式 NaN 穿透=红面——参数面
    tn_eff 已由 _PARAMS_POSITIVE 先拒，NaN 可达面=入流上游裸参直调）。"""
    import inspect
    from typing import Any

    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.flow import make_flow
    from waterprint.contracts.quantity import Quantity
    from waterprint.contracts.unit_api import UnitContext
    from waterprint.units_lib.municipal import aao as aao_pkg
    from waterprint.units_lib.municipal.aao import compute as aao_compute

    params = _params_of("waterprint.units_lib.municipal.aao")
    ctx = UnitContext(
        unit_id=aao_pkg.manifest.unit_id, inflows={}, inqualities={},
        params=params, condition=build_condition_set([]).iter_all().__next__(),
        assumptions={}, trace=None)
    flow = make_flow(Quantity(100.0, "m3/d"), 1.5)
    volumes = aao_compute._volumes  # noqa: SLF001  # 守卫面直调（AO-F1~F5 段）
    assert "tn_in" in inspect.signature(volumes).parameters  # 裸参注入面锚
    with pytest.raises(InvalidUnitConfig, match="delta_n") as excinfo:
        volumes(ctx, dict(params), flow, 200.0, float("nan"))
    message = str(excinfo.value)
    assert "tn_eff" in message and "nan" in message  # 归因键+实际值
    assert str(aao_pkg.manifest.unit_id) in message


def test_hebing_inflow_guard_rejects_nan_computed_value() -> None:
    """#2 hebing 入流工程量：NaN q_wet 入流计算值 →`not q_eng > 0` 拒
    （q_eng=flow.q_wet×SECS_PER_DAY——NaN 上游传播早拒；消息含端口与
    q/ds 实际值。SludgeFlow 直构=最小构造面——make_sludge P5 isfinite
    先拒 NaN 使契约面不可达，直构 dataclass 为唯一注入通道〔执行者裁量
    申报〕）。"""
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.sludge import SludgeFlow
    from waterprint.contracts.unit_api import UnitContext
    from waterprint.units_lib.sludge.hebing import compute as hebing_compute

    def _stock(q_wet: float) -> SludgeFlow:
        return SludgeFlow(q_wet=q_wet, ds=1.0, moisture=0.98)

    inflows = {
        PortRef(unit_id="up_primary", port_id="in_primary"):
            _stock(float("nan")),
        PortRef(unit_id="up_bio", port_id="in_bio"): _stock(1.0),
        PortRef(unit_id="up_chem", port_id="in_chem"): _stock(1.0),
    }
    ctx = UnitContext(
        unit_id="sludge_hebing", inflows=inflows, inqualities={}, params={},
        condition=build_condition_set([]).iter_all().__next__(),
        assumptions={}, trace=None)
    with pytest.raises(InvalidUnitConfig, match="q_wet/ds") as excinfo:
        hebing_compute._inflow_stocks(ctx)  # noqa: SLF001  # 入流装配面直调
    message = str(excinfo.value)
    assert "in_primary" in message and "nan" in message  # 端口+实际值归因
    assert "sludge_hebing" in message


def test_bashi_throat_guard_rejects_nan() -> None:
    """#3 bashi 喉宽：NaN b_throat →`not b_throat > 0` 拒（is None 检查
    前置不拦 NaN——`b_throat <= 0` 恒 False 穿透旧句式；消息含参数名）。"""
    from waterprint.units_lib.municipal.bashi_jiliangcao import compute as bashi

    with pytest.raises(InvalidUnitConfig, match=rf"参数 'b_throat'"):
        bashi._grade_of({"b_throat": float("nan")})  # noqa: SLF001  # 选档面直调


def test_adjacent_nan_face_case_count_is_eight() -> None:
    """面锚：T2 相邻同病八处（五 _factor+#1 aao+#2 hebing+#3 bashi）。"""
    assert len(_NAN_FACTOR_CASES) + 3 == 8
