"""用例编排：run_full_calc(project, conditions)——内核对外的唯一大门（L4 装配点）。

输入:  ProjectFile + 工况选择 + 数据包（单价/系数/假设）+ 单元发现结果
输出:  全厂结果包（PlantResult + ElevationProfile + SceneGraph + 概算 + 迹树）；
       T7a 份额：load_project/save_project 薄封装 + RunEnv 再导出
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 薄封装份额 D7 裁决 2026-08-25；镜像测试 tests/app/test_app.py）
#
# 【公开接口】
#   class RunEnv(不可变)：定义于 contracts/run_env.py（L0 契约），app
#       装配并重新导出——engine_version、data_version（系数+单价聚合
#       ——ARCH1 D4 定稿：包集={coefficients, unit_prices} 两包、
#       name=目录实名，见 run_env.py 规格）、assumptions、coefficients、
#       price_book、trace_sink、engine_params（引擎默认带调节影响元数据，
#       UF-08 项——T7a 已冻结数值于 registry/assumptions loop.* 三条）；
#       装配一次、执行期只读（SENS-B 2026-08-23 UF-31）
#   load_project(path: Path) -> ProjectFile / save_project(project:
#       ProjectFile, path: Path) -> None（SENS-B 2026-08-23 UF-33）：
#       经 project/io 薄封装——编排薄壳，逻辑住 L4.project-trace
#       （UF-33 口径：server 段调用终点收口本文件）
#   assemble(project: ProjectFile, env) -> AssembledGraph
#       装配：units_lib.discover_units → 按 design 节点实例化 →
#       构建图执行器入参（唯一允许接触具体单元的地点，§13.1）
#   run_full_calc(project, conditions, env) -> ResultBundle
#   run_enumeration(...) -> 枚举结果（SENS-B 2026-08-23 UF-33 新增）：
#       单单元枚举管线编排薄壳 grid→enumerate→constraints→ranking→
#       diagnose——逻辑住 solution 各子系统，本文件只穿针引线
#   export_artifact(...) -> 产物（SENS-B 2026-08-23 UF-33 新增）：
#       kind→calcbook/audit/dxf/estimate 渲染编排薄壳——逻辑住各子系统
#   class ResultBundle：plant（PlantResult）、profiles（按工况）、
#       scene（按工况 SceneGraph）、estimate（可选，需求时装配）、
#       trace（TraceTree）、repro 三元组
#
# 【T7a/T7b 分工注记】（总控 T7 拆分，2026-08-25）
#   - T7a 份额（本 commit 已落）：load_project/save_project 薄封装
#     （project.io 正门转发）+ RunEnv 再导出（经 __all__ 认可——
#     mypy no-implicit-reexport 与 ruff F401 先例 graph/__init__）。
#   - T7b 份额（保持缺省，规格冻结待实现）：assemble / run_full_calc
#     / run_enumeration / export_artifact（含 RunEnv 装配——从
#     DEFAULT_ASSUMPTIONS 提取 loop.* 三键投影 EngineParam 构造
#     engine_params，UF-08）；test_app 两例随之激活。
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
# 【参照】重写计划 §13.1 装配点/§14.3/§18.1；简报 T7a D7
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path

from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.run_env import RunEnv
from waterprint.project.io import load_project as _project_load
from waterprint.project.io import save_project as _project_save

__all__ = ["RunEnv", "load_project", "save_project"]


def load_project(path: Path) -> ProjectFile:
    """项目装载薄封装：转发 project.io 正门（UF-33——server 段终点收口）。"""
    return _project_load(path)


def save_project(project: ProjectFile, path: Path) -> None:
    """项目保存薄封装：转发 project.io 正门（原子写+确定性序列化）。"""
    _project_save(project, path)
