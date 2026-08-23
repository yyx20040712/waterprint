"""用例编排：run_full_calc(project, conditions)——内核对外的唯一大门（L4 装配点）。

输入:  ProjectFile + 工况选择 + 数据包（单价/系数/假设）+ 单元发现结果
输出:  全厂结果包（PlantResult + ElevationProfile + SceneGraph + 概算 + 迹树）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/app/test_app.py）
#
# 【公开接口】
#   class RunEnv(不可变)：定义于 contracts/run_env.py（L0 契约），app
#       装配并重新导出——engine_version、data_version（系数+单价聚合）、
#       assumptions、coefficients、price_book、trace_sink、engine_params
#       （引擎默认带调节影响元数据，UF-08 项 T4/T7 冻结数值）；装配一次、
#       执行期只读（SENS-B 2026-08-23 UF-31）
#   assemble(project: ProjectFile, env) -> AssembledGraph
#       装配：units_lib.discover_units → 按 design 节点实例化 →
#       构建图执行器入参（唯一允许接触具体单元的地点，§13.1）
#   run_full_calc(project, conditions, env) -> ResultBundle
#   run_enumeration(...) -> 枚举结果（SENS-B 2026-08-23 UF-33 新增）：
#       单单元枚举管线编排薄壳 grid→enumerate→constraints→ranking→
#       diagnose——逻辑住 solution 各子系统，本文件只穿针引线
#   export_artifact(...) -> 产物（SENS-B 2026-08-23 UF-33 新增）：
#       kind→calcbook/audit/dxf/estimate 渲染编排薄壳——逻辑住各子系统
#   load_project/save_project（SENS-B 2026-08-23 UF-33 新增）：经
#       project/io 薄封装——编排薄壳，逻辑住 L4.project-trace
#   class ResultBundle：plant（PlantResult）、profiles（按工况）、
#       scene（按工况 SceneGraph）、estimate（可选，需求时装配）、
#       trace（TraceTree）、repro 三元组
#
# 【行为规格】
#   R1 装配/执行分离：assemble 阶段发现失败（重复 unit_id/清单非法/
#      失联引用）= 启动期失败清单（全部报告，不是逐个崩溃）；
#      run 阶段只执行。
#   R2 编排顺序（全流程用例）：execute_graph（逐工况）→ elevation
#      profile → geometry scene → （按需）cost estimate / drafting /
#      trace 消费——子系统经总线数据衔接，本文件是唯一穿针引线处
#      （L3 互不 import 的代价在装配层兑现）。
#   R3 幂等与可复算：同 (project, conditions, env) 双跑 ResultBundle
#      序列化字节级相同；服务层以 (design_hash, condition) 为幂等键
#      直接复用（§15 工程细节 3）。
#   R4 旧项目导入（M4）：import_legacy 入口在此编排（migration 链 +
#      best-effort 字段映射报告），与 run_full_calc 平行，不混流。
#   R5 性能：全流程（32 单元 × 2+k 工况，含回路）<5s（§18.1 基准
#      门禁的主测点）。
#
# 【测试要求】三单元 M1 切片端到端、装配失败清单完整、双跑 diff=0、
#   三元组传播、（golden 数据就绪后）两大案例全流程。
#
# 【参照】重写计划 §13.1 装配点/§14.3/§18.1
# ══════════════════════════════════════════════════════════════════
