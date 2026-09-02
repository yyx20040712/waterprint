"""exports DWG 可选转换镜像测试（WP0 挂账补测）+list_exports 边车键面归一
（WP4 修2）。

输入:  waterprint_server.services.exports 公开符号
输出:  DWG 成功/失败两路与边车扫描契约断言
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（WP4 服务端小修攒批 2026-09-02）
#
# 【替身口径】（WP0 实测形态·跨平台镜像）——Windows=.cmd 批处理替身：
#   成功形态 copy %~1\%~7 → %~2\%~n7.dwg 产 .dwg/exit 0；失败形态
#   exit 2（WP0 实测失败形态）。POSIX=.sh cp 等价（CI ubuntu 面）——
#   两形态同走真实 _dwg_convert 子进程路径；真 ODA E2E=用户侧验收项
#   （WP0 挂账口径，禁测试依赖真件）。
# 【覆盖面】
#   - 成功路：DXF+DWG 同名并排双产物+边车双行登记；
#   - 失败路（exit 2）：DXF 照常交付+dwg 不存在+仅 1 边车行
#     （DXF 交付承诺不可破）；
#   - 修2（红先锚点）：合法 JSON 缺/多键边车→list_exports 跳过不炸
#     （TypeError 归一——与 JSONDecodeError 同惯例；完好边车照常列出）。
# 【参照】WP0/WP4 简报；外审整改#6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import dataclasses
import importlib
import json
import sys
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.services.exports")
create_export = getattr(_mod, "create_export")
list_exports = getattr(_mod, "list_exports")

calculation_mod = importlib.import_module("waterprint_server.services.calculation")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        None in (create_export, list_exports),
        reason="实现未就绪：waterprint_server.services.exports（服务层 M2/M3）",
    ),
    pytest.mark.anyio,
]


def _standin_converter(directory: Path, *, fail: bool) -> Path:
    """替身转换器（WP0 实测口径·跨平台镜像）：真实子进程路径，零真 ODA 依赖。

    ODA CLI argv=<in_dir> <out_dir> <version> <DWG|DXF> <recurse> <audit>
    <filter>——成功替身把输入 dxf 复制为输出同名 .dwg（exit 0）；失败
    替身恒 exit 2。Windows=.cmd（WP0 实测形态），POSIX=.sh（CI ubuntu）。
    """
    directory.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        standin = directory / "oda-standin.cmd"
        if fail:
            standin.write_bytes(b"@echo off\r\nexit /b 2\r\n")
        else:
            standin.write_bytes(
                b"@echo off\r\n"
                b'copy /Y "%~1\\%~7" "%~2\\%~n7.dwg" >nul\r\n'
                b"exit /b 0\r\n"
            )
        return standin
    standin = directory / "oda-standin.sh"
    if fail:
        standin.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    else:
        standin.write_text(
            '#!/bin/sh\ncp "$1/$7" "$2/$(basename "$7" .dxf).dwg"\nexit 0\n',
            encoding="utf-8",
        )
    standin.chmod(0o755)
    return standin


def _dwg_ctx(service_ctx, converter: Path):  # type: ignore[no-untyped-def]
    """开关装配：settings.model_copy 注入替身路径（frozen 面正门）。"""
    return dataclasses.replace(
        service_ctx,
        settings=service_ctx.settings.model_copy(
            update={"dwg_converter_path": str(converter)}
        ),
    )


async def _project_with_result(ctx, cass_payload) -> str:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（最近结果集就绪——dxf 导出消费前提）。"""
    outcome = projects_mod.create_project(ctx, {"project": cass_payload})
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(ctx, project_id, [])
    for _ in range(200):
        if ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert ctx.manager.status(handle.task_id).state == "done"
    return project_id


async def test_dwg_success_dual_products_and_dual_sidecars_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """WP0 挂账补测：替身转换成功→DXF+DWG 双产物+边车双行登记。"""
    project_id = await _project_with_result(service_ctx, cass_payload)
    converter = _standin_converter(tmp_path / "dwg", fail=False)
    ctx = _dwg_ctx(service_ctx, converter)
    handle = await create_export(
        ctx, project_id, "dxf", "design", {"unit_id": "municipal_cass"}
    )
    dxf = Path(handle.path)
    assert dxf.is_file() and dxf.stat().st_size > 0  # DXF 恒为契约产物
    dwg = dxf.with_suffix(".dwg")
    assert dwg.is_file() and dwg.stat().st_size > 0  # 同名并排 DWG
    metas = list_exports(ctx, project_id)
    assert sorted(m.file_name for m in metas) == sorted((dxf.name, dwg.name))  # 边车双行
    assert all(m.kind == "dxf" for m in metas)


async def test_dwg_failure_dxf_still_delivered_single_sidecar_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """WP0 挂账补测：替身 exit 2→warning 跳过 DWG，DXF 照常+仅 1 边车行。"""
    project_id = await _project_with_result(service_ctx, cass_payload)
    converter = _standin_converter(tmp_path / "dwg", fail=True)
    ctx = _dwg_ctx(service_ctx, converter)
    handle = await create_export(
        ctx, project_id, "dxf", "design", {"unit_id": "municipal_cass"}
    )
    dxf = Path(handle.path)
    assert dxf.is_file() and dxf.stat().st_size > 0  # DXF 交付承诺不可破
    assert not dxf.with_suffix(".dwg").exists()  # 无 DWG 残留
    metas = list_exports(ctx, project_id)
    assert [m.file_name for m in metas] == [dxf.name]  # 仅 1 边车行


async def test_list_exports_skips_sidecar_with_mismatched_keys_wiring(
    service_ctx,  # type: ignore[no-untyped-def]
) -> None:
    """修2（红先锚点）：合法 JSON 缺/多键边车→跳过不 500（TypeError 归一）。

    修复前：ExportMeta(**raw) 键面不符→TypeError 裸抛（列表面整体炸）；
    修复后与 JSONDecodeError 同惯例逐条跳过，完好边车照常列出。
    """
    good = {
        "project_id": "p1",
        "kind": "dxf",
        "condition_key": "design",
        "file_name": "prod-good.dxf",
        "design_digest": "d0123456789abcdef",
        "engine_version": "e",
        "data_version": "v",
        "stale_labeled": False,
    }
    (service_ctx.exports_dir / "prod-good.dxf.meta.json").write_text(
        json.dumps(good), encoding="utf-8"
    )
    (service_ctx.exports_dir / "prod-bad.meta.json").write_text(
        json.dumps({"project_id": "p1", "kind": "dxf"}), encoding="utf-8"
    )  # 合法 JSON 对象但缺 ExportMeta 必需键
    metas = list_exports(service_ctx, "p1")
    assert [m.file_name for m in metas] == ["prod-good.dxf"]  # 坏边车跳过、好边车照常
