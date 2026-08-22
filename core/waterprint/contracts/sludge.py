"""污泥量契约（SLUDGE 独立通道；DS 干固体守恒的载体）。

输入:  湿泥量、干固体量 DS、含水率（边界带单位，换算到规范单位）
输出:  SludgeFlow（不可变）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_sludge.py +
# 性质测试 properties_sludge.py）
#
# 【公开接口】
#   class SludgeFlow(不可变)：
#       q_wet: float        湿泥体积流量，规范单位 m3/s
#       ds: float           干固体质量流量，规范单位 kg/s
#       moisture: float     含水率，小数（0 <= moisture < 1）
#   make_sludge(...) -> SludgeFlow   构造正门（单位换算+校验集中于此）
#   mix(flows: Sequence[SludgeFlow], weights) -> SludgeFlow
#       污泥汇流：q_wet、ds 各自求和；含水率由总量反解（非简单平均）
#
# 【行为规格】
#   R1 守恒不变量（性质测试常驻）：任何混合/分流前后 Σds 不变
#      （§14.2"DS 守恒断言进性质测试——含水率变化不守恒即失败"）。
#   R2 含水率与 (ds, q_wet) 的相互换算依赖污泥密度假设，该假设只存在于
#      registry/assumptions.py（默认值带出处），本契约不内嵌密度常数。
#   R3 校验：q_wet >= 0、ds >= 0、0 <= moisture < 1；违反抛领域异常。
#   R4 污泥链含水率沿程变化 = 各单元改写 moisture 后产生新 SludgeFlow
#      （不可变值对象，禁止原地修改）。
#
# 【测试要求】混合守恒、含水率反解、非法构造拒绝；
#   性质：随机两组混合 Σds 前后相等（hypothesis）。
#
# 【参照】重写计划 §14.2；ADR 语义：SLUDGE 端口类型独立于 WATER（ports.py）
# ══════════════════════════════════════════════════════════════════
