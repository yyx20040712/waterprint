"""维度字段注册表：字段 ID / 单位 / 显示键 / 分类的唯一真源（dtype 元数据层）。

输入:  字段声明（各 manifest 与结果 schema 引用的字段 ID）
输出:  字段→（DimKey、规范单位、i18n 显示键、分类）查询
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/registry/test_dimensions.py）
#
# 【公开接口】
#   class FieldSpec(不可变)：field_id、dim: DimKey、unit: str（规范单位）、
#       i18n_key: str、category: str（几何/负荷/设备/水质/污泥/概算…）
#   register_dimension(spec) / dimension_of(field_id) -> FieldSpec
#   dtype_of(fields: Sequence[str]) -> numpy 结构化数组 dtype 描述
#       （方案枚举与 UnitResult.dims 的数组形态由此生成，单位作元数据随行）
#
# 【行为规格】
#   R1 字段 ID 是全系统取数唯一键：result_schema/概算/Excel/图纸/三维
#      全部按 field_id 取数；中文名只在 i18n_key（§3 保证 4）。
#   R2 unit 必须等于 quantity.CANONICAL_UNITS[dim]——登记时静态校验，
#      单位双轨在此终结（§12.1 三层策略的元数据层）。
#   R3 field_id 不可变更语义：只增不改名（序列化与历史计算迹依赖）。
#   R4 dtype_of 生成的结构化数组是 solution/enumerate.py 向量化枚举与
#      结果 DataFrame 的统一形态（pint 不进热路径，单位在本表，§11 R1）。
#
# 【测试要求】登记→查询往返、单位与量纲不一致拒绝、dtype 生成含全部字段、
#   重复登记拒绝。
#
# 【参照】重写计划 §2 单位制行/§12.1/§11 R1
# ══════════════════════════════════════════════════════════════════
