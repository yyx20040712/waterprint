"""export_batch worker 卫生面镜像测试：exp-hygiene-20260930（H1 通用边车+H2 异常族）。

输入:  waterprint_server.jobs.worker（export_batch 边车/项级失败族扩面）
输出:  批量任务行为契约断言（通用边车分支/K-02 取消守卫/flows 族收集）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-hygiene-20260930 exports 卫生批·worker 锚——本批新增件；
#   test_worker_batch.py 559 行顶 AGENTS §2 预算墙拆件，公共前置束经
#   命名空间包导入共享零复制〔pythonpath=. 先例〕）。
#
# 【覆盖面】
#   - H2：_ITEM_FAILURES 扩 flows 异常三件（InvalidFlowError/InvalidAudit
#     Error/InvalidAuditPathError）——audit 项渲染异常→failures 收集不炸
#     批（部分失败=done；未扩族前=异常上抛任务 failed）；
#   - H1：worker 通用边车分支（audit/calcbook/estimate 项 sidecars={kind
#     名本名}→{产物}.meta.json 落盘）+写盘前 K-02 同款取消检查（取消后
#     零新边车）。
# 【替身口径】flows.audit_render_flow/core.export_artifact monkeypatch 替身
#   （test_worker_batch.py 同款——真 calc 结果文件经 deserialize 正门）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path

import pytest

from tests.jobs.test_worker_batch import (
    _batch_payload,
    _item,
    _project_and_result,
    run_task,
)

pytestmark = [pytest.mark.anyio]


async def test_export_batch_audit_exception_family_collected_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """H2（exp-hygiene-20260930）：worker 项级失败族扩 flows 异常三件
    （InvalidFlowError/InvalidAuditError/InvalidAuditPathError——server 面
    经 flows 再导出取用）——audit 项渲染异常→failures 收集不炸批（部分
    失败=done；未扩族前=异常上抛任务 failed）。"""
    from waterprint import app as core
    from waterprint import flows

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    family = {
        "a": flows.InvalidFlowError,
        "b": flows.InvalidAuditError,
        "c": flows.InvalidAuditPathError,
    }

    def _raise_by_item(project, plant, out):  # type: ignore[no-untyped-def]
        stem = Path(out).name.split(".", maxsplit=1)[0]
        exc = family[stem]
        raise exc(f"injected {exc.__name__} (H2)")

    def _ok_non_audit(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        Path(out).write_bytes(b"ok")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(flows, "audit_render_flow", _raise_by_item)
        mp.setattr(core, "export_artifact", _ok_non_audit)
        result = run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [
                    _item("audit", "a.html"),
                    _item("audit", "b.html"),
                    _item("audit", "c.html"),
                    _item("dxf", "d.dxf", condition_key="design"),
                ],
            ),
            None,
            None,
        )
    assert result["state"] == "done"  # 族内异常=项级失败收集（不炸批）
    assert len(result["files"]) == 1  # dxf 项照常落盘
    failures = list(result["failures"])
    assert [f["index"] for f in failures] == [0, 1, 2]
    assert "InvalidFlowError" in str(failures[0]["error"])
    assert "InvalidAuditError" in str(failures[1]["error"])
    assert "InvalidAuditPathError" in str(failures[2]["error"])


async def test_export_batch_generic_kind_sidecar_written_and_cancel_guard_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """H1（exp-hygiene-20260930）worker 通用边车分支：audit 项携
    sidecars={"audit": 文本} 渲染成功→{产物}.meta.json 落盘（注册表扫描
    面入册）；写盘前取消（K-02 同款取消检查）→cancelled 且零新边车。"""
    from waterprint import flows

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cancel_flag = tmp_path / "cancel.flag"

    def _write_ok(project, plant, out):  # type: ignore[no-untyped-def]
        Path(out).write_text("<html>ok</html>", encoding="utf-8")

    items: list[dict[str, object]] = [
        {**_item("audit", "a.html"), "sidecars": {"audit": '{"kind": "audit-a"}'}},
        {**_item("audit", "b.html"), "sidecars": {"audit": '{"kind": "audit-b"}'}},
    ]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(flows, "audit_render_flow", _write_ok)
        result = run_task(
            _batch_payload(project_path, result_file, out_dir, [items[0]]),
            None,
            None,
        )
    assert result["state"] == "done"
    assert (out_dir / "a.html").is_file()
    sidecar = out_dir / "a.html.meta.json"
    assert sidecar.is_file()  # 通用分支落盘（曾仅 dxf/ifc 有边车）
    assert sidecar.read_text(encoding="utf-8") == '{"kind": "audit-a"}'  # 文本逐字

    def _write_then_flag(project, plant, out):  # type: ignore[no-untyped-def]
        Path(out).write_text("<html>ok</html>", encoding="utf-8")
        cancel_flag.write_text("cancel", encoding="utf-8")  # 渲染后置令牌

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(flows, "audit_render_flow", _write_then_flag)
        result = run_task(
            _batch_payload(project_path, result_file, out_dir, [items[1]]),
            str(cancel_flag),
            None,
        )
    assert result["state"] == "cancelled"  # 边车写盘前取消（K-02 口径）
    assert (out_dir / "b.html").is_file()  # 已落产物不可撤（诚实清单）
    assert not (out_dir / "b.html.meta.json").exists()  # 取消后零新边车
