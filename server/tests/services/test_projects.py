"""projects 服务镜像测试：保存语义（design_changed）、导入完整性
+约束勾选 PUT 变体（CP2 D6①——constraint_choices 持久/哈希/stale/解勾）。

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
result_is_stale = getattr(_mod, "result_is_stale")

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


# ═══ CP2 D6①（约束勾选持久化 2026-09-01）：PUT constraint_choices 变体 ═══

_KEY = "vxinglvchi.v_filter_band"  # kb 真键（vxinglvchi 滤速带——D7 键域宽不校验入 kb）


def _with_choices(project, choices: dict[str, str]):  # type: ignore[no-untyped-def]
    """design 仅换 constraint_choices 的 model_copy（PUT 全量载荷形态）。"""
    return project.model_copy(
        update={"design": project.design.model_copy(update={"constraint_choices": choices})}
    )


async def test_constraint_choices_persist_and_stale_linkage_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """CP2 D6①：PUT 含勾选→design_changed=True+content_hash 变+持久回读
    +旧结果 result_is_stale=True 联动+同 choices 重存 no-op。"""
    outcome0 = create_project(service_ctx, {})
    project_id = outcome0.project_id
    project = read_project(service_ctx, project_id)
    assert project.design.constraint_choices == {}  # 初始空（D1 复用既有字段）
    checked = _with_choices(project, {_KEY: "on"})
    outcome1 = save_project(service_ctx, project_id, checked)
    assert outcome1.design_changed is True  # 勾选变更计入 design 态
    assert outcome1.content_hash != outcome0.content_hash  # design_digest 随勾选变
    persisted = read_project(service_ctx, project_id)
    assert persisted.design.constraint_choices == {_KEY: "on"}  # 落盘持久铁证
    # stale 联动（services/projects.py result_is_stale——三读端点同源口径）：
    # 旧结果锚定旧 digest → 过期；锚定新 digest → 新鲜；缺键 fail-visible
    assert result_is_stale({"design_hash": outcome0.content_hash}, persisted) is True
    assert result_is_stale({"design_hash": outcome1.content_hash}, persisted) is False
    assert result_is_stale({}, persisted) is True
    # 同 choices 重复保存=no-op（design 态等值——不产空变更）
    outcome2 = save_project(service_ctx, project_id, checked)
    assert outcome2.design_changed is False
    assert outcome2.content_hash == outcome1.content_hash


async def test_constraint_choices_uncheck_returns_to_empty_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """CP2 D6①续：解勾删键回空（{}）→design_changed=True+digest 回环
    （确定性序列化——同 design 态哈希字节同）。"""
    outcome0 = create_project(service_ctx, {})
    project_id = outcome0.project_id
    project = read_project(service_ctx, project_id)
    checked = _with_choices(project, {_KEY: "on"})
    save_project(service_ctx, project_id, checked)
    cleared = _with_choices(project, {})
    outcome = save_project(service_ctx, project_id, cleared)
    assert outcome.design_changed is True  # 解勾也是 design 变更
    assert outcome.content_hash == outcome0.content_hash  # 回环=初始空档 digest
    assert read_project(service_ctx, project_id).design.constraint_choices == {}
