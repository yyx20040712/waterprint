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


def test_export_batch_second_gate_rejects_escape_writing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """AU-1/R1-1 二道闸：payload 直注的 kind 穿越/out_name 逃逸在 worker 即拒。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    project_path = str(_cass_project_file(tmp_path))  # SVRB D2：批首装载正门真源
    base = {
        "kind": "export_batch",
        "task_id": "gate",
        "project_path": project_path,
        "exports_dir": str(tmp_path / "gate-out"),
    }
    with pytest.raises(InvalidTaskPayloadError, match="二道闸"):  # kind 含路径段
        run_task(
            {**base, "items": [{"kind": "calcbook/../../evil", "out_name": "ok.xlsx"}]},
            None,
            None,
        )
    for evil_name in ("a/../../evil.xlsx", "..\\..\\evil.xlsx", "../../deep.xlsx", ""):
        with pytest.raises(InvalidTaskPayloadError, match="产物名非法"):
            run_task(
                {**base, "items": [{"kind": "calcbook", "out_name": evil_name}]},
                None,
                None,
            )
    assert not (tmp_path / "gate-out").exists()  # 二道闸拒于任何落盘之前


def test_export_batch_items_pass_unit_and_condition_to_core(
    test_settings, tmp_path, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """S2 D6 接线断言：批量 items 逐项透传 unit_id/condition_key 到 core。

    空串归一 None（单产物路径同款口径——exports.create_export
    condition_key or None 对偶面）；deserialize 正门真跑（真 calc 结果
    文件作 result_file——R1 序列化边界实载荷面）。
    """
    from waterprint import app as core

    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    project_path = str(_cass_project_file(tmp_path))
    calc = run_task(
        {
            "kind": "calc",
            "task_id": "passthrough-calc",
            "project_id": "p",
            "project_path": project_path,
            "conditions": [],
            "data_dir": str(test_settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert calc["state"] == "done"
    captured: list[tuple[str, object, object]] = []

    def _fake_export(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口（core.export_artifact 公开面）
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        captured.append((kind, unit_id, condition_key))
        Path(out).write_bytes(b"artifact")  # 替身落占位（GR-38 rename 面由真码执行）

    monkeypatch.setattr(core, "export_artifact", _fake_export)
    out_dir = tmp_path / "out"
    out_dir.mkdir()  # worker 面不建 exports_dir（服务装配期 ensure_directories 正门）
    result = run_task(
        {
            "kind": "export_batch",
            "task_id": "passthrough-batch",
            # SVRB D2：project_path 通道（worker load_project——kwargs 组装真源）
            "project_path": project_path,
            "exports_dir": str(out_dir),
            "items": [
                {
                    "kind": "dxf",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "a.dxf",
                    "unit_id": "municipal_cass",
                    "condition_key": "design",
                },
                {
                    "kind": "calcbook",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "b.xlsx",
                    "unit_id": "",
                    "condition_key": "",
                },
                {
                    "kind": "audit",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "c.xlsx",
                    "unit_id": None,  # R2 R3（DS-06）：显式 None 防 str(None)="None" 透传
                    "condition_key": None,
                },
            ],
        },
        None,
        None,
    )
    assert result["state"] == "done"
    assert captured == [
        ("dxf", "municipal_cass", "design"),  # items 级透传（S2 D6）
        ("calcbook", None, None),  # 空串归一 None（单产物同款口径）
        ("audit", None, None),  # 显式 None 归一 None（IPC 面不可信——DS-06）
    ]
    assert sorted(str(path.name) for path in (tmp_path / "out").iterdir()) == [
        "a.dxf",
        "b.xlsx",
        "c.xlsx",
    ]  # 原子替换落位（.tmp 已清）
