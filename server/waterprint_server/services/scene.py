"""scene 服务用例：最近完成结果集 → 三维场景图（core build_scene 纯投影）。

输入:  项目 id + condition_key（可选——缺省=结果工况排序首键，显式回显）
输出:  SceneGraph（core 冻结 dataclass——routers 响应模型直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE1 D1 2026-08-28；镜像测试 server/tests/services/test_scene.py）
#
# 【公开接口】
#   build_scene_for_project(ctx, project_id, condition_key=None)
#       -> core.SceneGraph（scene 数据通道服务面正门）
#   SceneGraph = core.SceneGraph（类型面再导出——routers 响应模型取用，
#       calculation.TaskStatus 先例：routers→core 非声明边经服务层转发）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：_latest_calc_result 复制 services/exports
#      同款取数模式（遍历 task_ids_for_project 取最末 done calc 的
#      status.result——消费时实时取，UF-37 统一口径；不 import exports
#      私有名，FE1 简报条款）；无结果集=SceneSourceNotFoundError（404
#      面，消息含"先 POST /api/calc/run"——ExportSourceNotFoundError
#      同语义）；结果文件缺失/损坏（OSError/InvalidResultError）同归
#      SceneSourceNotFoundError 404 面（FE1 M4 路径安全族——裸 500 禁）。
#   R2 工况缺省：condition_key=None → sorted(plant.conditions)[0]（显式
#      回显于 SceneGraph.condition_key——不猜测）；工况不在结果 =
#      core.build_scene 的 KeyError 转 InvalidSceneRequestError（422 面，
#      消息透传 KeyError 文本含合法工况集）。
#   R3 假设合成视图：{entry.key: entry.default for DEFAULT_ASSUMPTIONS}
#      + design.assumption_overrides（jobs.worker._build_env 同款三行
#      口径——计算与投影假设面一致，双源漂移根除）。
#   R4 确定性继承：同结果集同场景图（core R1 纯投影——服务层零加料，
#      双跑 asdict(sort_keys) 字节同，端点测试常驻断言）。
#
# 【测试要求】缺省工况回显、双跑字节同、422/404 异常面、
#   项目不存在（read_project 先于取数——ProjectNotFoundError 既有面）。
#
# 【参照】重写计划 §10.5/§12.2；FE1 简报 D1；UF-33（core 只经 waterprint.app）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from waterprint import app as core
from waterprint.contracts.result_schema import InvalidResultError, deserialize

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project

# SceneGraph 再导出（routers 响应模型面——routers→core 非声明边，分层 §13.4；
# calculation.TaskStatus 再导出先例）。__all__ 只列服务面公开符号。
__all__ = ["InvalidSceneRequestError", "SceneGraph", "SceneSourceNotFoundError",
           "build_scene_for_project"]
SceneGraph = core.SceneGraph


class SceneSourceNotFoundError(RuntimeError):
    """无最近完成结果集可消费——404 面（先运行计算）。"""


class InvalidSceneRequestError(ValueError):
    """scene 请求非法（工况不在结果）——422 面（透传 build_scene KeyError 文本）。"""


def _latest_calc_result(ctx: ServiceContext, project_id: str) -> Mapping[str, Any]:
    """最近完成计算结果集（exports._latest_calc_result 同款取数模式复制）。"""
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    if latest is None:
        raise SceneSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return latest


def build_scene_for_project(
    ctx: ServiceContext, project_id: str, condition_key: str | None = None
) -> core.SceneGraph:
    """场景图正门：项目校验 → 结果集取数 → 反序列化 → 假设合成 → core 投影。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    latest = _latest_calc_result(ctx, project_id)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        # FE1 M4（路径安全族）：结果文件缺失/损坏归一 404 领域面——裸 500 禁。
        raise SceneSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    chosen = condition_key if condition_key is not None else sorted(plant.conditions)[0]
    assumptions = {entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)
    try:
        return core.build_scene(plant, assumptions, chosen)
    except KeyError as exc:
        raise InvalidSceneRequestError(str(exc)) from exc
