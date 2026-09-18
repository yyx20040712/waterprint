"""services 同层共享取数件：最近完成计算结果集（六处复制收敛单源）。

输入:  ServiceContext + project_id + 消费方领域 404 异常工厂（not_found）
输出:  (task_id, result) 二元组——注册序最末 done calc 的任务号与结果集
"""

# ══════════════════════════════════════════════════════════════════
# 规格（《裁决书》方案二批 2a——B3-a 2026-09-19；准入五条见下）
#
# 【公开接口】
#   latest_calc_result(ctx, project_id, *, not_found)
#       -> (task_id, result)——六消费面（scene/elevation/cost/exports/
#       compare/trust）共享取数正门
#
# 【行为规格】
#   R1 取数：遍历 ctx.manager.task_ids_for_project(project_id) 取注册序
#      最末 done calc 的 status.result（消费时实时取，UF-37 统一口径；
#      ENG4 D2 先例口径——二元组为信息超集：溯源回显面携 task_id，
#      result bag 不含该键；不需要 task_id 的消费面解包丢弃分量）。
#   R2 无结果集：raise not_found(共享消息)——异常类经参数注入（消费方
#      领域 404 面；异常→HTTP 码经 main domain_error_codes 类名义表
#      注入，收敛前后异常类型与消息文本逐字恒等——行为零变）。
#   R3 星型单向：本件禁 import services/ 下任何消费方模块（唯一依赖
#      =services/__init__ 的 ServiceContext——包根不回指子模块，无环；
#      import-linter layers 契约同层内合法）。
#
# 【准入五条】（《裁决书》方案二——同层晋升登记）
#   ①≥2 处真实消费：收敛前 def 复制六份（scene/elevation/cost/
#     exports_io/compare/trust）+exports 转手 import（7 消费文件）；
#   ②无业务分支：纯取数投影，异常类参数注入不带业务分派；
#   ③命名中性：latest_calc 不带消费方语义；
#   ④旧复制同批删除禁并存（宪法 §2）；
#   ⑤契约同步：file-contracts 登记（server 面义务）。
#
# 【测试要求】六消费面既有用例经 import 间接覆盖（行为零变收敛——
#   零新增测试文件，锁面零动作）。
# 【参照】docs/design/2026-09-18_complexity-governance-ruling.md 方案二
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from waterprint_server.services import ServiceContext


def latest_calc_result(
    ctx: ServiceContext, project_id: str, *, not_found: type[Exception]
) -> tuple[str, Mapping[str, Any]]:
    """最近完成计算结果集（B3-a 六处复制收敛单源——ENG4 D2 二元组口径）。"""
    task_id: str = ""
    latest: Mapping[str, Any] | None = None
    for candidate in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(candidate)
        if status.kind == "calc" and status.state == "done" and status.result:
            task_id, latest = candidate, status.result
    if latest is None:
        raise not_found(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return task_id, latest
