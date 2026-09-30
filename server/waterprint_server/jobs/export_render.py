"""export 渲染分流件（jobs）：audit→flows.audit_render_flow，余 kind→app.export_artifact。

输入:  kind+ProjectFile+PlantResult+模板路径+输出路径（tmp）+路由选项 kwargs
输出:  渲染落盘路径（audit=flows 原子写；余 kind=export_artifact 写 tmp 由调用方 rename）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-audit-20260930 audit 501 收口批）
#
# 【公开接口】
#   _render_artifact(kind, project, plant, template, out, **options) -> Path
#       （services/exports.py 单产物段与 jobs/worker.py export_batch 逐项
#       两路径共享真源——防 audit 分流双源；参照 jobs/export_kwargs.py 先例）
#
# 【行为规格】
#   R-1 分流：kind="audit" → waterprint.flows.audit_render_flow(project,
#      plant, out)（内部 render_audit_html+tmp+os.replace 原子落盘，CLI
#      export audit 同款单一真源；路由选项零消费——unit/condition 显式
#      意图由 server 预校验 422 把守，混装批批级路由键归一层置空非此面）；
#      余 kind → app.export_artifact（UF-33 单入口）+_build_drawing_kwargs
#      组装（ifc=assumptions+site_design/dxf=site_design/余空——组装调用
#      随本件并入单源，export_kwargs 件转为本件内部消费源）。
#   R-2 纯调用零 IO 决策（渲染 IO 归 core 正门）；import 仅 waterprint.app+
#      waterprint.flows+contracts+同层 export_kwargs（jobs→flows 向下合法：
#      flows 不在 server UF-33 forbidden 面[server/pyproject 第二契约]，
#      cli 先例）；导入零副作用（Windows spawn 铁律）。
#   R-3 out 语义：调用方传唯一化 tmp 路径，渲染后由调用方 os.replace 至
#      终名（audit 双段原子=flow 内 tmp→out 再 caller out→终名，无害）。
#
# 【测试要求】routers/test_exports_audit.py 经单产物/批量两路径间接覆盖
#   （200 text/html+worker 分流）；worker 既有替身用例经 core.export_
#   artifact 模块属性面替换，本件调用点同步生效零断链。
# 【参照】任务书 exp-audit-20260930 §三.1/§三.2；AGENTS §1 层序/§13 图谱
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import Any

from waterprint import app as core
from waterprint import flows
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.result_schema import PlantResult

from waterprint_server.jobs.export_kwargs import _build_drawing_kwargs

__all__ = ["_render_artifact"]


def _render_artifact(  # 五参=export_artifact 对偶签名；**options=路由选项透传
    kind: str,
    project: ProjectFile,
    plant: PlantResult,
    template: Path,
    out: Path,
    **options: Any,
) -> Path:
    """渲染分流正门：audit=flows 流（HTML 审计报告），余 kind=app 用例。"""
    if kind == "audit":
        # audit=全厂单份 HTML：渲染/原子落盘单一真源=flows.audit_render_flow
        # （core 冻结签名——project 形参占位不实际消费，HTML 头部三元组自证）。
        return flows.audit_render_flow(project, plant, out)
    core.export_artifact(
        kind, plant, template, out,
        **_build_drawing_kwargs(kind, project), **options,
    )
    return out
