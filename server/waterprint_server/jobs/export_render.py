"""export 渲染分流件（jobs）：audit/estimate→flows 渲染流，余 kind→app.export_artifact。

输入:  kind+ProjectFile+PlantResult+模板路径+输出路径（tmp）+路由选项 kwargs
输出:  渲染落盘路径（flows 流=内部原子写；余 kind=export_artifact 写 tmp 由调用方 rename）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-audit-20260930 audit 501 收口批；est-20261001 estimate
#   501 收口批扩 estimate 分支+data_dir 形参）
#
# 【公开接口】
#   _render_artifact(kind, project, plant, template, out, *, data_dir=None,
#                    **options) -> Path
#       （services/exports.py 单产物段与 jobs/worker.py export_batch 逐项
#       两路径共享真源——防分流双源；参照 jobs/export_kwargs.py 先例）
#
# 【行为规格】
#   R-1 分流：kind="audit" → waterprint.flows.audit_render_flow(project,
#      plant, out)（内部 render_audit_html+tmp+os.replace 原子落盘，CLI
#      export audit 同款单一真源；路由选项零消费——unit/condition 显式
#      意图由 server 预校验 422 把守，混装批批级路由键归一层置空非此面）；
#      kind="estimate" → waterprint.flows.estimate_render_flow(project,
#      plant, out, condition_key=…, data_dir=…)（est-20261001：概算 xlsx
#      渲染流——计算链单源复用+原子落盘；template 形参不消费[audit 同款
#      占位]；data_dir 必填——None 即 InvalidFlowError 中文消息[装配层
#      接线缺陷面，非用户输入域]；condition_key 缺省/空串归一 "design"
#      [D4 归一层同源口径——services/exports.py 单点归一后的防线兜底]；
#      其余路由选项零消费[unit/六路由键携带已由预校验 422 把守]）；
#      余 kind → app.export_artifact（UF-33 单入口）+_build_drawing_kwargs
#      组装（ifc=assumptions+site_design/dxf=site_design/余空——组装调用
#      随本件并入单源，export_kwargs 件转为本件内部消费源）。
#   R-2 纯调用零 IO 决策（渲染 IO 归 core 正门）；import 仅 waterprint.app+
#      waterprint.flows+contracts+同层 export_kwargs（jobs→flows 向下合法：
#      flows 不在 server UF-33 forbidden 面[server/pyproject 第二契约]，
#      cli 先例）；导入零副作用（Windows spawn 铁律）。
#   R-3 out 语义：调用方传唯一化 tmp 路径，渲染后由调用方 os.replace 至
#      终名（flows 双段原子=流内 tmp→out 再 caller out→终名，无害）。
#
# 【测试要求】routers/test_exports_audit.py+test_exports_estimate.py 经
#   单产物/批量两路径间接覆盖（200 流+worker 分流）；worker 既有替身
#   用例经 core.export_artifact 模块属性面替换，本件调用点同步生效零断链。
# 【参照】任务书 exp-audit-20260930 §三.1/§三.2；est-20261001 §三 D2/D4；
#   AGENTS §1 层序/§13 图谱
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

# est-20261001 D4：estimate 项 condition_key 缺省/空串边界归一（归一层
# services/exports.py 单点；此处=防线兜底同值——直接调用面[worker 直构
# payload]与 server 面同语义，零第二真源漂移）。
_ESTIMATE_DEFAULT_CONDITION = "design"


def _render_artifact(  # noqa: PLR0913  # 六参=export_artifact 对偶签名+data_dir（estimate 装载面——规格冻结签名豁免先例：exports.create_export）
    kind: str,
    project: ProjectFile,
    plant: PlantResult,
    template: Path,
    out: Path,
    *,
    data_dir: Path | None = None,
    **options: Any,
) -> Path:
    """渲染分流正门：audit/estimate=flows 流，余 kind=app 用例。"""
    if kind == "audit":
        # audit=全厂单份 HTML：渲染/原子落盘单一真源=flows.audit_render_flow
        # （core 冻结签名——project 形参占位不实际消费，HTML 头部三元组自证）。
        return flows.audit_render_flow(project, plant, out)
    if kind == "estimate":
        # estimate=概算 xlsx：渲染/原子落盘单一真源=flows.estimate_render_flow
        # （template 形参占位不消费——audit 先例；data_dir=单价包装载面必填）。
        if data_dir is None:
            raise flows.InvalidFlowError(
                "estimate 渲染缺少 data_dir（数据包根——单价包/费率装载面；"
                "server 装配层提交时须透传 ctx.settings.data_dir）"
            )
        return flows.estimate_render_flow(
            project, plant, out,
            condition_key=(
                str(options.get("condition_key") or "")
                or _ESTIMATE_DEFAULT_CONDITION
            ),
            data_dir=data_dir,
        )
    core.export_artifact(
        kind, plant, template, out,
        **_build_drawing_kwargs(kind, project), **options,
    )
    return out
