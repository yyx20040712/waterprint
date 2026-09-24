"""批量导出域纯 helper 组（worker 顶墙拆件——AGENTS §2 `<名>_lib.py` 先例）。

输入:  导出项字段（out_name/sheet/h/v/unit_id）+边车文本
输出:  产物名二道闸/边车原子写/路由选项/阶段标签（纯函数零 IO 状态）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 2 2026-09-24——jobs/worker.py 500/500 顶墙拆件）
#   路径：server/waterprint_server/jobs/export_batch_lib.py
#   职责：export_batch 域四个纯 helper 原文迁驻（_safe_out_name 二道闸/
#       _write_sidecar_text 边车原子写/_item_route_options 选项归一/
#       _stage_label 阶段标签）——worker 撞 500 行预算墙（本批 ai_chat
#       kind 挂载触发），按 §2 门禁脚本拆解析层同款拆件配方。
#   禁区：禁 import worker/manager（纯函数件——防环）；禁行为变更
#       （原文迁移，语义/报错文案逐字保真）；禁入业务逻辑。
#
# 【行为规格】四件签名与语义=worker 原文冻结面（镜像测试
#   server/tests/jobs/test_worker_batch.py 断言不变——迁驻零语义漂移）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import structlog

__all__ = [
    "_item_route_options",
    "_safe_out_name",
    "_stage_label",
    "_write_sidecar_text",
]

_LOGGER = structlog.get_logger(__name__)  # 边车登记失败告警面（迁移自 worker）


def _safe_out_name(name: str, kind: str) -> str:
    from waterprint_server.jobs.worker import (  # noqa: PLC0415  # 懒 import 破环（worker 装载期先 import 本件）
        InvalidTaskPayloadError,
    )

    """R1-1 二道闸：产物文件名防逃逸（无分隔符/无 .. /非空——payload 直注
    IPC 面防线；服务面已过白名单，本闸防绕过服务层直构 payload，§18）。
    D-02（R-1）：kind=dxf 强制 .dxf 后缀——防 out_name="foo.dwg" 时转换
    产物 with_suffix 同路径覆盖已交付 DXF；SVRB D3：ifc 同款单特判。"""
    if (
        not name
        or "/" in name
        or "\\" in name
        or ".." in name
        or name in {".", ".."}
        or (kind == "dxf" and not name.endswith(".dxf"))
        or (kind == "ifc" and not name.endswith(".ifc"))
    ):
        raise InvalidTaskPayloadError(
            f"导出产物名非法：{name!r}（R1-1 二道闸——无路径分隔符/无父段"
            "引用；dxf/ifc 项产物名须对应后缀〔D-02 防转换同路径覆盖〕；"
            "exports_dir 内落盘是唯一合法位置）"
        )
    return name


def _write_sidecar_text(exports_dir: Path, file_name: str, text: str) -> None:
    """R2-C：批量产物边车落盘（GR-38 原子写；文本=services 预构建）。"""
    sidecar = exports_dir / f"{file_name}.meta.json"
    tmp = sidecar.with_name(f"{sidecar.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, sidecar)
    except OSError as exc:  # WP0 R-1/G1-01 同族：登记失败不回滚已交付产物
        _LOGGER.warning("export_sidecar_skipped", source=file_name, reason=f"write failed: {exc!r}")


def _item_route_options(item: Mapping[str, Any]) -> dict[str, str]:
    """PROFILE3（PD1）：sheet/h/v 归一提取（空串剔除=仅非 None 键——
    未传不传，kwargs 精确集恒定沿既有断言面）。"""
    options: dict[str, str] = {}
    for key in ("sheet", "h_scale", "v_scale"):
        value = str(item.get(key) or "") or None
        if value is not None:
            options[key] = value
    return options


def _stage_label(kind: str, unit_id: str | None, sheet: str | None) -> str:
    """stage 点段序（SVRB D4+PROFILE3 PD1）：unit 项现形态零改；纵断项
    （无 unit）带 sheet 段（export:dxf:profile）；余项省略段（既有语义）。"""
    if unit_id:
        return f"export:{kind}:{unit_id}"
    return f"export:{kind}:{sheet}" if sheet else f"export:{kind}"
