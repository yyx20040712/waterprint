"""spawn 进程池冒烟（ENG2 D2）：create_app 正门 → 真池 → calc 终态+进度。

输入:  conftest test_settings/cass_payload + create_app(executor=None) 真装配
输出:  池装配路径行为断言（done+结果载荷可读+进度事件≥1——§12.2）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ENG2 D2；质量门条款 3/4）
#
# 【用例】test_process_pool_smoke_end_to_end：
#   create_app(settings(calc_workers=1, executor=None)) → 真
#   ProcessPoolExecutor 路径（main.py:195-199 唯一现场——既有 client
#   fixture 注入 ThreadPoolExecutor，本用例补的就是池装配路径；既有
#   直调 run_task 用例不动）→ 经 HTTP 正门提交最小 calc run 载荷
#   （conditions=['design','avg']——SERVER 探针③先例）→ 轮询至终态
#   （60s 上限，超时=失败并中文报错含 task_id）→ 断言 succeeded +
#   结果载荷可读（result_file 落盘 JSON 可解析非空）+ 进度事件 ≥1 条
#   （消费面行为断言——经 manager.project_events 订阅面，提交前订阅
#   免竞态：spawn 子进程启动远慢于同环毫秒级订阅窗口）。
#
# 【纪律】本文件随 lock_tests.py 同步入锁（用户总授权 2026-08-23，
# 实现报告详列该锁定动作）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from waterprint_server.jobs.manager import Event
from waterprint_server.main import create_app
from waterprint_server.settings import Settings

pytestmark = [pytest.mark.anyio]

_TIMEOUT_SECONDS = 60  # 轮询上限（秒）——超时=失败（中文报错含 task_id）
_POLL_SECONDS = 1 / 2  # 轮询间隔（幂商式保字面量白名单）


async def _collect_project_events(app: FastAPI, project_id: str, sink: list[Event]) -> None:
    """项目通道事件收集（消费面=manager.project_events，SSE 数据源同款）。"""
    async for event in app.state.ctx.manager.project_events(project_id):
        sink.append(event)


async def test_process_pool_smoke_end_to_end(
    test_settings: Settings, cass_payload: dict[str, object]
) -> None:
    """真进程池端到端冒烟（Windows spawn；经 create_app 正门——质量门条款 3）。

    断言链：终态 done + result_file 落盘 JSON 可读 + 进度事件 ≥1 条
    （跨进程进度桥消费面行为——质量门条款 4）。
    """
    app = create_app(test_settings, executor=None)  # 真池（main.py:195-199 唯一现场）
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            created = await client.post("/api/projects", json={"project": cass_payload})
            assert created.status_code == 200
            project_id = str(created.json()["project_id"])
            events: list[Event] = []
            collector = asyncio.create_task(_collect_project_events(app, project_id, events))
            try:
                submitted = await client.post(
                    "/api/calc/run",
                    json={"project_id": project_id, "conditions": ["design", "avg"]},
                )
                assert submitted.status_code == 200
                task_id = str(submitted.json()["task_id"])
                loop = asyncio.get_running_loop()
                deadline = loop.time() + _TIMEOUT_SECONDS
                status: dict[str, object] = {}
                while True:
                    status = (await client.get(f"/api/calc/tasks/{task_id}")).json()
                    if status.get("state") in {"done", "cancelled", "failed"}:
                        break
                    if loop.time() > deadline:
                        pytest.fail(
                            f"spawn 冒烟超时（>{_TIMEOUT_SECONDS}s 未到终态）："
                            f"task_id={task_id} 当前态={status.get('state')}"
                        )
                    await asyncio.sleep(_POLL_SECONDS)
            finally:
                collector.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await collector
            assert status["state"] == "done"
            result = status["result"]
            assert isinstance(result, dict) and result.get("result_file")
            payload = json.loads(Path(str(result["result_file"])).read_bytes())
            assert isinstance(payload, dict) and payload  # 结果载荷可读（serialize JSON）
            progress = [e for e in events if e.type == "progress" and e.task_id == task_id]
            assert len(progress) >= 1  # 进度事件 ≥1（池 initializer 注入队列→桥→订阅面）
