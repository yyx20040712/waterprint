"""任务注册表落盘序列化面：终态记录文档/原子写/恢复扫描（纯函数零状态）。

输入:  registry_dir + task_id + 平字段记录束
输出:  确定性 JSON 落盘文件 / 合法恢复记录流
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（S2 落盘化批 R1 拆分——check_file_budgets 门禁 500 行预算
# 「无豁免→拆文件」；行为经 manager 薄壳由 test_manager 恢复矩阵用例
# 覆盖，零行为变化）
#
# 【公开接口】
#   TERMINAL_STATES: 终态元组（done/cancelled/failed——manager._TERMINAL
#       同源单定义，消除双定义漂移面）
#   terminal_document(*, task_id, kind, payload, state, progress, stage,
#       condition_key, stale, error, error_type, result, snapshot_hash,
#       project_id) -> dict：S2 D4 落盘文档（TaskStatus 同构面+
#       snapshot_hash；subscribers/cancel_requested 进程内字段不在
#       入参面=天然排除）
#   write_record(registry_dir, task_id, document) -> Path：GR-38 原子写
#   iter_restorable(registry_dir) -> Iterator[(task_id, document)]：
#       合法终态记录流（损坏跳过+warning）
#
# 【行为规格】
#   R1 确定性序列化：ensure_ascii=False+sort_keys+indent=2+UTF-8+
#      尾换行（dump_openapi 同款纪律）；write_bytes 落盘（禁文本
#      模式默认换行——CRLF 教训）。
#   R2 原子写：同分区临时文件+os.replace（GR-38——worker.
#      _atomic_write_bytes 同款）；文件名=task_id 过 validate_component
#      白名单校验分量（uuid hex 服务端生成非客户端可控，仍带防御——
#      质量门 4）。
#   R3 恢复扫描：mtime 升序（近似完成时刻序——R2 R2/DS-04：单并发下
#      与注册序等价，多并发下比 uuid 字典序更贴「最近完成」业务语义
#      [exports 最近结果集取最末 done]；同名平局按文件名，读取态
#      OSError 排末尾）；逐条校验（分量白名单/JSON 对象形态/task_id
#      与文件名一致/state∈TERMINAL_STATES）；损坏越界逐条跳过+
#      structlog warning（fail-visible 不阻断启动——单条坏档不炸服务；
#      与锁守卫 fail-closed 场景不同：读面恢复）。键集不做完整性
#      声称——缺键由消费侧 KeyError→manager 薄壳 catch 同款跳过兜底
#      （R2 R4/DS-05：描述与实现对齐）。领域构造（TaskRequest kind
#      白名单等）归调用方，构造异常由调用方同款跳过（manager 薄壳）。
#
# 【测试要求】经 manager 薄壳由 server/tests/jobs/test_manager.py
#   恢复矩阵用例覆盖（终态重启可查/损坏跳过/非终态无痕 404/幂等表
#   不恢复）；本模块纯函数零 manager 内部类依赖。
#
# 【参照】重写计划 §16 A5/§18；S2 简报 D1~D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Final

import structlog

from waterprint_server.settings import validate_component

_LOGGER = structlog.get_logger(__name__)

# 终态面单定义（manager._TERMINAL 同源——S2 R1 拆分消除双定义漂移）。
TERMINAL_STATES: Final[tuple[str, ...]] = ("done", "cancelled", "failed")


def terminal_document(  # noqa: PLR0913  # S2 D4 落盘字段面冻结（13 键平字段——总控 R1 预裁口径）
    *,
    task_id: str,
    kind: str,
    payload: Mapping[str, Any],
    state: str,
    progress: float,
    stage: str,
    condition_key: str | None,
    stale: bool,
    error: str | None,
    error_type: str | None,
    result: Mapping[str, Any] | None,
    snapshot_hash: str | None,
    project_id: str,
) -> dict[str, Any]:
    """终态记录落盘文档（TaskStatus 同构面+snapshot_hash）。

    平字段入参=调用方（manager 薄壳）从 _TaskRecord 投影；subscribers/
    cancel_requested 进程内字段不在入参面（D4 排除语义由签名承载）。
    """
    return {
        "task_id": task_id,
        "kind": kind,
        "payload": dict(payload),
        "state": state,
        "progress": progress,
        "stage": stage,
        "condition_key": condition_key,
        "stale": stale,
        "error": error,
        "error_type": error_type,
        "result": dict(result) if result is not None else None,
        "snapshot_hash": snapshot_hash,
        "project_id": project_id,
    }


def write_record(registry_dir: Path, task_id: str, document: Mapping[str, Any]) -> Path:
    """GR-38 原子写：确定性 JSON+write_bytes UTF-8+临时文件 os.replace。"""
    blob = (
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    registry_dir.mkdir(parents=True, exist_ok=True)
    target = registry_dir / f"{validate_component(task_id)}.json"
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(blob)
    os.replace(tmp, target)
    return target


def iter_restorable(registry_dir: Path) -> Iterator[tuple[str, Mapping[str, Any]]]:
    """合法终态记录流（S2 D2 恢复扫描——mtime 升序近似完成时刻序，R2 R2/DS-04）。

    损坏 JSON/非对象形态/task_id 不一致/非终态/分量越界/读取态 IO 异常
    逐条跳过+structlog warning（fail-visible 不阻断启动）。
    """

    def _mtime(entry: Path) -> tuple[float, str]:
        try:
            return (entry.stat().st_mtime, entry.name)
        except OSError:
            return (float("inf"), entry.name)  # stat 失败排末尾（读取面随后跳过）

    registry_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(registry_dir.glob("*.json"), key=_mtime):
        task_id = entry.stem
        try:
            validate_component(task_id)
            raw = json.loads(entry.read_bytes().decode("utf-8"))
            if not isinstance(raw, Mapping):
                raise ValueError("记录须为 JSON 对象")
            document: Mapping[str, Any] = raw
            if str(document["task_id"]) != task_id:
                raise ValueError("task_id 与文件名不一致")
            state = str(document["state"])
            if state not in TERMINAL_STATES:
                raise ValueError(f"非终态记录不恢复（D1 仅终态落盘）：{state}")
        except (ValueError, KeyError, TypeError, UnicodeDecodeError, OSError) as exc:
            _LOGGER.warning(
                "任务注册表记录跳过（恢复面 fail-visible 不阻断启动）",
                path=str(entry),
                reason=f"{type(exc).__name__}: {exc}",
            )
            continue
        yield task_id, document
