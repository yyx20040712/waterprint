"""export_batch kwargs 组装件（jobs）：core 调用参数的序列化侧真源。

输入:  kind（导出产物类）+ProjectFile（worker 侧 load_project 重建）
输出:  core.export_artifact extra kwargs dict（dxf/ifc 图纸族装配面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（SVRB D2④ 2026-09-05：_build_drawing_kwargs 自 services/
# exports.py 迁入——worker 需消费而 worker→services 上行违分层契约
# （lint-imports layers main→routers→services→jobs→settings）；函数=
# core 调用参数组装属 jobs「序列化与调用 core」职责域（§13.4），
# services/exports.py 改 from ..jobs.export_kwargs import（services→
# jobs 向下合法）；ENG8 终名+docstring 随迁。
#
# 【行为规格】
#   R-1 纯函数零 IO 零全局态；import 仅 stdlib typing+waterprint.app+
#      waterprint.contracts（UF-33 单入口口径与 worker 同款）。
#   R-2 导入零副作用（Windows spawn 铁律——AGENTS §1；本模块只做函数
#      定义，禁模块级可变全局/连接/打印）。
#
# 【测试要求】services/exports 既有用例经 import 透传间接覆盖+worker
#   面新增通道用例（tests/jobs/test_worker_batch.py）。
#
# 【参照】SVRB 简报 D2④；重写计划 §13.4/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

from waterprint import app as core
from waterprint.contracts.project_schema import ProjectFile


def _build_drawing_kwargs(kind: str, project: ProjectFile) -> dict[str, Any]:
    """dxf·ifc 族出图 kwargs 组装（SC1 D7/M5，ENG7 P3b 自 create_export 抽出；
    SVRB 自 services/exports.py 随迁本件——worker 批量面与单产物路径共享真源）。

    ifc 附 assumptions+site_design（scene 服务同口径假设合成视图）、dxf 附
    site_design（unit_id 缺省=全厂总图——SVRB 起批量面同款透传）；余 kind
    空 dict——core.export_artifact extra 面。
    """
    if kind == "ifc":
        merged = {e.key: e.default for e in core.DEFAULT_ASSUMPTIONS}
        merged |= project.design.assumption_overrides
        return {"assumptions": merged, "site_design": project.design.site}
    if kind == "dxf":
        return {"site_design": project.design.site}
    return {}
