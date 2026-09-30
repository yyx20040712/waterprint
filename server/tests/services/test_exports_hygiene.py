"""exports 服务卫生面镜像测试：exp-hygiene-20260930（H7 单产物两源收口）。

输入:  waterprint_server.services.exports 单产物段（渲染 kwargs/命名/注册表）
输出:  「1 项/2 项不分叉」契约断言（condition_key/sheet 两键三面同源）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-hygiene-20260930 exports 卫生批·services 锚——本批新增
#   件；test_exports.py 555 行顶 AGENTS §2 预算墙拆件，公共前置束经命名
#   空间包导入共享零复制〔pythonpath=. 先例〕）。
#
# 【覆盖面】
#   - H7：显式 items 单产物渲染 kwargs 的 condition_key/sheet 改读
#     items[0] 归一值——与命名/注册表三面同源（渲染曾读端点
#     condition_key/批级 sheet_option=跨面分叉缺陷收口；默认单 item 已
#     种子端点值=零回归）。
# 【替身口径】services.exports._render_artifact monkeypatch 侦听替身
#   （kwargs 捕获+tmp 落位保 os.replace 真码路径）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path

import pytest

from tests.services.test_exports import _project_with_result

_exports_mod = pytest.importorskip("waterprint_server.services.exports")
create_export = getattr(_exports_mod, "create_export")
list_exports = getattr(_exports_mod, "list_exports")

pytestmark = [pytest.mark.anyio]


def _capture_render(captured: list[dict[str, object]]):  # type: ignore[no-untyped-def]
    """渲染侦听替身工厂（kwargs 捕获+tmp 落位——os.replace 真码可续）。"""

    def _capture(  # type: ignore[no-untyped-def]  # 替身签名镜像被测接口（jobs.export_render._render_artifact）
        kind, project, plant, template, out, **options
    ):
        captured.append({"kind": kind, **options})
        Path(out).write_bytes(b"h7")

    return _capture


async def test_single_item_condition_key_render_and_naming_same_source_wiring(
    service_ctx, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """H7（exp-hygiene-20260930）「1 项/2 项不分叉」：显式 items 单产物
    渲染 kwargs 的 condition_key 改读 items[0] 归一值（item 自有优先）
    ——与命名/注册表三面同源（渲染曾读端点值=跨面分叉缺陷收口）。"""
    project_id = await _project_with_result(service_ctx)
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(_exports_mod, "_render_artifact", _capture_render(captured))
    handle = await create_export(
        service_ctx, project_id, "dxf", "design",
        {"items": [{"kind": "dxf", "condition_key": "avg"}]},
    )
    assert handle.task_id is None  # 单产物即时生成（≤即时上限）
    assert captured[0]["condition_key"] == "avg"  # 渲染=item 自有（曾读端点 "design"）
    assert "-dxf-avg-" in Path(handle.path).name  # 命名同源（item 自有）
    metas = [m for m in list_exports(service_ctx, project_id) if m.kind == "dxf"]
    assert metas and metas[-1].condition_key == "avg"  # 注册表同源（ExportMeta 读 items[0] 值）


async def test_single_item_sheet_render_and_naming_same_source_wiring(
    service_ctx, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """H7（exp-hygiene-20260930）sheet 两源收口：批级 sheet+item 级 unit
    并存时归一层 unit 项不继承批级 sheet（命名/批量路径既有语义）——渲染
    kwargs 同读 items[0] 归一值（曾读批级 sheet_option=渲染/命名分叉，
    且 core sheet×unit 互斥闸必败面）。"""
    project_id = await _project_with_result(service_ctx)
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(_exports_mod, "_render_artifact", _capture_render(captured))
    handle = await create_export(
        service_ctx, project_id, "dxf", "design",
        {
            "sheet": "profile",
            "items": [
                {"kind": "dxf", "unit_id": "municipal_cass", "condition_key": "design"}
            ],
        },
    )
    assert handle.task_id is None  # 单产物即时生成
    assert captured[0]["sheet"] is None  # 渲染=归一值（unit 项不继承批级 sheet——曾 "profile"）
    assert captured[0]["unit_id"] == "municipal_cass"  # unit 项面零回归（上批已读 items[0]）
    name = Path(handle.path).name
    assert "-dxf-municipal_cass-design-" in name  # 命名=unit 项形态
    assert "profile" not in name  # 命名/渲染两源同拍（无 -profile- 段）
