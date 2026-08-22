"""公式注册表：每条公式挂表达式/条文号/量纲签名，加载时静态校验（溯源基石）。

输入:  各单元/子系统登记的公式规格（FormulaSpec）
输出:  查询 API、启动期量纲静态校验结果（不匹配 = 启动失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/registry/test_formulas.py）
#
# 【公开接口】
#   class FormulaSpec(不可变)：
#       formula_id: str          全库唯一（如 "GB50014-6.6.11-AAO-volume"）
#       expression: str          人类可读表达式（符号定义见 symbols）
#       symbols: Mapping[符号→DimKey 与含义]
#       output_dim: DimKey       输出量纲签名
#       norm_ref: str            规范条文号（GB 50014-2021 §x.x.x 等）+出处
#   register(spec) / by_id(formula_id) -> FormulaSpec
#   validate_all() -> ValidationReport
#       启动期对全部登记项做静态校验
#   apply(formula_id, bindings: Mapping[str→float],
#         ctx: (unit_id, condition_key)) -> float
#       唯一求值正门：求值同时向 TraceCollector 记录一条 TraceNode
#
# 【行为规格】
#   R1 量纲静态校验（§12.1 元数据层）：bindings 的 DimKey 集合与 spec.symbols
#      一致才允许登记生效；不一致 = 启动失败（不是运行时警告）。
#   R2 公式语义依据 = 规范条文；旧实现仅作交叉对照，不作依据（§5 迁移原则）。
#      无 norm_ref 的公式禁止登记。
#   R3 apply 是唯一求值路径：绕过 apply 直接抄公式代码 = 评审拒绝
#      （否则计算迹断链，§16 A1"注册表与实现漂移"防线）。
#   R4 实现与注册表一致性由测试背书：每条公式至少一个 golden 数值断言
#      + trace 中 formula_id 与实参值域校验（A1 缓解措施，落进单元包测试）。
#   R5 formula_id 稳定：进入项目计算迹与审计报告，改名 = 破坏可复算，
#      必须新增不修改。
#
# 【测试要求】登记→查询往返、量纲不匹配拒绝、norm_ref 必填、
#   apply 产生一条完整 TraceNode。
#
# 【参照】重写计划 §3-5/§12.1/§16 A1
# ══════════════════════════════════════════════════════════════════
