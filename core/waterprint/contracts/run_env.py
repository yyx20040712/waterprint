"""执行环境上下文契约：RunEnv——装配一次、执行期只读（UF-31 下沉 L0）。

输入:  引擎版本 + 数据包聚合版本（系数/单价）+ 假设/系数/单价 + 迹收集器
输出:  RunEnv（不可变）——执行期参与可复算三元组的一切只读上下文
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_run_env.py）
#
# 【公开接口】
#   class RunEnv(不可变)：
#       engine_version、data_version（系数+单价聚合）、assumptions、
#       coefficients、price_book、trace_sink——执行环境上下文契约；
#       另含 engine_params 字段（引擎技术参数，见 R2）
#   （实现期冻结字段精确类型与装配正门签名；app 装配并重新导出）
#
# 【行为规格】
#   R1 类型家：RunEnv 定义于本契约（L0）——graph/executor.py(L3) 与
#      solution/enumerate.py(L3) 公开签名 `env: RunEnv` 只 import 本
#      文件，不上溯 app.py(L4)（UF-31 分层矛盾消解）；app.py 装配并
#      重新导出（SENS-B 2026-08-23 UF-31）。
#   R2 引擎技术参数（loop 阻尼/容差/缓存上限，UF-08 项）以"带调节
#      影响元数据的引擎默认"条目入 engine_params 字段，T4/T7 冻结
#      数值——禁散落代码字面量（GR-15 缺省须带出处同向）。
#   R3 不可变：装配一次、执行期只读（app.py【公开接口】既有语义）；
#      执行期改写 = 领域异常。
#   R4 trace_sink 遵循 contracts/trace_api.py 协议（registry 与迹
#      收集器的唯一耦合面），本契约只携带不实现。
#   R5 本文件是 L0 契约（GR-36 类②跨层协议：L3 executor/enumerate
#      与 L4 app 共用），禁 I/O、禁运行时可变状态。
#
# 【测试要求】不可变性（改写抛领域异常）、字段完备、engine_params
#   条目元数据完整性（实现期随数值冻结落用例）。
#
# 【参照】重写计划 §13.1 装配点；UF-31/UF-08/UF-10（register）；
#   GR-36/GR-15（conventions）
# ══════════════════════════════════════════════════════════════════
