"""services 同层共享取数件：最近完成计算结果集+诊断件读取（复制收敛单源）。

输入:  ServiceContext + project_id + 消费方领域 404 异常工厂（not_found）
       / result bag（diag 件读取面）
输出:  (task_id, result) 二元组 / 降级变体 None / DiagnosticsReport|None
"""

# ══════════════════════════════════════════════════════════════════
# 规格（《裁决书》方案二批 2a——B3-a 2026-09-19；准入五条见下；
#   b27 2026-11-18 AUDIT-#16 扩面：四份 _load_diagnostics 逐字复制
#   〔trust/ops_debug/report/validation〕+site 降级变体收编本件——
#   行为对照表六态恒等 None 后机械合并，降级语义零变。）
#
# 【公开接口】
#   latest_calc_result(ctx, project_id, *, not_found)
#       -> (task_id, result)——六消费面（scene/elevation/cost/exports/
#       compare/trust）共享取数正门
#   latest_done_result_or_none(ctx, project_id) -> result | None
#       ——b27 收编 site 降级变体（无 done calc → None 不抛——site R2
#       可降级辅助面语义，与 404 数据源缺失语义分野记档）
#   load_diagnostics(latest) -> DiagnosticsReport | None
#       ——b27 收编四份 _load_diagnostics（trust/ops_debug/report/
#       validation 消费）
#
# 【行为规格】
#   R1 取数：遍历 ctx.manager.task_ids_for_project(project_id) 取注册序
#      最末 done calc 的 status.result（消费时实时取，UF-37 统一口径；
#      ENG4 D2 先例口径——二元组为信息超集：溯源回显面携 task_id，
#      result bag 不含该键；不需要 task_id 的消费面解包丢弃分量）。
#   R2 无结果集：raise not_found(共享消息)——异常类经参数注入（消费方
#      领域 404 面；异常→HTTP 码经 main domain_error_codes 类名义表
#      注入，收敛前后异常类型与消息文本逐字恒等——行为零变）；
#      降级变体同场景返回 None（b27——取数循环与 R1 同判，仅无结果
#      分支分野，两形态各自消费面语义保留）。
#   R3 星型单向：本件禁 import services/ 下任何消费方模块（唯一依赖
#      =services/__init__ 的 ServiceContext——包根不回指子模块，无环；
#      import-linter layers 契约同层内合法；core 面=contracts L0 只读）。
#   R4 诊断件三态降级（b27 AUDIT-#16 行为对照表——六态收敛前四份
#      恒等）：缺 diag_file 键/非字符串/空串 → None；路径不可读
#      （OSError）→ None；字节损坏（InvalidDiagnosticsError）→ None
#      （禁伪造空报告冒充——降级由消费方如实投影）；正常 →
#      DiagnosticsReport。收敛前 trust/validation 的 _NO_DIAGNOSTICS
#      模块常量与 ops_debug/report 的字面量 None 值恒等，单源后统一
#      字面量形态。
#
# 【准入五条】（《裁决书》方案二——同层晋升登记）
#   ①≥2 处真实消费：收敛前 def 复制六份（scene/elevation/cost/
#     exports_io/compare/trust）+exports 转手 import（7 消费文件）；
#     b27 扩面取数变体一份+diag 四份（准入同过——diag 件读取为纯
#     取数投影无业务分支）；
#   ②无业务分支：纯取数投影，异常类参数注入不带业务分派；
#   ③命名中性：latest_calc 不带消费方语义；
#   ④旧复制同批删除禁并存（宪法 §2）；
#   ⑤契约同步：file-contracts 登记（server 面义务）。
#
# 【测试要求】六消费面既有用例经 import 间接覆盖（行为零变收敛——
#   零新增测试文件，锁面零动作；b27 扩面同口径——四 diag 消费面
#   降级三态既有用例经 import 间接覆盖）。
# 【参照】docs/design/2026-09-18_complexity-governance-ruling.md 方案二
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from waterprint.contracts.trust import (
    DiagnosticsReport,
    InvalidDiagnosticsError,
    deserialize_diag,
)

from waterprint_server.services import ServiceContext


def latest_calc_result(
    ctx: ServiceContext, project_id: str, *, not_found: type[Exception]
) -> tuple[str, Mapping[str, Any]]:
    """最近完成计算结果集（B3-a 六处复制收敛单源——ENG4 D2 二元组口径）。

    直连消费面=scene/elevation/cost/exports/compare/trust 六处（exports_io
    为原 def 宿主，本批迁出后不计直连面）。not_found 须为单消息构造
    约定的异常类——raise not_found(msg) 调用形态，签名不符即 TypeError
    （fail-loud 非静默）。"""
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


def latest_done_result_or_none(
    ctx: ServiceContext, project_id: str
) -> Mapping[str, Any] | None:
    """最近完成计算结果集降级变体（b27 AUDIT-#16 收编 site 复制）。

    取数循环与 latest_calc_result 同判（注册序最末 done calc 实时取）；
    无结果集分支分野：返回 None 而非 raise——site 可降级辅助面 R2 语义
    （无完成计算=空报告 200，与 404 数据源缺失语义分野记档）。"""
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    return latest


def load_diagnostics(latest: Mapping[str, Any]) -> DiagnosticsReport | None:
    """诊断件读取（b27 AUDIT-#16 四份复制收敛单源）。

    三态降级：缺键/非字符串/空串、路径不可读（OSError）、字节损坏
    （InvalidDiagnosticsError）→ None 显式降级——禁伪造空报告冒充
    （消费方 diagnostics_available=False 等如实投影）。"""
    diag_file = latest.get("diag_file")
    if not isinstance(diag_file, str) or not diag_file:
        return None
    try:
        return deserialize_diag(Path(diag_file).read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return None
