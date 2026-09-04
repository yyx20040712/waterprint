"""export_batch worker DWG 双产物镜像测试（R2-C 交付2）：可选转换+边车登记。

输入:  waterprint_server.jobs.worker（run_task/dwg 挂钩）与 services.exports
       （create_export 批量 payload 契约面）
输出:  DWG 四形态行为断言（替身转换器跨平台）+payload 契约断言
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（R2-C 服务端安全小批 2026-09-02·交付2）
#
# 【替身口径】（WP0 实测形态·test_exports_dwg.py 三用例先例——.cmd/.sh
#   跨平台）：成功替身 copy 输入 dxf 为输出同名 .dwg（exit 0）；失败替身
#   恒 exit 2；超时替身 sleep≈2s（timeout=1s 必超）。四形态全走真实
#   dwg_convert 子进程路径，零真 ODA 依赖（真件 E2E=用户侧验收，WP0 口径）。
# 【覆盖面】
#   - 形态①成功：DXF+DWG 双产物+双边车（worker 路径=同步路径
#     :466/:467-469 双产物登记同构）；files 结果面零漂移（DWG 不入——
#     边车是登记面非任务产物清单）；
#   - 形态②失败（exit 2）：DXF 照常交付+仅 DXF 边车（DXF 交付承诺不可破）；
#   - 形态③开关关（converter 空串）：零子进程+仅 DXF 边车（登记块在=
#     登记——与 test_worker.py 存量直构 payload〔无登记块零边车〕分界）；
#   - 形态④超时（sleep 2s/timeout 1s）：DXF 照常+仅 DXF 边车（超时=
#     warning 跳过族）；
#   - 契约面：create_export 批量 payload 携带 dwg_converter_path/timeout_s
#     +dxf 项 sidecars 预构建边车文本（ExportMeta 单源——worker 仅落盘）。
# 【登记块口径】item 携带 sidecars=payload 预构建边车文本（services
#   ExportMeta 八键单源）；缺块=存量零边车行为（test_worker.py 锁用例
#   iterdir 断言约束——设计实录）。
# 【R-1 增补（2026-09-02 A 二审六必改）】
#   - D-01：dwg_convert 产物落位 os.replace 失败→归入失败族（None）——
#     修复前 dwg 路径先赋值=假成功（returned 非 None+exists=False+零告警
#     ——A 复现件红相形态；K-05 拆件后真源=jobs.dwg.dwg_convert）；
#   - D-02：kind=dxf 的 out_name 后缀闸（必须 .dxf）——防 out_name=
#     "foo.dwg" 时转换产物 with_suffix 同路径覆盖已交付 DXF（A 复现件
#     形态 C：DXF 内容被 b'REALDWG' 覆盖）；
#   - K-03：sidecars 二道闸（非映射=InvalidTaskPayloadError，不再裸
#     ValueError 炸）+转换前置=开关非空且 sidecars 含 "dwg" 键（转换
#     决定与登记面绑定——无登记键不转换，防幽灵产物）；
#   - K-04：timeout 缺键/非正整数/非整数→跳过+warning（不 0 秒静默
#     超时、不 ValueError 炸批）；
#   - K-02：转换前取消检查（DXF 落盘后置令牌→转换跳过+取消后零新
#     边车；转换后落盘由既有取消清理逻辑管，不补）。
# 【参照】R2-C 简报交付2；WP0 挂账「worker 无边车面与边车面同批设计」
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task")
projects_mod = importlib.import_module("waterprint_server.services.projects")
calculation_mod = importlib.import_module("waterprint_server.services.calculation")
exports_mod = importlib.import_module("waterprint_server.services.exports")
create_export = getattr(exports_mod, "create_export")

pytestmark = [
    pytest.mark.skipif(
        None in (run_task, create_export),
        reason="实现未就绪：waterprint_server 导出面（服务层）",
    ),
    pytest.mark.anyio,
]

_META_BASE: dict[str, object] = {
    "project_id": "p-dwg",
    "kind": "dxf",
    "condition_key": "design",
    "design_digest": "d0123456789abcdef",
    "engine_version": "e-test",
    "data_version": "v-test",
    "stale_labeled": False,
}


@pytest.fixture(autouse=True)
def _progress_queue_guard():
    """进度队列全局还原（service_ctx Manager 注入面——test_manager.py 先例）。

    Manager.start() 注入 worker 模块全局、shutdown() 关队列不清全局——
    不还原则关闭队列泄给后续直调 run_task 的测试（跨文件顺序耦合）。
    """
    prior = _mod._PROGRESS_QUEUE  # noqa: SLF001  # 快照（注入口全局）
    yield
    _mod._PROGRESS_QUEUE = prior  # noqa: SLF001  # 还原（基线动态零漂移）


def _standin_converter(directory: Path, mode: str) -> Path:
    """替身转换器（跨平台）：ok=copy 成功/fail=exit 2/slow=sleep 2s。

    ODA CLI argv=<in_dir> <out_dir> <version> <DWG|DXF> <recurse> <audit>
    <filter>——成功替身把输入 dxf 复制为输出同名 .dwg（WP0 实测形态）。
    """
    directory.mkdir(parents=True, exist_ok=True)
    slow_cmd_win = b"@echo off\r\n@ping -n 3 127.0.0.1 >nul\r\nexit /b 0\r\n"
    slow_cmd_posix = "#!/bin/sh\nsleep 2\nexit 0\n"
    if sys.platform == "win32":
        forms = {
            "ok": b'@echo off\r\ncopy /Y "%~1\\%~7" "%~2\\%~n7.dwg" >nul\r\nexit /b 0\r\n',
            "fail": b"@echo off\r\nexit /b 2\r\n",
            "slow": slow_cmd_win,
        }
        standin = directory / "oda-standin.cmd"
        standin.write_bytes(forms[mode])
        return standin
    forms = {
        "ok": '#!/bin/sh\ncp "$1/$7" "$2/$(basename "$7" .dxf).dwg"\nexit 0\n',
        "fail": "#!/bin/sh\nexit 2\n",
        "slow": slow_cmd_posix,
    }
    standin = directory / "oda-standin.sh"
    standin.write_text(forms[mode], encoding="utf-8")
    standin.chmod(0o755)
    return standin


def _fake_export_write(kind, plant, template, out, *, unit_id=None, condition_key=None):  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口（core.export_artifact 公开面——test_worker.py 先例）
    """core.export_artifact 替身：落占位字节（GR-38 rename 由真码执行）。"""
    Path(out).write_bytes(b"dxf-standin")


async def _result_file_via_calc(service_ctx, cass_payload) -> str:  # type: ignore[no-untyped-def]
    """真 calc 结果文件（worker deserialize 正门实载荷——test_worker.py 同款）。"""
    outcome = projects_mod.create_project(service_ctx, {"project": cass_payload})
    artifacts = service_ctx.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    calc = run_task(
        {
            "kind": "calc",
            "task_id": "dwg-forms-calc",
            "project_id": "p-dwg",
            "project_path": str(
                service_ctx.projects_dir / f"{outcome.project_id}.wp.json"
            ),
            "conditions": [],
            "data_dir": str(service_ctx.settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert calc["state"] == "done"
    return str(calc["result_file"])


def _form_payload(exports_dir: Path, result_file: str, converter: str, timeout_s: int) -> dict[str, object]:
    """四形态共用批量 payload：登记块（sidecars）+转换开关全携带。"""

    def _text(file_name: str) -> str:
        return (
            json.dumps(
                {**_META_BASE, "file_name": file_name},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    return {
        "kind": "export_batch",
        "task_id": "dwg-form",
        "project_id": "p-dwg",
        "exports_dir": str(exports_dir),
        "dwg_converter_path": converter,
        "dwg_converter_timeout_s": timeout_s,
        "items": [
            {
                "kind": "dxf",
                "result_file": result_file,
                "template": "unused",
                "out_name": "batch.dxf",
                "unit_id": "municipal_cass",
                "condition_key": "design",
                "sidecars": {"dxf": _text("batch.dxf"), "dwg": _text("batch.dwg")},
            }
        ],
    }


async def _drive_batch(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 前置束参数束（_fake_export 替身签名先例）
    service_ctx, cass_payload, tmp_path, converter: str, timeout_s: int,
    *, drop_dwg_sidecar: bool = False,
) -> tuple[Path, object]:
    """前置束：真 calc 结果+export_artifact 替身+批量任务直驱（worker 正门）。"""
    from waterprint import app as core

    result_file = await _result_file_via_calc(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    payload = _form_payload(out_dir, result_file, converter, timeout_s)
    if drop_dwg_sidecar:  # K-03 登记绑定形态：仅 dxf 边车键（缺 dwg 键）
        payload["items"][0]["sidecars"].pop("dwg")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _fake_export_write)
        result = run_task(payload, None, None)
    return out_dir, result


async def test_batch_dxf_dwg_success_dual_products_and_sidecars_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """形态①成功：DXF+DWG 双产物+双边车（同步路径双产物登记同构）。"""
    converter = _standin_converter(tmp_path / "dwg", "ok")
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path,
        str(converter), service_ctx.settings.dwg_converter_timeout_s,
    )
    assert result["state"] == "done"
    dxf = out_dir / "batch.dxf"
    dwg = out_dir / "batch.dwg"
    assert dxf.is_file() and dxf.stat().st_size > 0  # DXF 恒为契约产物
    assert dwg.is_file() and dwg.stat().st_size > 0  # 替身 copy=真实子进程路径成功
    assert [str(path) for path in result["files"]] == [str(dxf)]  # files 零漂移
    dxf_meta = json.loads((out_dir / "batch.dxf.meta.json").read_text(encoding="utf-8"))
    dwg_meta = json.loads((out_dir / "batch.dwg.meta.json").read_text(encoding="utf-8"))
    assert dxf_meta == {**_META_BASE, "file_name": "batch.dxf"}  # 八键全量（ExportMeta 镜像）
    assert dwg_meta == {**_META_BASE, "file_name": "batch.dwg"}  # 双产物各一行


async def test_batch_dxf_dwg_failure_dxf_delivered_single_sidecar_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """形态②失败（exit 2）：DXF 照常交付+仅 DXF 边车（无 DWG 残留）。"""
    converter = _standin_converter(tmp_path / "dwg", "fail")
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path,
        str(converter), service_ctx.settings.dwg_converter_timeout_s,
    )
    assert result["state"] == "done"  # 转换失败=warning 跳过（任务不失败）
    assert (out_dir / "batch.dxf").is_file()  # DXF 交付承诺不可破
    assert not (out_dir / "batch.dwg").exists()  # 无 DWG 残留
    sidecars = sorted(path.name for path in out_dir.glob("*.meta.json"))
    assert sidecars == ["batch.dxf.meta.json"]  # 仅 DXF 边车


async def test_batch_dxf_converter_off_registers_dxf_sidecar_only_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """形态③开关关：零子进程调用+仅 DXF 边车（登记块在=登记）。"""
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path,
        "", service_ctx.settings.dwg_converter_timeout_s,
    )
    assert result["state"] == "done"
    assert (out_dir / "batch.dxf").is_file()
    assert not (out_dir / "batch.dwg").exists()  # 开关空=零转换
    sidecars = sorted(path.name for path in out_dir.glob("*.meta.json"))
    assert sidecars == ["batch.dxf.meta.json"]  # 登记块在=DXF 恒登记


async def test_batch_dxf_dwg_timeout_dxf_delivered_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """形态④超时（替身 sleep≈2s/timeout=1s）：DXF 照常+仅 DXF 边车。

    超时族=SubprocessError 归一 warning 跳过（WP0「超时=跳过」铁律的
    worker 路径实录——与 exit 2 失败族分立的两形态）。
    """
    converter = _standin_converter(tmp_path / "dwg", "slow")
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path, str(converter), 1
    )
    assert result["state"] == "done"  # 超时=warning 跳过（任务不失败）
    assert (out_dir / "batch.dxf").is_file()  # DXF 交付承诺不可破
    assert not (out_dir / "batch.dwg").exists()  # 超时无 DWG 残留
    sidecars = sorted(path.name for path in out_dir.glob("*.meta.json"))
    assert sidecars == ["batch.dxf.meta.json"]  # 仅 DXF 边车


async def test_create_export_batch_payload_carries_dwg_face_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, monkeypatch
) -> None:
    """契约面：create_export 批量 payload 携带 DWG 开关+超时+dxf 项边车文本。"""
    outcome = projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(service_ctx, project_id, [])
    for _ in range(200):
        if service_ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert service_ctx.manager.status(handle.task_id).state == "done"
    captured: list[object] = []
    original_submit = service_ctx.manager.submit

    async def _spy_submit(request, *, idempotency_key=None):  # type: ignore[no-untyped-def]
        captured.append(request)
        return await original_submit(request, idempotency_key=idempotency_key)

    monkeypatch.setattr(service_ctx.manager, "submit", _spy_submit)
    # R0.5 总控裁定（2026-09-04）：批量 DWG 边车契约载体改有-unit 形态
    # （services/test_exports.py:162 同形态）——无-unit dxf 批量现被 M5 D5
    # 对偶拒绝 422 属预期新行为（tests/routers/test_exports.py 用例族锁）。
    await create_export(
        service_ctx,
        project_id,
        "dxf",
        "ok",
        {
            "unit_id": "municipal_cass",
            "items": [
                {"kind": "dxf", "condition_key": "design"},
                {"kind": "dxf", "condition_key": "avg"},
            ],
        },
    )
    payload = captured[0].payload  # type: ignore[attr-defined]
    assert payload["dwg_converter_path"] == ""  # settings 透传（默认关）
    assert payload["dwg_converter_timeout_s"] == service_ctx.settings.dwg_converter_timeout_s
    latest = service_ctx.manager.status(handle.task_id).result
    for item in payload["items"]:
        dxf_meta = json.loads(item["sidecars"]["dxf"])
        dwg_meta = json.loads(item["sidecars"]["dwg"])
        assert dxf_meta["project_id"] == project_id
        assert dxf_meta["kind"] == "dxf"
        assert dxf_meta["design_digest"] == latest["design_hash"]  # 三元组真源
        assert dxf_meta["engine_version"] == latest["engine_version"]
        assert dxf_meta["stale_labeled"] is False
        assert dxf_meta["file_name"].endswith(".dxf")
        dwg_name = dxf_meta["file_name"][: -len(".dxf")] + ".dwg"
        assert dwg_meta == dxf_meta | {"file_name": dwg_name}  # 同源仅名异


def test_dwg_convert_osreplace_failure_returns_none_wiring(tmp_path, monkeypatch) -> None:
    """D-01 单元面：产物落位 os.replace 失败→归入失败族（None——DXF 不可破）。

    修复前红相（A 复现件形态）：dwg 路径先赋值再 replace——异常被外层
    归一后 returned 非 None+产物 exists=False+零告警=假成功路径。
    """
    import os

    dxf = tmp_path / "u.dxf"
    dxf.write_bytes(b"dxf-bytes")
    converter = _standin_converter(tmp_path / "dwg", "ok")
    original_replace = os.replace

    def _fail_dwg_replace(src, dst, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(dst).endswith(".dwg"):  # 只炸 DWG 落位（DXF 面不受扰）
            raise OSError("injected replace failure (D-01)")
        return original_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", _fail_dwg_replace)
    from waterprint_server.jobs import dwg as dwg_mod  # K-05 拆件后真源
    result = dwg_mod.dwg_convert(str(converter), dxf, 10 * 10)
    assert result is None  # 修复前红：returned 非 None（假成功）
    assert not (tmp_path / "u.dwg").exists()  # 零幽灵产物


async def test_batch_dxf_out_name_suffix_gate_blocks_dwg_collision_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """D-02：kind=dxf 的 out_name 非 .dxf 后缀→二道闸拒（IPC 不可信面）。

    A 复现件形态 C：修复前 out_name="foo.dwg" 经 with_suffix(".dwg")
    =同路径——转换产物 os.replace 直接覆盖已交付 DXF（内容被替换）；
    修复后 InvalidTaskPayloadError 拒于任何落盘之前。
    """
    result_file = await _result_file_via_calc(service_ctx, cass_payload)
    converter = _standin_converter(tmp_path / "dwg", "ok")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    payload = _form_payload(out_dir, result_file, str(converter), 10 * 10)
    payload["items"][0]["out_name"] = "foo.dwg"  # dxf 项伪装 dwg 名=碰撞源
    with pytest.raises(_mod.InvalidTaskPayloadError, match="后缀"):
        run_task(payload, None, None)
    assert list(out_dir.iterdir()) == []  # 拒于任何落盘之前（含 DXF）


async def test_batch_sidecars_non_mapping_rejected_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """K-03：sidecars 非映射→InvalidTaskPayloadError（IPC 二道闸——不再裸炸）。"""
    result_file = await _result_file_via_calc(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    payload = _form_payload(out_dir, result_file, "", 10 * 10)
    payload["items"][0]["sidecars"] = "not-a-map"  # 直注非法形态
    with pytest.raises(_mod.InvalidTaskPayloadError, match="sidecars"):
        run_task(payload, None, None)


async def test_batch_missing_dwg_sidecar_key_skips_conversion_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """K-03：开关配置在但 sidecars 缺 "dwg" 键→零转换零 DWG（登记绑定）。

    修复前红相：converter 非空即转换→幽灵 DWG 落地（无登记面却产产物）。
    """
    converter = _standin_converter(tmp_path / "dwg", "ok")
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path, str(converter), 10 * 10,
        drop_dwg_sidecar=True,
    )
    assert result["state"] == "done"
    assert (out_dir / "batch.dxf").is_file()  # DXF 照常交付
    assert not (out_dir / "batch.dwg").exists()  # 无登记键=零转换（修复前红：幽灵 DWG）
    sidecars = sorted(path.name for path in out_dir.glob("*.meta.json"))
    assert sidecars == ["batch.dxf.meta.json"]  # 仅 DXF 边车


async def test_batch_invalid_timeout_skips_not_crashes_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """K-04：timeout 非整数字符串→跳过+warning（DXF 照常——不炸批不静默超时）。"""
    converter = _standin_converter(tmp_path / "dwg", "ok")
    out_dir, result = await _drive_batch(
        service_ctx, cass_payload, tmp_path, str(converter), "not-a-number",
    )
    assert result["state"] == "done"  # 修复前红：int() ValueError 炸批
    assert (out_dir / "batch.dxf").is_file()
    assert not (out_dir / "batch.dwg").exists()
    sidecars = sorted(path.name for path in out_dir.glob("*.meta.json"))
    assert sidecars == ["batch.dxf.meta.json"]


async def test_batch_cancel_before_conversion_skips_dwg_wiring(  # type: ignore[no-untyped-def]
    service_ctx, cass_payload, tmp_path
) -> None:
    """K-02：DXF 落盘后取消令牌置位→转换前检查命中（零 DWG+零新边车）。"""
    from waterprint import app as core

    result_file = await _result_file_via_calc(service_ctx, cass_payload)
    converter = _standin_converter(tmp_path / "dwg", "ok")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cancel_flag = tmp_path / "cancel.flag"

    def _export_then_cancel(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None
    ):
        Path(out).write_bytes(b"dxf-standin")
        cancel_flag.write_text("cancel", encoding="utf-8")  # DXF 落盘后置令牌

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _export_then_cancel)
        result = run_task(
            _form_payload(out_dir, result_file, str(converter), 10 * 10),
            str(cancel_flag),
            None,
        )
    assert result["state"] == "cancelled"
    assert list(result["files"]) == [str(out_dir / "batch.dxf")]  # 已落盘 DXF 携带
    assert (out_dir / "batch.dxf").is_file()
    assert not (out_dir / "batch.dwg").exists()  # 修复前红：转换照跑=幽灵 DWG
    assert list(out_dir.glob("*.meta.json")) == []  # 取消后零新边车（K-02 检查在登记前）
