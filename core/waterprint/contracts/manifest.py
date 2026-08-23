"""模组清单 schema：参数/端口/去除率/规范引用/工况映射的声明式唯一真源。

输入:  清单数据（单元包内 manifest.py 声明，或序列化 JSON）
输出:  UnitManifest（加载即静态校验，非法清单 = 启动失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_manifest.py）
#
# 【公开接口】
#   class ParamSpec：field_id、dim: DimKey、default、离散网格（可选，
#       solution/grid.py 消费）、范围（可选，约束层消费）
#   class ConditionMapping：声明式规则，形如
#       {"n_active": "n if pool.all_pools else n - 1"} 的受限表达式 DSL
#   class UnitManifest(不可变)：
#       unit_id / i18n_key / version / business_line
#       params: tuple[ParamSpec, ...]
#       ports:  tuple[Port, ...]
#       removal_refs: Mapping[指标→coefficients 键]（去除率引用数据包）
#       norm_refs: tuple[条文引用, ...]    （GB 50014-2021 §x.x.x 等）
#       condition_mappings: tuple[ConditionMapping, ...]
#       constraint_refs: tuple[str, ...]   （constraint_kb 键）
#   load_manifest(data: Mapping) -> UnitManifest   加载+静态校验正门
#
# 【工况映射 DSL】（T0.5 冻结；求值内核 = contracts/expr.py 共享受限求值器）
#   统一写法：目标参数 → 表达式字符串，形如
#      {"n_active": "n if pool.all_pools else n - 1"}（本示例为正典，
#      ADR-007 决策 3 同此写法，消除两处示例漂移的双源）。
#   语法子集 = 公式 DSL（见 registry/formulas.py【表达式 DSL】）+ 条件
#      扩展：IfExp（x if cond else y）、Compare（== != < > <= >=）、
#      BoolOp（and/or）、布尔字面量。
#   可用名 = 本单元 manifest 声明的 params 键 + 预留上下文字段 pool
#      （含 all_pools: bool，由工况引擎按 condition 求值注入；点式引用
#      pool.all_pools 经 expr.parse_checked 以扁平允许名校验、求值以
#      扁平键从 bindings 取值——归一后表达式树不含 Attribute）。
#   静态校验（load_manifest 追加，R1c 执行细则）：parse_checked 通过 +
#      引用名 ⊆ params ∪ {pool.*}。
#   求值时机：executor 在调 compute 前按 ADR-007 变换参数（graph/executor
#      R2）；compute 内禁止工况 if 分支（与 ADR-007 一致）。
#
# 【行为规格】
#   R1 静态校验（加载时，失败=启动失败不是运行时警告，§3 保证 2 思想）：
#      a) 参数 field_id 必须在 dimensions 注册表登记且单位匹配 DimKey；
#      b) 端口经 ports.validate 语义合法；
#      c) 工况映射必须是受限 DSL 白名单表达式（禁止任意 Python——声明式，
#         ADR-007；DSL 定义见【工况映射 DSL】节；禁止 compute 式过程逻辑
#         混入清单）；
#      d) norm_refs 非空（无条文出处的设计参数不允许——溯源最低门槛）。
#   R2 去除率/系数只存引用键，数值在 data/coefficients 数据包（版本化，
#      随规范版本演进），清单不含魔法数。
#   R3 清单可序列化（项目文件内嵌单元版本），确定性序列化规则同 project/io。
#   R4 业务线字段 ∈ {municipal, mine_water, sludge, conveyance}（§14.3 边界）。
#
# 【测试要求】四类静态校验各自的拒绝路径、合法最小清单往返序列化无损。
#
# 【参照】重写计划 §3-5/§13.6/§14.1；数据包 data/coefficients/README.md
# ══════════════════════════════════════════════════════════════════
