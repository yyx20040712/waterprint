"""辐流初沉池清单声明：参数/端口/去除率引用/条文/工况映射（声明式唯一真源）。

输入:  本单元工程定义（范围与出处见 docs/norms，M2 交付期冻结）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（结构预留：municipal_chuchenchi，内容随 M2 交付）
#
# 【固定形态】UNIT_ID = "municipal_chuchenchi"；manifest = load_manifest({...})。
# 【迁移来源】旧系统 mod.json（chuchenchi）仅作交叉对照，不作依据——
#   参数范围/默认值/条文号逐条按现行规范复核（重写计划 §5）。
# 【声明五件】params（含离散网格）/ ports（含回流标记）/
#   removal_refs（data/coefficients 键）/ norm_refs（条文号列表，非空）/
#   condition_mappings（n_active 等声明式规则，ADR-007）。
# ══════════════════════════════════════════════════════════════════
