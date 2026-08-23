"""单元计算协议：UnitContext → UnitResult（图执行器与工艺单元之间的唯一耦合面）。

输入:  上游端口量快照（水/泥）、参数（规范单位裸值）、工况、假设注入、迹收集器
输出:  UnitResult（输出端口量 + 维度字段数组 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_unit_api.py）
#
# 【公开接口】
#   class UnitContext(不可变)：
#       unit_id: str
#       inflows:  Mapping[PortRef→WaterFlow|SludgeFlow]   上游快照
#       inqualities: Mapping[PortRef→WaterQuality]
#       params:   Mapping[字段ID→float]    规范单位裸值（manifest 校验过）
#       condition: OperatingCondition      当前工况（ADR-007）
#       assumptions: AssumptionSet         显性化默认假设（registry 注入）
#       trace: TraceSink 协议引用          记录公式应用（contracts/trace_api.py）
#   class UnitResult(不可变)：
#       outflows: Mapping[PortRef→WaterFlow|SludgeFlow]
#       outqualities: Mapping[PortRef→WaterQuality]
#       dims:      结构化数组（字段、单位、值——dtype 由 dimensions 注册表定义）
#       warnings:  tuple[Warning, ...]
#       formula_ids: tuple[str, ...]       本次执行实际应用的公式 ID（可审计）
#   class Unit(Protocol)：
#       manifest: UnitManifest
#       def compute(ctx: UnitContext) -> UnitResult: ...
#
# 【行为规格】
#   R1 compute 是纯函数：同 ctx 必同 UnitResult（可复算基石，§3 保证 6）；
#      禁止读写全局状态、禁止随机数、禁止时钟访问。
#   R2 协议即装配边界：graph/executor.py 只 import 本协议，永不 import 具体单元
#      （import-linter "装配点唯一"契约强制）。
#   R3 向量化唯一实现：compute 的数值路径必须是向量化实现，标量 = N=1 特例
#      （§3 保证 1；禁止双轨——单元测试断言标量与 N=1 数组结果一致）。
#   R4 中文名只存在于 i18n 显示层：dims 按字段 ID 取数（§3 保证 4）。
#   R5 工况影响只经 ctx.condition + manifest 声明式映射进入参数，compute 内
#      禁止工况 if 分支（ADR-007，评审拒绝项）。
#
# 【测试要求】协议结构契约（字段存在/不可变）、N=1 特例断言模板、
#   纯函数断言模板（供 32 个单元包镜像套用）。
#
# 【参照】重写计划 §3/§13.1/§14.1；借鉴 Blender/n8n 节点契约（§15）
# ══════════════════════════════════════════════════════════════════
