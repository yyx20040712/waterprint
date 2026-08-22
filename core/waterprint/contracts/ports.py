"""端口与边契约（水/泥类型化端口、回流标记——回路与连接合法性的唯一裁判）。

输入:  单元 manifest 的端口声明、用户的连线意图
输出:  Port / Edge 不可变类型与 FluidKind 枚举
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_ports.py）
#
# 【公开接口】
#   class FluidKind(Enum)：WATER / SLUDGE
#   class Direction(Enum)：IN / OUT
#   class Port(不可变)：port_id、fluid: FluidKind、direction: Direction、
#       recycle: bool = False（回流/内回流边标记，驱动 SCC 划分与固定点迭代）
#   class PortRef(不可变)：unit_id + port_id（边的端点）
#   class Edge(不可变)：src: PortRef、dst: PortRef
#   validate_edge(edge, ports_index) -> None
#       连接合法性唯一裁判；非法抛 InvalidConnection（含人类可读原因）
#
# 【行为规格】
#   R1 类型不匹配（水→泥、泥→水）= InvalidConnection；前端连线规则与
#      本规则同源（端口颜色=流体语义只是显示，真相在这里）。
#   R2 方向必须 OUT→IN；一入多出/多入一出由图级校验（graph 层）处理，
#      本文件只管单条边的局部合法性。
#   R3 recycle=True 的边：语义为"循环回流"（污泥回流 R、内回流 Ri），
#      图引擎据此把环从异常变为可解对象（§3 保证 3，病灶"DAG 环路直接异常"）。
#   R4 端口 ID 稳定：进项目文件序列化，改名必须走迁移链（project/migration.py）。
#
# 【测试要求】类型/方向非法拒绝（含错误消息可读）、recycle 标记缺省 False、
#   不可变性（赋值即异常）。
#
# 【参照】重写计划 §3-3/§14.2；ADR-003
# ══════════════════════════════════════════════════════════════════
