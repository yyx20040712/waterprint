"""对话轮任务 runner（ai_chat kind——agent CLI 子进程桥，终裁 §一）。

输入:  payload {session_id, message, data_dir, artifacts_dir}
输出:  终态 Mapping（turn_summary 原文）；进度=stage 中文标签+步进百分比
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 2 2026-09-24）
#   路径：server/waterprint_server/jobs/ai_chat.py
#   职责：ai_chat 任务 kind 执行体——spawn agent CLI 桥模式
#       （uv run --directory agent python -m waterprint_agent.chat
#       --turn <sid> --message-file <f>，uv 绝对路径+仓库根推导命令面），
#       stdout JSONL 事件→进度上报；取消=行边界轮询+子进程终止。
#   禁区：禁 import waterprint_agent（server→agent 禁向——子进程是唯一
#       通道，审 B2 处置）；禁 LLM/对话逻辑入 server（智能在 agent 环，
#       ADR-019）；禁密钥/消息原文入日志（stage 只携标签）。
#
# 【行为规格】
#   R1 子进程：命令=[uv, run, --directory, <repo>/agent, python, -m,
#      waterprint_agent.chat, --turn, sid, --message-file, mf]；env=
#      os.environ 原样（AI 三键+超时经 env 单通道——main 启动 setdefault
#      归一化，门一 W1-k2：密钥禁经任务载荷）；消息文件落 artifacts_dir
#      （全文=用户输入，UTF-8——门一 W1-d1 全读对偶）。
#   R2 进度：JSONL 事件→_report（stage=中文标签，percent=步进幂商）；
#      turn_summary 行解析为终态结果（state=done 原文透传）。
#   R3 取消：每行边界查 _cancelled——置位即 terminate+wait，返回
#      {"state":"cancelled"}（不写半途结果——R4 同构）。
#   R4 失败：uv 缺失/载荷缺件→InvalidTaskPayloadError（422 面）；子进程
#      非零退出→RuntimeError（500 面——门一 W4 分类解耦）；stdout 非法行
#      跳过不计败（容错解析）。b28（AUDIT-#13 2026-11-18）：三处
#      process.wait 宽限超时→AiChatBridgeTimeoutError（DOMAIN_ERROR_CODES
#      名义族成员——failed 任务 error_code 非 None，不再裸穿 TimeoutExpired
#      的 error_code=None 形态）。b28 回炉（reviewer major）：收割账本
#      _ReapLedger 防重入——kill 本轮至多一次，已 kill 未退（poll 恒 None
#      顽固形态）时 finally 不再开第二次 wait+kill 全窗，在途领域错误
#      原样透传；终报文案如实（kill 后仍未退="未收割"，不谎报已收割）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import subprocess
import uuid
from collections.abc import Mapping
from pathlib import Path
from shutil import which
from typing import Any

__all__ = ["_run_ai_chat"]

_MAX_WAIT_S = 10  # terminate 后 join 宽限（秒——子进程收 SIGTERM 收尾窗）
_TAIL_CHARS = 2 * 10**2  # 失败面 stderr 摘要长度 200（诊断最小面——幂积保白名单）


class AiChatBridgeTimeoutError(RuntimeError):
    """对话子进程桥超时（终止宽限/终态收割超时——上游依赖失败 502 族）。

    b28（AUDIT-#13）：原 TimeoutExpired 裸穿=failed 任务 error_type
    游离 DOMAIN_ERROR_CODES 映射族（error_code=None）；收编后按类名入
    名义表（502 与只读面 AiChatReadError 同族同码）。
    """


class _ReapLedger:
    """本轮收割账本（b28 回炉：kill 防重发单源+finally 兜底防重入闸）。

    reviewer major：终态/取消收割超时且 kill 后仍不退（poll() 恒 None
    的顽固形态）时，finally 兜底对已 kill 未退进程重复完整收割——实测
    4 wait/3 kill 占四个宽限窗，且终报文案谎报"已 kill 收割"。账本语义：
    killed=True 即本轮 kill 已发、收割尝试已在册——finally 据此不再开
    第二次 wait+kill 全窗，在途领域错误原样透传（不被"兜底收割"替换）。
    """

    def __init__(self, process: Any) -> None:
        self._process = process
        self.killed = False

    def kill_once(self) -> None:
        """kill 单源（本轮至多一次——finally 兜底与 _wait_child 超时枝共用）。"""
        if not self.killed:
            self._process.kill()  # SIGKILL 强收防僵尸（kill 已发则不再补刀）
            self.killed = True

    def kill_and_grace(self) -> bool:
        """kill（防重发）+二段宽限收割：宽限内退出=True（已收割）；仍不退
        =False（顽固进程——收割失败如实上返，不伪造收割成功）。"""
        self.kill_once()
        try:
            self._process.wait(timeout=_MAX_WAIT_S)
        except subprocess.TimeoutExpired:
            return False
        return True


def _wait_child(process: Any, stage: str, reap: _ReapLedger) -> int:
    """process.wait 单源包装（三处 wait 同源——b28 AUDIT-#13）：
    TimeoutExpired→kill（账本防重发）+二段宽限收割后转
    AiChatBridgeTimeoutError（失败形态 error_type 入映射族，error_code
    不再 None 游离）。b28 回炉：二段宽限仍不退=已 kill 未退，终报文案
    如实（"已 kill 但未收割（进程未退出）"——不谎报已收割）。"""
    try:
        return int(process.wait(timeout=_MAX_WAIT_S))  # int 收口：process=Any 面 no-any-return 防线
    except subprocess.TimeoutExpired as exc:
        reaped = reap.kill_and_grace()
        detail = "已 kill 收割" if reaped else "已 kill 但未收割（进程未退出）"
        raise AiChatBridgeTimeoutError(
            f"对话子进程{stage}超时（{_MAX_WAIT_S}s 宽限后仍未退出——{detail}）"
        ) from exc

_STATIC_LABELS: Mapping[str, str] = {
    "turn_start": "对话开始",
    "assistant_text": "生成回复",
    "fallback": "降级模式",
    "turn_end": "回合完成",
}


def _stage_label(event: Mapping[str, Any]) -> str:
    """事件→中文阶段标签（R2——标签面零数据零密钥）。"""
    kind = str(event.get("type", ""))
    if kind in _STATIC_LABELS:
        return _STATIC_LABELS[kind]
    name = str(event.get("name", ""))
    if kind == "llm_step":
        return f"思考中（第 {event.get('step', '?')} 步）"
    if kind == "tool_start":
        return f"调用工具 {name}"
    if kind == "tool_result":
        verdict = "完成" if event.get("ok") else "失败"
        return f"工具{verdict} {name}"
    return "对话进行中"


def _child_env() -> dict[str, str]:
    """子进程 env（os.environ 原样——AI 三键+超时经 env 单通道，门一 W1-k2：
    密钥禁经任务载荷[registry 落盘面]，main 启动 setdefault 归一化 settings→env）。"""
    return dict(os.environ)


def _spawn_bridge(payload: Mapping[str, Any], uv: str, session_id: str) -> tuple[Any, Path]:
    """R1：消息文件落盘+子进程 spawn（返回 (Popen, 消息文件)——清理归调用方）。"""
    artifacts_dir = Path(str(payload.get("artifacts_dir", ".")))
    # P0-C（fix-plan 批3）：repo_root 只消费不自算——services 侧
    # submit_ai_chat_turn 单点推导（data_dir.resolve().parent）后显式入载荷。
    # 旧代码把 data_dir 当仓库根（uv --directory <data>/agent 必然 os
    # error 2）；缺键=载荷契约破坏，fail-fast 显式报错胜过静默错位。
    if "repo_root" not in payload:
        raise RuntimeError(
            "ai_chat 载荷缺 repo_root（P0-C 契约——services 侧必须显式单点推导注入）"
        )
    repo_root = Path(str(payload["repo_root"]))
    message_file = artifacts_dir / f"ai-chat-{uuid.uuid4().hex}.msg"
    message_file.parent.mkdir(parents=True, exist_ok=True)
    message_file.write_text(str(payload.get("message", "")) + "\n", encoding="utf-8")
    command = [
        uv,
        "run",
        "--directory",
        str(repo_root / "agent"),
        "python",
        "-m",
        "waterprint_agent.chat",
        "--turn",
        session_id,
        "--message-file",
        str(message_file),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_child_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return process, message_file


def _stream_events(
    process: Any, task_id: str, cancel_token: object, progress: Any, reap: _ReapLedger
) -> tuple[int | None, dict[str, Any]]:
    """R2/R3：stdout JSONL→进度上报与终态收割（返回 (退出码|None, summary)）。

    取消协作=行边界轮询（置位返回退出码 None——调用方翻译 cancelled）；
    两处 wait 均经 _wait_child+收割账本（b28 回炉防重入单源）。"""
    from waterprint_server.jobs.worker import (  # noqa: PLC0415  # 懒 import 破环（worker 装载期先 import 本件）
        _cancelled,
        _report,
        _StagePoint,
    )

    summary: dict[str, Any] = {}
    seen = 0
    assert process.stdout is not None
    for raw in process.stdout:
        if _cancelled(cancel_token):  # R3：行边界取消协作
            process.terminate()
            _wait_child(process, "终止宽限", reap)  # b28：超时→AiChatBridgeTimeoutError
            return None, summary
        text = raw.strip()
        if not text:
            continue
        try:
            event = json.loads(text)
        except ValueError:
            continue  # R4：非法行容错跳过
        if not isinstance(event, dict):
            continue
        seen += 1
        if event.get("type") == "turn_summary":
            summary = {key: value for key, value in event.items() if key != "type"}
            continue
        _report(task_id, _StagePoint(_stage_label(event), seen, seen + 10), progress)
    return _wait_child(process, "终态收割", reap), summary  # b28：超时→领域错误


def _run_ai_chat(
    payload: Mapping[str, Any],
    cancel_token: object,
    progress: Any,
) -> Mapping[str, Any]:
    """ai_chat 执行体（R1-R4——子进程桥+事件流进度+取消协作）。"""
    from waterprint_server.jobs.worker import (  # noqa: PLC0415  # 懒 import 破环（worker 装载期先 import 本件）
        InvalidTaskPayloadError,
    )

    session_id = str(payload.get("session_id", ""))
    if not session_id or not str(payload.get("message", "")):
        raise InvalidTaskPayloadError(
            "ai_chat 载荷缺 session_id/message（IPC 面防线——服务面已校验，"
            "本闸防绕过服务层直构 payload）"
        )
    from waterprint_server.settings import (  # noqa: PLC0415  # 懒 import（与 worker 破环族同制）
        validate_component,
    )

    try:
        validate_component(session_id)  # 门一 B1 防御纵深：IPC 面成分二道闸
    except ValueError as exc:
        raise InvalidTaskPayloadError(f"session_id 成分非法：{exc}") from exc
    uv = which("uv")
    if uv is None:
        raise InvalidTaskPayloadError("未找到 uv 可执行（agent CLI 子进程桥不可用）")
    process, message_file = _spawn_bridge(payload, uv, session_id)
    reap = _ReapLedger(process)  # 收割账本：kill 防重发+finally 防重入（b28 回炉）
    try:
        return_code, summary = _stream_events(
            process,
            str(payload["task_id"]),
            cancel_token,
            progress,  # manager 注入
            reap,
        )
    finally:
        message_file.unlink(missing_ok=True)  # 消息文件即用即清（不留敏感面）
        # b28（AUDIT-#13）：收割从未发生（异常早于收割位）→单次 kill+宽限
        # 收割，超时经 _wait_child 转"兜底收割"领域错误替换在途原异常上抛
        # （raise from TimeoutExpired 保留因果链）。b28 回炉（防重入闸）：
        # kill 已发仍未退（终态/取消收割超时路径——账本在册）→不再开第二
        # 次 wait+kill 全窗（顽固进程 4 wait/3 kill 缺陷闭口），在途领域
        # 错误原样透传。
        if process.poll() is None and not reap.killed:
            reap.kill_once()
            _wait_child(process, "兜底收割", reap)
    if return_code is None:
        return {"state": "cancelled"}
    # b28 起 _stream_events 返回 int|None——None 守卫后窄化 int，旧 type: ignore 退役
    if return_code != 0:
        tail = process.stderr.read()[-_TAIL_CHARS:] if process.stderr else "（空）"
        raise RuntimeError(  # 门一 W4：运行期失败≠载荷非法（500 面——分类解耦）
            f"对话子进程退出码 {return_code}（agent CLI 桥失败——stderr 摘要 {tail}）"
        )
    return {"state": "done", "session_id": session_id, **summary}
