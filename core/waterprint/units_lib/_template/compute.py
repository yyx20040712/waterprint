"""单元计算实现模板：唯一计算源（≤400 行）；本模板走标量形态
（批量=逐行调用；municipal 13 包已切 _apply_batch 向量路径，
见 architecture §3.8）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + 维度字段数组 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；`wp new-unit` 生成的 compute.py 必须满足）
#
# 【固定形态】
#   def make_unit(...) -> Unit 协议实现（工厂由包 __init__ 导出）
#   数值路径 = 标量 compute 逐行调用（批 13-A 起 municipal 13 包已切
#   _apply_batch 向量路径；新单元默认标量形态，向量化另立批切换）。
#
# 【编写规则】
#   R1 一切公式经 registry.formulas.apply 求值（formula_id 挂条文）；
#      内联公式代码 = 评审拒绝（计算迹断链，§16 A1）。
#   R2 默认值经 ctx.assumptions 取得；代码内数值字面量（非 0/1 索引）
#      = 评审拒绝（§3 保证 7）。
#   R3 工况影响只经 manifest 工况映射后的 ctx.params（compute 内
#      禁止读 ctx.condition 做分支——ADR-007）。
#   R4 纯函数：无全局可变状态、无随机、无时钟（§3 保证 6）。
#   R5 禁止 import 其他单元包与 L3 子系统（分层契约）。
#   R6 超 400 行按公式组拆子模块（volume/oxygen/geometry…），
#      compute.py 只做编排（拆分阈值低于全局 500，AGENTS §11）。
#   R7 输出按字段 ID（dimensions 注册过），中文名只进 i18n 键。
#   R8 业务规则对齐 docs/business-logic.md：参数只经 §1 初始化链；
#      耦合量按 §2 单一归属表读结果契约（禁双写）；数值字面量
#      零容忍（§9，check_magic_numbers.py 白名单不含 units_lib）。
# ══════════════════════════════════════════════════════════════════
