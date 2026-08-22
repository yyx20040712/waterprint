"""jobs worker 镜像测试：序列化边界、取消协作、大结果走文件。

输入:  waterprint_server.jobs.worker 公开符号
输出:  进程边界契约断言（§18 IPC 行 / §16 A6）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task", None)

pytestmark = [
    pytest.mark.skipif(
        run_task is None,
        reason="实现未就绪：waterprint_server.jobs.worker（服务层 M2）",
    ),
]


def test_worker_entry_imports_without_side_effects() -> None:
    """R5 接线断言（骨架期即可验）：模块导入零副作用（Windows spawn 安全）。

    实现合入后本断言自动生效：导入 waterprint_server.jobs.worker 不得
    创建进程池/连接队列/打印输出。
    """
    import os
    import subprocess
    import sys

    code = "import waterprint_server.jobs.worker as w; assert callable(w.run_task)"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", f"导入期产生副作用输出: {result.stdout!r}"


def test_large_result_returns_file_handle_wiring() -> None:
    """R3 接线断言：万级枚举结果经 arrow 文件返回路径句柄（不整包过 pickle）。"""
    raise AssertionError(
        "M2 接线断言：大结果任务的返回值含文件路径而非内联大数组——不得删除（A6）"
    )
