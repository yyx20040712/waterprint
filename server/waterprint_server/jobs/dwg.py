"""DXF→DWG 可选转换域件（jobs）：子进程转换原语+批量项转换闸面。

输入:  转换器路径/超时/产物路径（worker export_batch 挂钩与
       services.exports 单产物路径两消费面）
输出:  DWG 产物路径（成功）或 None（关/闸拒/失败——失败=warning+None）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（R2-C R-1 拆件 2026-09-02：K-05 根因解决——worker.py 500
# 行帽下批量面扩展受限，转换域独立成件〔ENG5 D4 records.py 先例〕）
#
# 【公开接口】
#   dwg_convert(converter: str, dxf_file: Path, timeout_s: int) -> Path | None
#       子进程转换原语（services.exports._post_export_dwg 消费——单产物
#       路径策略壳在 exports，本函数为两路径共享真源）
#   batch_dwg_artifact(payload, sidecars, dxf: Path) -> Path | None
#       export_batch dxf 项转换入口（闸面集中：开关+登记绑定+timeout 闸）
#
# 【行为规格】
#   R1 任何失败=warning+None（DXF 交付承诺不可破——WP0 铁律沿册）；
#      直 subprocess 而非 ezdxf.addons.odafc（WP0 三由：addon 只认全局
#      配置/PATH 显式路径不可注入；无 timeout；1.4.4 无产物分支未 raise）。
#   R2 D-01（R-1）：产物落位 os.replace 成功后才置成功旗标——replace
#      抛 OSError 归入外层失败族（修复前先赋值=假成功：returned 非
#      None+产物 exists=False+零告警）。
#   R3 K-03（R-1）：批量转换前置=开关非空且 sidecars 含 "dwg" 键
#      （转换决定与登记面绑定——无登记键不转换，防幽灵产物：转换成功
#      必登记，无登记面不产产物）。
#   R4 K-04（R-1）：timeout 缺键/非正整数/非整数→按开关空串同等跳过
#      +warning（不 0 秒静默超时〔语义隐蔽〕、不 int() ValueError 炸批）。
#
# 【测试要求】test_worker_dwg.py 四形态+R-1 六用例（D-01 单元面注入）。
#
# 【参照】R2-C 简报交付2；R-1 总控裁决六必改；WP0 评估件 §四
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

import structlog

# WP0（ODA-A）：ODA File Converter 输出版本参数=AC1032/R2018（§12.5 基线）。
_DWG_CLI_VERSION: Final[str] = "ACAD2018"
_LOGGER = structlog.get_logger(__name__)


def _hidden_gui_options() -> dict[str, Any]:
    """Windows 转换器弹窗抑制（SW_HIDE——ezdxf odafc 同款；POSIX/缺符号恒空，
    getattr 面=typeshed 缺席豁免且运行时等价）。"""
    if sys.platform != "win32":
        return {}
    startup = getattr(subprocess, "STARTUPINFO", None)
    if startup is None:  # 防御面：实现缺符号时退化为普通 spawn
        return {}
    info = startup()
    info.dwFlags = getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
    info.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {"startupinfo": info}


def dwg_convert(converter: str, dxf_file: Path, timeout_s: int) -> Path | None:
    """DXF→DWG 子进程转换（ODA CLI 契约 <in_dir> <out_dir> <version> <DWG|DXF>
    <recurse> <audit> [filter]）。任何失败（OSError/SubprocessError/退出码≠0/
    空产物）=warning+None——DXF 交付承诺不可破。"""
    dwg: Path | None = None  # 成功旗标（D-01：落位成功后才置——with 外返回）
    reason = ""
    try:
        in_dir = str(dxf_file.parent.resolve())  # resolve 失败归入失败面
        with tempfile.TemporaryDirectory(dir=in_dir) as tmp_name:  # exports 同分区（GR-38）
            argv = [converter, in_dir, tmp_name, _DWG_CLI_VERSION, "DWG", "0", "1", dxf_file.name]
            proc = subprocess.run(  # recurse=0 单文件；audit=1 同 ezdxf 默认；退出码下方统一判
                argv, capture_output=True, timeout=timeout_s, check=False,
                **_hidden_gui_options(),
            )
            produced = Path(tmp_name) / dxf_file.with_suffix(".dwg").name
            # R-1/G1-02：三重判（退出码+存在+非零字节——空产物不登记）
            if proc.returncode == 0 and produced.is_file() and produced.stat().st_size > 0:
                landed = dxf_file.with_suffix(".dwg")
                os.replace(produced, landed)  # D-01：失败抛 OSError→外层失败族
                dwg = landed  # 落位成功后才置旗标（修复前=假成功路径）
            else:
                stderr = (proc.stderr or b"").decode("utf-8", "replace").strip()
                reason = f"returncode={proc.returncode} stderr={stderr}"
    except (OSError, subprocess.SubprocessError) as exc:
        # 超时/缺件/管道/落位失败（D-01：replace 失败时旗标未置=失败族）/
        # cleanup——归一 reason；已落位旗标保持（A-01：cleanup 异常不吞成功）。
        reason = repr(exc)
    if dwg is None:  # 已落位（纵遇 cleanup 异常）不告警——不留幽灵 DWG
        _LOGGER.warning("dwg_convert_skipped", source=dxf_file.name, reason=reason)
    return dwg


def _timeout_of(payload: Mapping[str, Any]) -> int:
    """K-04 timeout 闸：非正整数/缺键/非整数=0（0=按开关空串同等跳过语义）。"""
    try:
        value = int(payload.get("dwg_converter_timeout_s"))  # type: ignore[arg-type]
    except (TypeError, ValueError):  # None 缺键/非整数字符串——IPC 面不可信
        return 0
    return value if value >= 1 else 0


def batch_dwg_artifact(
    payload: Mapping[str, Any], sidecars: Mapping[str, Any], dxf: Path
) -> Path | None:
    """export_batch dxf 项转换入口（闸面集中）：开关+登记绑定（K-03）
    +timeout 闸（K-04）——过闸才调 dwg_convert 原语。"""
    converter = str(payload.get("dwg_converter_path") or "")
    if not converter or "dwg" not in sidecars:
        return None  # 关=正常态不告警；无登记键=不转换（K-03 防幽灵产物）
    timeout_s = _timeout_of(payload)
    if timeout_s < 1:
        _LOGGER.warning(
            "dwg_convert_skipped", source=dxf.name,
            reason=f"invalid timeout {payload.get('dwg_converter_timeout_s')!r} (K-04)",
        )
        return None
    return dwg_convert(converter, dxf, timeout_s)
