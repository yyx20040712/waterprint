"""jobs worker 镜像测试：序列化边界、取消协作、大结果走文件。

输入:  waterprint_server.jobs.worker 公开符号
输出:  进程边界契约断言（§18 IPC 行 / §16 A6）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task")

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


def _cass_project_file(tmp_path: Path) -> Path:
    """CASS 项目落盘（worker 正门载荷——app.save_project 确定性序列化）。"""
    from waterprint import app as core
    from waterprint.contracts.project_schema import (
        DesignState,
        Metadata,
        ProjectFile,
        ViewState,
    )

    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
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
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                }
            ],
        ),
        view=ViewState(timestamp="2026-08-26T00:00:00Z"),
        metadata=Metadata(
            format_version="1.0",
            content_hash="0" * 64,
            engine_version="0",
            data_version="0",
        ),
    )
    path = tmp_path / "enum.wp.json"
    core.save_project(project, path)
    return path


def test_large_result_returns_file_handle_wiring(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R3 接线断言：万级枚举结果经 arrow 文件返回路径句柄（不整包过 pickle）。"""
    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "enumerate",
        "task_id": "rows-handle-probe",
        "project_id": "p",
        "project_path": str(_cass_project_file(tmp_path)),
        "unit_id": "municipal_cass",
        "conditions": [],
        "options": {},
        "data_dir": str(test_settings.data_dir),
        "artifacts_dir": str(artifacts),
    }
    outcome = run_task(payload, None, None)
    assert outcome["state"] == "done"
    assert "rows_file" in outcome and "feasible_count" in outcome  # 路径句柄面
    assert "rows" not in outcome  # 不整包内联（§16 A6：万级行禁过 pickle 大数组）
    rows_file = Path(str(outcome["rows_file"]))
    assert rows_file.is_file() and rows_file.suffix == ".feather"  # arrow 文件落盘
    frame = pd.read_feather(rows_file)  # 按需重载（分页消费面）
    assert len(frame) == outcome["feasible_count"]
    assert len(frame) >= 1  # CASS manifest 网格非空（数据面前提）


def test_unknown_kind_rejected_at_serialization_boundary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R1 镜像缺失收口：未知 kind 在 pickle 边界即拒（禁静默空结果）。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    with pytest.raises(InvalidTaskPayloadError, match="未知任务 kind"):
        run_task({"kind": "nonsense", "task_id": "x"}, None, None)
