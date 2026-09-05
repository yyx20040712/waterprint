"""exports 下载校验服务镜像测试（EXPD 甲案：resolve_export_file）。

输入:  waterprint_server.services.exports 下载面（service_ctx 直测）
输出:  合法名解析/坏 stem/坏后缀族/缺产物/缺边车七例契约断言
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（EXPD 甲案下载端点批 2026-09-05·简报 §2.1 D1/D2+§2.5）
#
# 【覆盖面】七例（简报 §2.5 服务层镜像清单逐项）：
#   1. 合法在册名→绝对路径（=create_export 落盘件真身）；
#   2. 坏 stem（a.b.dxf——stem 含点）→InvalidExportRequestError（422 面）；
#   3. 坏后缀（.meta.json 边车名）→InvalidExportRequestError；
#   4. 无后缀（tasks=产物任务目录名）→InvalidExportRequestError；
#   5. 后缀白名单外族（X.DXF 大小写+.xlsx 纯后缀名 suffix==""）→
#      InvalidExportRequestError；
#   6. 合法名缺产物→ExportFileNotFoundError（404 面）；
#   7. 产物在而边车缺（真导出后删边车）→ExportFileNotFoundError
#      （注册口径双闸——简报 D2：detail 分述产物缺/边车缺）。
# 【闸序断言】422 先于 404（格式错先判防存在性泄露——简报 D2）：
#   坏名例（2-5）断 InvalidExportRequestError 即证后缀/stem 闸先于
#   存在性双闸（422 而非 404）。
# 【R 轮增补（D-G1-01/G1-07+总控实锤 2026-09-05）】：
#   R1 恒等闸镜像——反斜杠/盘符名 422（Windows pathlib 视 \ 为分隔符
#   致 stem 取末段过闸+拼接逃逸任意读；match 两态注记：POSIX 反斜杠
#   非分隔符由 stem 字符集闸兜——双 OS 闭合）；
#   R2 长名镜像——72 字符 composite stem 在册合法（validate_component
#   {0,63} 全长上界属 settings 单分量语义，不适用多分量拼接全名——
#   municipal_vxinglvchi 全厂 stem 实测在册而 422 缺陷收口）。
# 【落位注记】EXPD 拆件（宪法 §2 行预算 ≤500——services/test_exports.py
#   443 行满载；test_exports_dwg.py 按面拆件先例），_project_with_result
#   内嵌同款（跨测试件 import 无门禁面）。
# 【参照】EXPD 简报 §2.1；AGENTS §18 路径安全
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.services.exports")
create_export = getattr(_mod, "create_export")
# EXPD 红先行纪律（AGENTS §6「先失败一次」）：resolve_export_file 缺席=用例
# 体内 TypeError/AttributeError 实红（不进 skipif 守卫——skip≠红）。
resolve_export_file = getattr(_mod, "resolve_export_file", None)

calculation_mod = importlib.import_module("waterprint_server.services.calculation")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        create_export is None,
        reason="实现未就绪：waterprint_server.services.exports（服务层 M2/M3）",
    ),
    pytest.mark.anyio,
]


async def _project_with_result(ctx) -> str:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（test_exports.py 同款——导出消费前提）。"""
    outcome = projects_mod.create_project(
        ctx,
        {
            "project": {
                "format_version": "1.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7 / 86400,
                            "kz": 1.4,
                            "CODCR": 400.0,
                            "BOD5": 200.0,
                            "SS": 250.0,
                            "NH3N": 26.0,
                            "TN": 43.0,
                            "TP": 6.5,
                        },
                        "municipal_cass": {},
                    },
                    "edges": [
                        {
                            "src": {"unit_id": "inlet", "port_id": "out"},
                            "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                        }
                    ],
                },
                "view": {},
                "metadata": {
                    "format_version": "1.0",
                    "content_hash": "0",
                    "engine_version": "0",
                    "data_version": "0",
                },
            }
        },
    )
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(ctx, project_id, [])
    for _ in range(200):
        if ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert ctx.manager.status(handle.task_id).state == "done"
    return project_id


async def _real_calcbook_name(ctx) -> str:  # type: ignore[no-untyped-def]
    """真导出一次 calcbook→产物名（合法在册名——例1/例7 前置）。"""
    project_id = await _project_with_result(ctx)
    handle = await create_export(ctx, project_id, "calcbook")
    return str(Path(handle.path).name)


