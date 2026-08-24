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
bind_dimension_lookup(_optional_lookup)
