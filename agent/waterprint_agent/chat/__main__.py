"""Chat CLI 入口（单发/多轮/worker 桥/历史/清单五模式）。

输入:  argv（话术 / --interactive / --turn+--message-file / --history / --list-sessions）
输出:  stdout（单发=文本摘要；--turn=JSONL 事件流；--history=JSONL 消息）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/__main__.py
#   职责：python -m waterprint_agent.chat 入口——单发话术（NL 入口
#       重建①，B4-4a 三话术口径）/交互多轮（stdin）/worker 桥模式
#       （--turn：JSONL 事件流 stdout，server ai_chat 子进程消费）/
#       历史与清单（--history/--list-sessions，前端只读面）。
#   禁区：禁顶层 import context（懒加载铁律同 main.py——server 依赖
#       在函数体内触达）；退出码=0 成功/1 失败（桥层据此判终态）；
#       禁密钥打印（config 只进 llm 调用）。
#
# 【行为规格】
#   R1 单发：`python -m waterprint_agent.chat "<话术>"`——新会话一轮，
#      打印 assistant 文本；降级/失败如实打印（禁伪装成功）。
#   R2 桥模式：`--turn <sid> --message-file <path>`——读文件首行为
#      用户输入，事件逐行 JSON stdout（turn_start…turn_end），终态
#      exit 0；会话不存在=新建（sid 沿用）。
#   R3 只读：--history <sid>=消息 JSONL；--list-sessions=摘要 JSON。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import json
import sys


def _emit_jsonl(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False, default=str), flush=True)


def _run_bridge_turn(ctx, args: argparse.Namespace) -> int:
    """桥模式（R2）：读消息文件跑一轮——事件流 stdout，终态恒 0（截断已事件化）。"""
    if not args.message_file:
        print("桥模式须给 --message-file", file=sys.stderr)
        return 1
    with open(args.message_file, encoding="utf-8") as handle:
        message = handle.readline().strip()
    from waterprint_agent.chat import loop, sessions

    session = sessions.load_session(ctx, args.turn) or sessions.create_session(ctx)
    result = loop.run_turn(ctx, session, message, emit=_emit_jsonl)
    _emit_jsonl({"type": "turn_summary", "session_id": session.session_id, **result})
    return 0


def _run_interactive(ctx) -> int:
    """交互多轮（stdin——exit/quit/退出 收束）。"""
    from waterprint_agent.chat import loop, sessions

    session = sessions.create_session(ctx, title="交互会话")
    print(f"会话 {session.session_id} 就绪（输入 exit 退出）", flush=True)
    for line in sys.stdin:
        text = line.strip()
        if text in {"exit", "quit", "退出"}:
            break
        if not text:
            continue
        result = loop.run_turn(ctx, session, text, emit=_emit_jsonl)
        print(result["assistant"], flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI 入口（R1-R3——返回进程退出码）。"""
    parser = argparse.ArgumentParser(prog="waterprint_agent.chat", description=__doc__)
    parser.add_argument("text", nargs="*", help="单发话术（省略=须给模式旗标）")
    parser.add_argument("--interactive", action="store_true", help="stdin 多轮交互")
    parser.add_argument("--turn", metavar="SESSION_ID", help="worker 桥模式：跑一轮")
    parser.add_argument("--message-file", metavar="PATH", help="桥模式用户输入文件")
    parser.add_argument("--history", metavar="SESSION_ID", help="打印会话消息 JSONL")
    parser.add_argument("--list-sessions", action="store_true", help="打印会话清单 JSON")
    args = parser.parse_args(argv)

    from waterprint_agent import context
    from waterprint_agent.chat import loop, sessions

    ctx = context.get_context()

    if args.list_sessions:
        print(json.dumps(sessions.list_sessions(ctx), ensure_ascii=False))
        return 0
    if args.history:
        for item in sessions.read_history(ctx, args.history):
            _emit_jsonl(item)
        return 0
    if args.turn:
        return _run_bridge_turn(ctx, args)
    if args.interactive:
        return _run_interactive(ctx)
    if args.text:
        text = " ".join(args.text)
        _session, result = loop.single_shot(ctx, text, emit=_emit_jsonl)
        print(result["assistant"])
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
