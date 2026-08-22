"""污泥线单元包根（7 个单元包，M3 交付；回路迭代的主战场）。

输入:  各单元包的 manifest/compute 白名单导出
输出:  线级导出聚合（供 units_lib.discover_units 扫描）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M0.5 结构接线：7 包骨架已就位，内容随 M3 交付）
#
# 【本线单元包（7）】
#   hebing 合并、shusong 输送、bengzhan 泵站、nongsuo 浓缩、
#   xiaohua 消化、tuoshui 脱水、ganhua 干化
#
# 【典型流程链】各线排泥 → hebing → shusong → bengzhan → nongsuo
#   →（xiaohua）→ tuoshui →（ganhua）→ 外运处置
#
# 【本线特殊性】
#   - 污泥回流 R/内回流 Ri 循环边 → 回路组经 graph/loop 固定点迭代
#     （本线单元仍是纯函数——迭代状态由图引擎持有）；
#   - SLUDGE 端口类型独立通道，DS 守恒由性质测试背书（contracts/
#     sludge.py R1）；
#   - 含水率沿程变化：各单元改写 moisture 产生新 SludgeFlow，
#     禁止原地修改。
# ══════════════════════════════════════════════════════════════════
