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
#   dtype_of(fields: Sequence[str]) -> numpy 结构化数组 dtype 描述
#       【T4 落点占位】（方案枚举与 UnitResult.dims 的数组形态由此生成，
#       单位作元数据随行）——本任务 D2 裁决留 T4，不在本文件留任何
#       代码占位（宪法 §3 禁占位实现；本注记即唯一占位形态）
#
# 【行为规格】
#   R1 字段 ID 是全系统取数唯一键：result_schema/概算/Excel/图纸/三维
#      全部按 field_id 取数；中文名只在 i18n_key（§3 保证 4）。
#   R2 unit 必须等于 quantity.CANONICAL_UNITS[dim]——登记时静态校验，
#      单位双轨在此终结（§12.1 三层策略的元数据层）。
#   R3 field_id 不可变更语义：只增不改名（序列化与历史计算迹依赖）。
#   R4 dtype_of 生成的结构化数组是 solution/enumerate.py 向量化枚举与
#      结果 DataFrame 的统一形态（pint 不进热路径，单位在本表，§11 R1）。
#      【T4 落点，见上】
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
# 【测试要求】登记→查询往返、单位与量纲不一致拒绝、dtype 生成含全部字段
#   【T4】、重复登记拒绝、未登记查询抛领域异常。
#
# 【参照】重写计划 §2 单位制行/§12.1/§11 R1；简报 T3 D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from waterprint.contracts.manifest import bind_dimension_lookup
from waterprint.contracts.quantity import CANONICAL_UNITS, DimKey


class InvalidDimensionError(Exception):
    """维度字段登记/查询非法（单位不一致/重复登记/未登记）——领域异常。"""


@dataclass(frozen=True)
@final
class FieldSpec:
    """单字段登记项：ID + 量纲 + 规范单位 + i18n 显示键 + 分类（五字段）。"""

    field_id: str
    dim: DimKey
    unit: str
    i18n_key: str
    category: str


# 进程内唯一真源：field_id → FieldSpec（R3 只增不改名）。
_FIELDS: dict[str, FieldSpec] = {}


def register_dimension(spec: FieldSpec) -> None:
    """登记字段：R2 单位==规范单位 + R3 唯一性双守卫，违反即拒。"""
    if spec.unit != CANONICAL_UNITS[spec.dim]:
        raise InvalidDimensionError(
            f"字段 {spec.field_id!r} 单位非法：{spec.unit!r}，"
            f"DimKey.{spec.dim.value} 的规范单位为 "
            f"{CANONICAL_UNITS[spec.dim]!r}（R2 单位双轨在此终结）"
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
