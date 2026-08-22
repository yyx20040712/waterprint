"""全厂结果与计算迹节点 schema（全架构总线：概算/图纸/三维/前端都消费它）。

输入:  图引擎执行产出（graph/executor.py）、公式应用记录（trace/collector.py）
输出:  PlantResult / TraceNode（序列化模型，字段 ID 制）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_result_schema.py）
#
# 【公开接口】
#   class TraceNode(不可变)：一次公式应用的完整记录——
#       formula_id、输入快照（字段ID→规范单位值）、输出值、
#       norm_ref（条文号）、unit_id、condition_key
#   class UnitResultSnapshot：UnitResult 的序列化形态（含 warnings）
#   class PlantResult(不可变)：
#       conditions: Mapping[condition_key → Mapping[unit_id → UnitResultSnapshot]]
#       summary:    Mapping[condition_key → 汇总指标]（出水裕度、总泥量等，
#                   按字段 ID，非中文名）
#       trace:      tuple[TraceNode, ...]     全程可审计（§3 保证 5）
#       repro:      {design_hash, engine_version, data_version}   三元组
#   serialize(result) / deserialize(data)   确定性序列化正门
#
# 【行为规格】
#   R1 本 schema 是全架构总线（§16 A4）：elevation/cost/drafting/geometry/
#      前端全部只消费它，互不感知；变更必须走 ADR + 契约测试 + 前端重新生成。
#   R2 稳定字段 ID：概算/Excel/图纸按字段 ID 取数；中文名只存在于 i18n
#      显示层（§3 保证 4，病灶"概算 4 级中文模糊匹配/361 条影子标签"）。
#   R3 序列化确定性：键排序、round(x,10) 定点、无随机 ID——同结果两次序列化
#      字节级相同（与 project/io 同规则，供"双跑 diff=0"测试）。
#   R4 结果绑定三元组：repro 三元组与项目 metadata 不一致 = 结果过期，
#      消费方（导出/前端）必须显式提示，禁止静默使用（§16 A8）。
#   R5 计算迹完整性：任一输出数值都能沿 trace 回溯到公式 ID + 条文号 +
#      输入快照——审计链路（M4 验收）以此为准。
#
# 【测试要求】往返无损、确定性序列化、按 condition_key 索引完整性、
#   三元组不一致检测。
#
# 【参照】重写计划 §3-4/§3-6/§12.3/§16 A4；ADR-004
# ══════════════════════════════════════════════════════════════════