async def test_resolve_export_file_legal_name_returns_absolute_path_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例1：合法在册名→绝对路径（=create_export 落盘件真身）。"""
    file_name = await _real_calcbook_name(service_ctx)
    resolved = resolve_export_file(service_ctx, file_name)  # type: ignore[misc]
    assert isinstance(resolved, Path)
    assert resolved.is_absolute()
    assert resolved.is_file()
    assert resolved == Path(service_ctx.exports_dir / file_name).resolve()


async def test_resolve_export_file_bad_stem_rejected_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例2：坏 stem（a.b.dxf 含点）→InvalidExportRequestError（422 面）。"""
    with pytest.raises(_mod.InvalidExportRequestError, match="stem"):
        resolve_export_file(service_ctx, "a.b.dxf")  # type: ignore[misc]


async def test_resolve_export_file_sidecar_suffix_rejected_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例3：边车名（.meta.json 后缀）→InvalidExportRequestError（422 面）。"""
    with pytest.raises(_mod.InvalidExportRequestError, match="后缀"):
        resolve_export_file(service_ctx, "p1-calcbook-all-0123456789.xlsx.meta.json")  # type: ignore[misc]


async def test_resolve_export_file_no_suffix_rejected_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例4：无后缀名（tasks=产物任务目录名）→InvalidExportRequestError（422 面）。"""
    with pytest.raises(_mod.InvalidExportRequestError, match="后缀"):
        resolve_export_file(service_ctx, "tasks")  # type: ignore[misc]


async def test_resolve_export_file_suffix_family_rejected_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例5：后缀白名单外族——大小写 .DXF+纯后缀名 .xlsx（suffix==""）→422 面。"""
    for name in ("P1-DXF-DESIGN-0123456789.DXF", ".xlsx"):
        with pytest.raises(_mod.InvalidExportRequestError, match="后缀"):
            resolve_export_file(service_ctx, name)  # type: ignore[misc]


async def test_resolve_export_file_missing_product_raises_404_face_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例6：合法名产物缺→ExportFileNotFoundError（404 面）。"""
    with pytest.raises(_mod.ExportFileNotFoundError, match="不存在"):
        resolve_export_file(service_ctx, "p1-dxf-c-0123456789.dxf")  # type: ignore[misc]


async def test_resolve_export_file_missing_sidecar_raises_404_face_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 服务镜像例7：产物在而边车缺（真导出后删边车）→ExportFileNotFoundError（双闸）。"""
    import os

    file_name = await _real_calcbook_name(service_ctx)
    os.remove(service_ctx.exports_dir / f"{file_name}.meta.json")
    with pytest.raises(_mod.ExportFileNotFoundError, match="边车"):
        resolve_export_file(service_ctx, file_name)  # type: ignore[misc]


# R2 回归锚名：72 字符 composite stem（拼接形——各分量合法而全长超 64 分量上界）。
_LONG_STEM_NAME = (
    "golden-municipal-vxinglvchi-demo-project-dxf-design-0123456789abcdefghij.dxf"
)


async def test_resolve_export_file_long_stem_in_registry_returns_path_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPDR2 服务镜像：stem>64 长名在册合法（72 字符拼接形——分量上界不适用全名）。"""
    import os

    stem = _LONG_STEM_NAME[: -len(".dxf")]
    assert len(stem) > 64  # 回归锚：R2 前此名被 validate_component {0,63} 拒
    product = service_ctx.exports_dir / _LONG_STEM_NAME
    sidecar = service_ctx.exports_dir / f"{_LONG_STEM_NAME}.meta.json"
    product.write_bytes(b"EXPD-R2-LONG-STEM")  # 直接落盘+边车（在册形态）
    sidecar.write_text("{}\n", encoding="utf-8")
    try:
        resolved = resolve_export_file(service_ctx, _LONG_STEM_NAME)  # type: ignore[misc]
        assert isinstance(resolved, Path)
        assert resolved.is_absolute() and resolved.is_file()
        assert resolved == Path(service_ctx.exports_dir / _LONG_STEM_NAME).resolve()
    finally:
        os.remove(product)  # 用后清理（探针产物不残留）
        os.remove(sidecar)


async def test_resolve_export_file_backslash_drive_identity_gate_rejected_wiring(
    service_ctx,
) -> None:  # type: ignore[no-untyped-def]
    """EXPDR1 服务镜像：反斜杠/盘符名→InvalidExportRequestError（恒等闸——首闸）。

    match 两态注记：Windows 命中恒等闸消息；POSIX 反斜杠非分隔符（恒等
    放行）由 stem 字符集闸兜（\\ 与 : 不在 [A-Za-z0-9_-]）——双 OS 闭合。
    """
    for evil in ("..\\..\\..\\..\\evil.dxf", "C:\\evil.dxf"):
        with pytest.raises(_mod.InvalidExportRequestError, match=r"恒等闸|stem"):
            resolve_export_file(service_ctx, evil)  # type: ignore[misc]
