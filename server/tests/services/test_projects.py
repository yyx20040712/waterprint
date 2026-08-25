"""projects 服务镜像测试：保存语义（design_changed）、导入完整性。

输入:  waterprint_server.services.projects 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.projects")
save_project = getattr(_mod, "save_project")
import_legacy = getattr(_mod, "import_legacy")
create_project = getattr(_mod, "create_project")
read_project = getattr(_mod, "read_project")

pytestmark = [
    pytest.mark.skipif(
        None in (save_project, import_legacy),
        reason="实现未就绪：waterprint_server.services.projects（服务层 M2/M4）",
    ),
    pytest.mark.anyio,
]


async def _created(ctx, payload=None):  # type: ignore[no-untyped-def]
    """创建并返回 (project_id, ProjectFile)。"""
    outcome = create_project(ctx, payload or {})
    return outcome.project_id, read_project(ctx, outcome.project_id)


async def test_view_only_save_reports_no_design_change_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：仅改 view 态的保存 design_changed=False（§17.1）。"""
    project_id, project = await _created(service_ctx)
    view_only = project.model_copy(
        update={"view": project.view.model_copy(update={"timestamp": "2026-08-26T01:00:00Z"})}
    )
    outcome = save_project(service_ctx, project_id, view_only)
    assert outcome.design_changed is False  # view 态不入哈希（R10 病灶根除）
    design_changed = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"nodes": {**project.design.nodes, "extra_unit": {"x": 1.0}}}
            )
        }
    )
    outcome = save_project(service_ctx, project_id, design_changed)
    assert outcome.design_changed is True  # design 变更区分（R2 dirty 语义）


async def test_legacy_import_lists_unmapped_fields_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R3 接线断言（M4 归属·简报 SERVER D3 未就绪语义实质化）。

    import_legacy 显式未就绪（ImportNotReadyError→501）——不假装功能；
    未映射字段清单（ImportReport.unmapped）的完整性断言归 M4 接线批。
    """
    with pytest.raises(_mod.ImportNotReadyError, match="M4"):
        import_legacy(service_ctx, {"legacy": {"未知字段": 1}})
