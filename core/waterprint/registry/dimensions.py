"""维度字段注册表：字段 ID / 单位 / 显示键 / 分类的唯一真源（dtype 元数据层）。

输入:  字段声明（各 manifest 与结果 schema 引用的字段 ID）
输出:  字段→（DimKey、规范单位、i18n 显示键、分类）查询
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 最小实现；镜像测试 tests/registry/test_dimensions.py）
#
# 【公开接口】
#   class FieldSpec(不可变)：field_id: str、dim: DimKey、unit: str（规范单位）、
#       i18n_key: str、category: str（几何/负荷/设备/水质/污泥/概算…）——五字段
#   class InvalidDimensionError(Exception)
#       登记非法（单位与量纲不一致/字段重复/未登记查询）——GR-11 Invalid* 族
#   register_dimension(spec: FieldSpec) -> None
#   dimension_of(field_id: str) -> FieldSpec    未登记 = 领域异常（禁 None）
#   dtype_of(fields: Sequence[str]) -> numpy.dtype（T4 D5 已实现）
#       结构化 dtype：每输入 field_id 一命名槽、逐槽 "<f8"、字段序=输入
#       序；单位不进 dtype（FieldSpec 即元数据随行，R4"单位在本表"）。
#       三拒（全 InvalidDimensionError，消息含 field_id 原值）：空序列
#       拒（GR-14 空集显式语义：无字段=装配缺陷禁静默）、未知字段拒
#       （内部经 dimension_of）、序列内重复拒。
#       （原"【T4 落点占位】本注记即唯一占位形态"使命终结，2026-08-24）
#
# 【行为规格】
#   R1 字段 ID 是全系统取数唯一键：result_schema/概算/Excel/图纸/三维
#      全部按 field_id 取数；中文名只在 i18n_key（§3 保证 4）。
#   R2 unit 必须等于 quantity.CANONICAL_UNITS[dim]——登记时静态校验，
#      单位双轨在此终结（§12.1 三层策略的元数据层）。
#   R3 field_id 不可变更语义：只增不改名（序列化与历史计算迹依赖）。
#      【ARCH1 D2】field_id 登记即过文法守卫：须匹配
#      [A-Za-z_][A-Za-z0-9_]*（与 manifest 侧 _IDENTIFIER_PATTERN 对称，
#      GR-26 推广），违反 → InvalidDimensionError（消息含 field_id 原值
#      +文法要求）——依据 dtype_of 槽名==field_id 恒等假设：空串等非法
#      名登记会使 numpy 静默改名（f0），故拒绝于登记期。pool_length 等
#      合法名不受扰。
#      （注：manifest 侧 _IDENTIFIER_PATTERN 允许数字开头——数字开头
#      param name 可过 manifest 文法，但必在 R1a 报"未登记"且无法经
#      register_dimension 补登记（本守卫拒），诊断需两跳定位文法病根；
#      ARCH1 二审 M-3 实证，两侧消息均载文法条款。）
#   R4 dtype_of 生成的结构化数组是 solution/enumerate.py 向量化枚举与
#      结果 DataFrame 的统一形态（pint 不进热路径，单位在本表，§11 R1）。
#      【T4 已落地，见【公开接口】dtype_of】
#
# 【T3 冻结注记】（总控简报 D2 裁决，2026-08-23）
#   - 模块级预置 pool_length（dim=LENGTH、unit="m"、
#     i18n_key="units.fields.pool_length"、category="geometry"）——
#     manifest 测试（roundtrip R1a）与全系统几何取数的首个冻结字段。
#   - 依赖倒置装配：本模块导入时经 contracts.manifest.bind_dimension_lookup
#     安装 dimension_of 查询（L1→L0 合法边；manifest 的 R1a 校验借此
#     查询，L0 不 import L1——AGENTS §1 / 图谱 §1b 仅声明 registry→contracts）。
#   - 注册表状态在模块级单例 dict（进程内唯一真源）；登记/查询均同步。
#   - registry/** 在魔法数字白名单内（本文件当前零数值字面量）。
#
# 【T4 冻结注记】（总控简报 D5/D6 裁决，2026-08-24）
#   - D6：FieldSpec.dim 类型放宽为 DimKey | str，__post_init__ 归一为
#     DimKey（非法字符串 → InvalidDimensionError，消息含原值）——锁定
#     测试传 "LENGTH"/"FLOW" 字符串（DimKey 为 StrEnum 且值==名，字典
#     查找兼容），归一消除 R2 错误消息 spec.dim.value 对裸 str 的
#     AttributeError 隐患。registry/formulas.py 的 FormulaSpec 同款归一。
#   - D5：dtype_of 已实现（见【公开接口】）；数值面零字面量
#     （"<f8" 是 dtype 记法字符串，非数值）。
#
# 【测试要求】登记→查询往返、单位与量纲不一致拒绝、dtype 生成含全部字段
#   【T4】、重复登记拒绝、未登记查询抛领域异常。
#
# 【参照】重写计划 §2 单位制行/§12.1/§11 R1；简报 T3 D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

import numpy

from waterprint.contracts.manifest import bind_dimension_lookup
from waterprint.contracts.quantity import CANONICAL_UNITS, DimKey


class InvalidDimensionError(Exception):
    """维度字段登记/查询非法（单位不一致/重复登记/未登记）——领域异常。"""


# field_id 文法（ARCH1 D2，GR-26 推广）：登记期守卫，与 manifest 侧
# _IDENTIFIER_PATTERN 对称（本侧更严：首字符须字母/下划线——dtype 槽名
# 恒等假设要求合法标识符形态）。
_FIELD_ID_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _normalize_dim(value: DimKey | str, field_id: str) -> DimKey:
    """D6 归一：DimKey | str → DimKey（非法字符串拒，消息含原值）。"""
    if isinstance(value, DimKey):
        return value
    if not isinstance(value, str):
        raise InvalidDimensionError(
            f"字段 {field_id!r} 的 dim 必须为 DimKey 或其成员名字符串："
            f"得到 {value!r}"
        )
    try:
        return DimKey(value)
    except ValueError as exc:
        members = sorted(member.value for member in DimKey)
        raise InvalidDimensionError(
            f"字段 {field_id!r} 的 dim 非法：{value!r}（合法 {members}）"
        ) from exc


@dataclass(frozen=True)
@final
class FieldSpec:
    """单字段登记项：ID + 量纲 + 规范单位 + i18n 显示键 + 分类（五字段）。

    dim 收 DimKey | str（D6）：锁定测试与声明侧传成员名字符串
    （"LENGTH" 等），__post_init__ 归一为 DimKey——登记后一律枚举。
    """

    field_id: str
    dim: DimKey | str
    unit: str
    i18n_key: str
    category: str

    def __post_init__(self) -> None:
        """dim 归一（D6）：非法字符串 → InvalidDimensionError（含原值）。"""
        object.__setattr__(self, "dim", _normalize_dim(self.dim, self.field_id))


# 进程内唯一真源：field_id → FieldSpec（R3 只增不改名）。
_FIELDS: dict[str, FieldSpec] = {}


def register_dimension(spec: FieldSpec) -> None:
    """登记字段：D2 文法守卫 + R2 单位==规范单位 + R3 唯一性三守卫，违反即拒。"""
    if not isinstance(spec.field_id, str) or not _FIELD_ID_PATTERN.fullmatch(
        spec.field_id
    ):
        raise InvalidDimensionError(
            f"字段 ID 文法非法：{spec.field_id!r}"
            "（须匹配 [A-Za-z_][A-Za-z0-9_]*——dtype_of 槽名==field_id "
            "恒等假设，空串/空格/中文会使 numpy 静默改名；GR-26 推广，"
            "ARCH1 D2）"
        )
    dim = _normalize_dim(spec.dim, spec.field_id)
    if spec.unit != CANONICAL_UNITS[dim]:
        raise InvalidDimensionError(
            f"字段 {spec.field_id!r} 单位非法：{spec.unit!r}，"
            f"DimKey.{dim.value} 的规范单位为 "
            f"{CANONICAL_UNITS[dim]!r}（R2 单位双轨在此终结）"
        )
    if spec.field_id in _FIELDS:
        raise InvalidDimensionError(
            f"字段重复登记：{spec.field_id!r}"
            "（field_id 只增不改名，R3——序列化与历史计算迹依赖）"
        )
    _FIELDS[spec.field_id] = spec


def dimension_of(field_id: str) -> FieldSpec:
    """字段查询正门：未登记 = 领域异常（禁止返回 None 假装成功）。"""
    try:
        return _FIELDS[field_id]
    except KeyError as exc:
        raise InvalidDimensionError(
            f"未登记字段：{field_id!r}（合法字段经 register_dimension 登记；"
            "field_id 是全系统取数唯一键，R1）"
        ) from exc


def dtype_of(fields: Sequence[str]) -> numpy.dtype[numpy.void]:
    """结构化 dtype（D5/R4）：方案枚举与结果数组的统一形态生成正门。

    每输入 field_id 一命名槽、逐槽 "<f8"、字段序=输入序；单位不进
    dtype（FieldSpec 即元数据随行——"单位在本表"，§11 R1）。三拒
    （全 InvalidDimensionError，消息含 field_id 原值）：空序列拒
    （GR-14 空集显式语义：无字段=装配缺陷禁静默）、未知字段拒
    （内部经 dimension_of，R1 唯一键）、序列内重复拒（dtype 列名唯一）。
    """
    if not fields:
        raise InvalidDimensionError(
            "dtype_of 拒绝空字段序列：无字段的 dtype = 装配缺陷"
            "（GR-14 空集显式语义——禁静默产出零列数组）"
        )
    seen: set[str] = set()
    for field_id in fields:
        if field_id in seen:
            raise InvalidDimensionError(
                f"dtype_of 字段序列含重复：{field_id!r}"
                "（结构化 dtype 列名必须唯一——GR-14 显式拒绝）"
            )
        seen.add(field_id)
        dimension_of(field_id)
    return numpy.dtype([(field_id, "<f8") for field_id in fields])


def _optional_lookup(field_id: str) -> FieldSpec | None:
    """R1a 查询钩子（manifest 侧约定：None = 未登记，异常语义留本层）。"""
    return _FIELDS.get(field_id)


# 模块级预置（D2 冻结）：pool_length——几何取数首个冻结字段。
_POOL_LENGTH: FieldSpec = FieldSpec(
    field_id="pool_length",
    dim=DimKey.LENGTH,
    unit="m",
    i18n_key="units.fields.pool_length",
    category="geometry",
)
register_dimension(_POOL_LENGTH)

# ── M1a 三单元切片参数字段（2026-08-25；出处=docs/norms/{cugeshan,
#    xigeshan,chenshachi}.md 三表签字参数列——粗/细格栅参数表意共用字段
#    ID，同名跨线不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4）。
#    角度（alpha/theta）与日数（t_clean）、表面负荷（q_surf，m³/(m²·h)）、
#    重力加速度（g_gravity，m/s²）、时换算（sec_per_hour，s/h）在 DimKey
#    无对应量类，按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，三表
#    口径：°/d/m³·m⁻²·h⁻¹/m·s⁻²/s）。 ──
_M1A_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("n", DimKey.DIMENSIONLESS, "", "units.fields.n", "equipment"),
    FieldSpec("b", DimKey.LENGTH, "m", "units.fields.b", "geometry"),
    FieldSpec("alpha", DimKey.DIMENSIONLESS, "", "units.fields.alpha", "geometry"),
    FieldSpec("h", DimKey.LENGTH, "m", "units.fields.h", "geometry"),
    FieldSpec("v", DimKey.VELOCITY, "m/s", "units.fields.v", "load"),
    FieldSpec("v1", DimKey.VELOCITY, "m/s", "units.fields.v1", "load"),
    FieldSpec("s", DimKey.LENGTH, "m", "units.fields.s", "geometry"),
    FieldSpec("bar_shape", DimKey.DIMENSIONLESS, "", "units.fields.bar_shape",
              "equipment"),
    FieldSpec("g_gravity", DimKey.DIMENSIONLESS, "", "units.fields.g_gravity",
              "load"),
    FieldSpec("length_disc_step", DimKey.LENGTH, "m",
              "units.fields.length_disc_step", "geometry"),
    FieldSpec("q_surf", DimKey.DIMENSIONLESS, "", "units.fields.q_surf", "load"),
    FieldSpec("t_retention", DimKey.TIME, "s", "units.fields.t_retention",
              "load"),
    FieldSpec("t_clean", DimKey.DIMENSIONLESS, "", "units.fields.t_clean",
              "operation"),
    FieldSpec("theta", DimKey.DIMENSIONLESS, "", "units.fields.theta",
              "geometry"),
    FieldSpec("d_r", DimKey.LENGTH, "m", "units.fields.d_r", "geometry"),
    FieldSpec("b_channel", DimKey.LENGTH, "m", "units.fields.b_channel",
              "geometry"),
    FieldSpec("v_channel", DimKey.VELOCITY, "m/s", "units.fields.v_channel",
              "load"),
    FieldSpec("sec_per_hour", DimKey.DIMENSIONLESS, "",
              "units.fields.sec_per_hour", "load"),
)
for _spec in _M1A_FIELDS:
    register_dimension(_spec)
bind_dimension_lookup(_optional_lookup)

# ── M2a2 核心三单元参数字段（2026-08-25；出处=docs/norms/{chuchenchi,aao,
#    erchunchi}.md 三表参数列/算例 1 输入行——同名跨单元字段 ID 不耦合：
#    各包 manifest 各写各的默认值，AGENTS §11 R4；x_mlss/h2/r_external 等
#    联动值由调用侧取同值，注册表只登记字段语义）。小时/日/负荷带类单位
#    在 DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键
#    走，三表口径：h/d/m³·m⁻²·h⁻¹/kgBOD5·kgMLSS⁻¹·d⁻¹）。 ──
_M2A2_FIELDS: tuple[FieldSpec, ...] = (
    # chuchenchi 辐流初沉池（算例 1：q'=2.3/T=1.2 h/T_sludge=2 d/r1=1.8/
    # r2=0.8/h5=1.5；D 档 0.5 m/长度档 0.1 m）
    FieldSpec("q_prime", DimKey.DIMENSIONLESS, "", "units.fields.q_prime", "load"),
    FieldSpec("t_settle", DimKey.DIMENSIONLESS, "", "units.fields.t_settle", "load"),
    FieldSpec("t_sludge", DimKey.DIMENSIONLESS, "", "units.fields.t_sludge",
              "operation"),
    FieldSpec("r1", DimKey.LENGTH, "m", "units.fields.r1", "geometry"),
    FieldSpec("r2", DimKey.LENGTH, "m", "units.fields.r2", "geometry"),
    FieldSpec("h5", DimKey.LENGTH, "m", "units.fields.h5", "geometry"),
    FieldSpec("dia_disc_step", DimKey.LENGTH, "m", "units.fields.dia_disc_step",
              "geometry"),
    # aao AAO 生物池（算例 1：Ns=0.10/X=4000/t_p=1.5 h/R=1.0/Ri=2.0/
    # TN_eff=15；sec_per_hour=3600 时换算）
    FieldSpec("ns", DimKey.DIMENSIONLESS, "", "units.fields.ns", "load"),
    FieldSpec("x_mlss", DimKey.CONCENTRATION, "mg/L", "units.fields.x_mlss",
              "load"),
    FieldSpec("t_p", DimKey.DIMENSIONLESS, "", "units.fields.t_p", "load"),
    FieldSpec("r_external", DimKey.DIMENSIONLESS, "", "units.fields.r_external",
              "operation"),
    FieldSpec("r_internal", DimKey.DIMENSIONLESS, "", "units.fields.r_internal",
              "operation"),
    FieldSpec("tn_eff", DimKey.CONCENTRATION, "mg/L", "units.fields.tn_eff",
              "load"),
    # erchunchi 辐流二沉池（算例 1：q_nom=1.2/X=4000 联动/R=1.0 联动/
    # h2=3.0/r_pit=1.0）
    FieldSpec("q_nom", DimKey.DIMENSIONLESS, "", "units.fields.q_nom", "load"),
    FieldSpec("r_pit", DimKey.LENGTH, "m", "units.fields.r_pit", "geometry"),
    FieldSpec("h2", DimKey.LENGTH, "m", "units.fields.h2", "geometry"),
)
for _spec in _M2A2_FIELDS:
    register_dimension(_spec)

# ── M2b2 深度处理段四单元参数字段（2026-08-25；出处=docs/norms/{tiaojiechi,
#    gaomidu,vxinglvchi,ziwai}.md 四表参数档/算例 1 输入行——同名跨单元字段
#    ID 不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4；小时/分钟/负荷
#    带类单位在 DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随
#    i18n 键走，四表口径：h/min/m³·m⁻²·h⁻¹/m·h⁻¹/支/模块）。side_disc_step
#    为平面边长 0.5 m 离散档（tiaojiechi B/L、gaomidu B、vxinglvchi B/L
#    共用语义形态，与 M2a2 dia_disc_step 池径档对称）。 ──
_M2B2_FIELDS: tuple[FieldSpec, ...] = (
    # tiaojiechi 调节池（算例 1：t_reg=8.0 h/h2=5.0 m/ratio_lb=2.5/
    # n_pump_duty=2；B/L 档 0.5 m、DN 档 0.1 m）
    FieldSpec("t_reg", DimKey.DIMENSIONLESS, "", "units.fields.t_reg", "load"),
    FieldSpec("ratio_lb", DimKey.DIMENSIONLESS, "", "units.fields.ratio_lb",
              "geometry"),
    FieldSpec("n_pump_duty", DimKey.DIMENSIONLESS, "", "units.fields.n_pump_duty",
              "equipment"),
    FieldSpec("side_disc_step", DimKey.LENGTH, "m", "units.fields.side_disc_step",
              "geometry"),
    # gaomidu 高密沉淀池（算例 1：q_surface=15/r_sludge=0.04/t_mix=1.5 min/
    # t_floc=12 min/l_tube=1.0/h_clear=1.2/h_buffer=1.2/h_thick=2.0；
    # B 档 0.5 m、h_total 档 0.1 m）
    FieldSpec("q_surface", DimKey.DIMENSIONLESS, "", "units.fields.q_surface",
              "load"),
    FieldSpec("r_sludge", DimKey.DIMENSIONLESS, "", "units.fields.r_sludge",
              "operation"),
    FieldSpec("t_mix", DimKey.DIMENSIONLESS, "", "units.fields.t_mix", "load"),
    FieldSpec("t_floc", DimKey.DIMENSIONLESS, "", "units.fields.t_floc", "load"),
    FieldSpec("l_tube", DimKey.LENGTH, "m", "units.fields.l_tube", "geometry"),
    FieldSpec("h_clear", DimKey.LENGTH, "m", "units.fields.h_clear", "geometry"),
    FieldSpec("h_buffer", DimKey.LENGTH, "m", "units.fields.h_buffer", "geometry"),
    FieldSpec("h_thick", DimKey.LENGTH, "m", "units.fields.h_thick", "geometry"),
    # vxinglvchi V 型滤池（算例 1：v_filter=8.0 m/h/ratio_lb=2.5/
    # h_water_above=1.3/h_sand=1.3/h_bottom=1.0/t_cycle=24；B/L 档 0.5 m）
    FieldSpec("v_filter", DimKey.DIMENSIONLESS, "", "units.fields.v_filter",
              "load"),
    FieldSpec("h_water_above", DimKey.LENGTH, "m", "units.fields.h_water_above",
              "geometry"),
    FieldSpec("h_sand", DimKey.LENGTH, "m", "units.fields.h_sand", "geometry"),
    FieldSpec("h_bottom", DimKey.LENGTH, "m", "units.fields.h_bottom", "geometry"),
    FieldSpec("t_cycle", DimKey.DIMENSIONLESS, "", "units.fields.t_cycle",
              "operation"),
    # ziwai 紫外消毒（算例 1：n_channel=2/v_channel=0.4/b_c=1.2/
    # n_lamp_module=8/l_module=0.6/l_stab=1.2/h_module=0.5；h_w 档 0.1 m）
    FieldSpec("n_channel", DimKey.DIMENSIONLESS, "", "units.fields.n_channel",
              "equipment"),
    FieldSpec("b_c", DimKey.LENGTH, "m", "units.fields.b_c", "geometry"),
    FieldSpec("n_lamp_module", DimKey.DIMENSIONLESS, "",
              "units.fields.n_lamp_module", "equipment"),
    FieldSpec("l_module", DimKey.LENGTH, "m", "units.fields.l_module", "equipment"),
    FieldSpec("l_stab", DimKey.LENGTH, "m", "units.fields.l_stab", "geometry"),
    FieldSpec("h_module", DimKey.LENGTH, "m", "units.fields.h_module", "equipment"),
)
for _spec in _M2B2_FIELDS:
    register_dimension(_spec)

# ── M2c 市政余三单元参数字段（2026-08-26；出处=docs/norms/{cass,
#    bashi_jiliangcao,wushui_tisheng}.md 三表参数档/算例 1 输入行——同名跨
#    单元字段 ID 不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4；
#    t_cycle/t_settle 沿用既有字段（CASS 周期/沉淀时段 h 语义，V 滤过滤
#    周期/初沉沉淀时间同名不同包默认值）；小时/分钟档类在 DimKey 无对应
#    量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，三表口径：
#    h/min/台）。 ──
_M2C_FIELDS: tuple[FieldSpec, ...] = (
    # cass CASS 生物池（算例 1：n_pool=4/t_cycle=4 h/t_react=2.0/
    # t_settle=1.0[复用 M2a2]/t_draw=1.0/t_selector=0.75 h；L/B 0.5 m 档）
    FieldSpec("n_pool", DimKey.DIMENSIONLESS, "", "units.fields.n_pool", "equipment"),
    FieldSpec("t_react", DimKey.DIMENSIONLESS, "", "units.fields.t_react", "operation"),
    FieldSpec("t_draw", DimKey.DIMENSIONLESS, "", "units.fields.t_draw", "operation"),
    FieldSpec("t_selector", DimKey.DIMENSIONLESS, "", "units.fields.t_selector",
              "load"),
    # bashi_jiliangcao 巴歇尔计量槽（算例 1：b_throat=0.75 m，B7 七档离散）
    FieldSpec("b_throat", DimKey.LENGTH, "m", "units.fields.b_throat", "geometry"),
    # wushui_tisheng 污水提升泵房（算例 1：t_well=10 min/h_static=10.0 m/
    # v_pipe=1.2 m/s/l_pipe=100 m/n_standby=1/h_well=2.0 m；DN 0.1 m 档）
    FieldSpec("t_well", DimKey.DIMENSIONLESS, "", "units.fields.t_well", "load"),
    FieldSpec("h_static", DimKey.LENGTH, "m", "units.fields.h_static", "load"),
    FieldSpec("v_pipe", DimKey.VELOCITY, "m/s", "units.fields.v_pipe", "load"),
    FieldSpec("l_pipe", DimKey.LENGTH, "m", "units.fields.l_pipe", "geometry"),
    FieldSpec("n_standby", DimKey.DIMENSIONLESS, "", "units.fields.n_standby",
              "equipment"),
    FieldSpec("h_well", DimKey.LENGTH, "m", "units.fields.h_well", "geometry"),
)
for _spec in _M2C_FIELDS:
    register_dimension(_spec)

# ── M3a2 矿井水线前段单元参数字段（2026-08-27；出处=docs/norms/
#    mine_water_{input,tiaojiechi,chenshachi,ningjiao}.md 四表参数档/
#    算例 1 输入行——同名跨单元字段 ID 不耦合：各包 manifest 各写各的
#    默认值，AGENTS §11 R4；tiaojiechi/chenshachi/ningjiao 参数面全部
#    复用既有字段（t_reg/h2/ratio_lb/n/side_disc_step/length_disc_step/
#    t_mix/t_floc/t_clean——默认值跨包独立），仅 input 线首注入面与
#    chenshachi/ningjiao 专属档新增登记。流量（m³/d 口径）/管径（mm）/
#    停留（s·min·h）类在 DimKey 无对应量类或口径与规范单位不一致者按
#    DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，四表口径：
#    m³/d/mm/s/min）。 ──
_M3A2_FIELDS: tuple[FieldSpec, ...] = (
    # mine_water_input 矿井水输入（算例 1：Q_avg_daily=43836 m³/d/Kz=1.5/
    # DN=800 mm/z_water_inlet=100.0/z_ground=102.0/h_pool=3.0；进水水质
    # 六指标注入=GB/T 19223-2015 含悬浮物类典型值）
    FieldSpec("q_avg_daily", DimKey.DIMENSIONLESS, "", "units.fields.q_avg_daily",
              "load"),
    FieldSpec("kz", DimKey.DIMENSIONLESS, "", "units.fields.kz", "load"),
    FieldSpec("dn_inlet", DimKey.DIMENSIONLESS, "", "units.fields.dn_inlet",
              "equipment"),
    FieldSpec("z_water_inlet", DimKey.LENGTH, "m", "units.fields.z_water_inlet",
              "geometry"),
    FieldSpec("z_ground", DimKey.LENGTH, "m", "units.fields.z_ground", "geometry"),
    FieldSpec("h_pool", DimKey.LENGTH, "m", "units.fields.h_pool", "geometry"),
    FieldSpec("ss_in", DimKey.CONCENTRATION, "mg/L", "units.fields.ss_in", "quality"),
    FieldSpec("cod_in", DimKey.CONCENTRATION, "mg/L", "units.fields.cod_in",
              "quality"),
    FieldSpec("bod5_in", DimKey.CONCENTRATION, "mg/L", "units.fields.bod5_in",
              "quality"),
    FieldSpec("nh3n_in", DimKey.CONCENTRATION, "mg/L", "units.fields.nh3n_in",
              "quality"),
    FieldSpec("tn_in", DimKey.CONCENTRATION, "mg/L", "units.fields.tn_in", "quality"),
    FieldSpec("tp_in", DimKey.CONCENTRATION, "mg/L", "units.fields.tp_in", "quality"),
    # mine_water_chenshachi 平流沉砂池（算例 1：v_h=0.25 m/s/t_stay=60 s/
    # h2=0.5 m 复用/n=8 复用/t_clean=2 d 复用 M1A；l_cell 0.5 m 档/
    # B 0.1 m 档复用 side_disc_step/length_disc_step）
    FieldSpec("v_h", DimKey.VELOCITY, "m/s", "units.fields.v_h", "load"),
    FieldSpec("t_stay", DimKey.DIMENSIONLESS, "", "units.fields.t_stay", "load"),
    # mine_water_ningjiao 混凝反应池（算例 1：t_mix=1.0/t_floc=3.0 复用
    # M2B2；t_seed=2.0/t_ripen=1.5 新增；h2/ratio_lb/n/B 0.5 m 档复用）
    FieldSpec("t_seed", DimKey.DIMENSIONLESS, "", "units.fields.t_seed", "load"),
    FieldSpec("t_ripen", DimKey.DIMENSIONLESS, "", "units.fields.t_ripen", "load"),
)
for _spec in _M3A2_FIELDS:
    register_dimension(_spec)

# ── M3a3 矿井水线后段单元参数字段（2026-08-27；出处=docs/norms/
#    mine_water_{cifenli,gaomidu,vxinglvchi,ziwai}.md 四表参数档/
#    算例 1 输入行——同名跨单元字段 ID 不耦合：各包 manifest 各写各的
#    默认值，AGENTS §11 R4；q_surf/t_mix/t_floc/n/h2 族/l_tube/h_clear/
#    h_thick/v_filter/side_disc_step/b_channel 复用既有登记（默认值跨包
#    独立），仅各表专属参数新增登记。转速（rpm）/磁种投加（kg/d）/
#    停留（min·h）/功率（W）/穿透率（%）/指数/剂量（mJ/cm²）类在
#    DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键
#    走，四表口径）。 ──
_M3A3_FIELDS: tuple[FieldSpec, ...] = (
    # mine_water_cifenli 磁分离（主算例：n_units=4 台/omega=3 rpm/
    # q_surf=25 复用 M1A；m_seed=21918 kg/d=ningjiao KN-F13 口径参数面衔接）
    FieldSpec("n_units", DimKey.DIMENSIONLESS, "", "units.fields.n_units",
              "equipment"),
    FieldSpec("omega", DimKey.DIMENSIONLESS, "", "units.fields.omega",
              "equipment"),
    FieldSpec("m_seed", DimKey.DIMENSIONLESS, "", "units.fields.m_seed",
              "operation"),
    # mine_water_gaomidu 高密沉淀（主算例：n=2 复用/t_mix=0.5/t_floc=12.0/
    # q_surf=6.0/l_tube=1.0/h_clear=1.0/h_thick=0.5 复用 M2B2；h_dist=1.5
    # 新增布水区高；B/L 0.5 m 档复用 side_disc_step）
    FieldSpec("h_dist", DimKey.LENGTH, "m", "units.fields.h_dist", "geometry"),
    # mine_water_vxinglvchi V 型滤池（主算例：n=16 复用/v_filter=5.0 复用
    # M2B2；t_filter=24 h/h_media=1.0/h_water=1.2/h_plate=0.1/h_under=0.9
    # 新增；B/L 0.1 m 档复用 side_disc_step 包独立默认）
    FieldSpec("t_filter", DimKey.DIMENSIONLESS, "", "units.fields.t_filter",
              "operation"),
    FieldSpec("h_media", DimKey.LENGTH, "m", "units.fields.h_media", "geometry"),
    FieldSpec("h_water", DimKey.LENGTH, "m", "units.fields.h_water", "geometry"),
    FieldSpec("h_plate", DimKey.LENGTH, "m", "units.fields.h_plate", "geometry"),
    FieldSpec("h_under", DimKey.LENGTH, "m", "units.fields.h_under", "geometry"),
    # mine_water_ziwai 紫外消毒渠（主算例：n=3 复用/b_channel=1.7 复用
    # M1A；h_channel=1.2/p_lamp=250 W/n_layer=6/d_long=0.12/xi_total=3/
    # n_t=1.5/t254=65 % 百分数口径新增）
    FieldSpec("h_channel", DimKey.LENGTH, "m", "units.fields.h_channel",
              "geometry"),
    FieldSpec("p_lamp", DimKey.DIMENSIONLESS, "", "units.fields.p_lamp",
              "equipment"),
    FieldSpec("n_layer", DimKey.DIMENSIONLESS, "", "units.fields.n_layer",
              "equipment"),
    FieldSpec("d_long", DimKey.LENGTH, "m", "units.fields.d_long", "equipment"),
    FieldSpec("xi_total", DimKey.DIMENSIONLESS, "", "units.fields.xi_total",
              "load"),
    FieldSpec("n_t", DimKey.DIMENSIONLESS, "", "units.fields.n_t", "load"),
    FieldSpec("t254", DimKey.DIMENSIONLESS, "", "units.fields.t254", "quality"),
)
for _spec in _M3A3_FIELDS:
    register_dimension(_spec)
# ── M3b2 污泥线七单元参数字段（sludge_*.md 七表参数档；口径同前段注）──
_M3B2_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("ds_primary", DimKey.DIMENSIONLESS, "", "units.fields.ds_primary", "sludge"),
    FieldSpec("p_primary", DimKey.DIMENSIONLESS, "", "units.fields.p_primary", "sludge"),
    FieldSpec("ds_bio", DimKey.DIMENSIONLESS, "", "units.fields.ds_bio", "sludge"),
    FieldSpec("p_bio", DimKey.DIMENSIONLESS, "", "units.fields.p_bio", "sludge"),
    FieldSpec("ds_chem", DimKey.DIMENSIONLESS, "", "units.fields.ds_chem", "sludge"),
    FieldSpec("p_chem", DimKey.DIMENSIONLESS, "", "units.fields.p_chem", "sludge"),
    FieldSpec("s0_bod", DimKey.CONCENTRATION, "mg/L", "units.fields.s0_bod", "load"),
    FieldSpec("se_bod", DimKey.CONCENTRATION, "mg/L", "units.fields.se_bod", "load"),
    FieldSpec("v_bio", DimKey.VOLUME, "m3", "units.fields.v_bio", "geometry"),
    FieldSpec("x_vss", DimKey.CONCENTRATION, "mg/L", "units.fields.x_vss", "load"),
    FieldSpec("t_design", DimKey.DIMENSIONLESS, "", "units.fields.t_design", "operation"),
    FieldSpec("v_press", DimKey.VELOCITY, "m/s", "units.fields.v_press", "load"),
    FieldSpec("d_grav", DimKey.LENGTH, "m", "units.fields.d_grav", "geometry"),
    FieldSpec("q_solid", DimKey.DIMENSIONLESS, "", "units.fields.q_solid", "load"),
    FieldSpec("t_thicken", DimKey.DIMENSIONLESS, "", "units.fields.t_thicken", "load"),
    FieldSpec("h_eff", DimKey.LENGTH, "m", "units.fields.h_eff", "geometry"),
    FieldSpec("p_out", DimKey.DIMENSIONLESS, "", "units.fields.p_out", "sludge"),
    FieldSpec("h_cone", DimKey.LENGTH, "m", "units.fields.h_cone", "geometry"),
    FieldSpec("t_digest", DimKey.DIMENSIONLESS, "", "units.fields.t_digest", "operation"),
    FieldSpec("t_digest_temp", DimKey.DIMENSIONLESS, "", "units.fields.t_digest_temp", "operation"),
    FieldSpec("eta_vs", DimKey.DIMENSIONLESS, "", "units.fields.eta_vs", "sludge"),
    FieldSpec("r_biogas", DimKey.DIMENSIONLESS, "", "units.fields.r_biogas", "operation"),
    FieldSpec("machine_type", DimKey.DIMENSIONLESS, "", "units.fields.machine_type", "equipment"),
    FieldSpec("dose_pam", DimKey.DIMENSIONLESS, "", "units.fields.dose_pam", "operation"),
    FieldSpec("p_cake", DimKey.DIMENSIONLESS, "", "units.fields.p_cake", "sludge"),
    FieldSpec("t_op", DimKey.DIMENSIONLESS, "", "units.fields.t_op", "operation"),
    FieldSpec("r_evap", DimKey.DIMENSIONLESS, "", "units.fields.r_evap", "equipment"),
)
for _spec in _M3B2_FIELDS:
    register_dimension(_spec)
