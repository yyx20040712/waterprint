"""jobs worker 枚举多工况镜像测试：condition_keys 载荷 + 行数×(2+k)（ADR-018 D2/D5）。

输入:  waterprint_server.jobs.worker run_task（enumerate kind 载荷）+
       CASS 项目（inlet→cass，同 test_worker 母本口径）
输出:  多工况行族契约断言（载荷组装归 jobs/enum_payload.py——拆件后
       worker 唯一正门不变形；行数/键集/列族三面）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task")

pytestmark = pytest.mark.skipif(
    run_task is None,
    reason="实现未就绪：waterprint_server.jobs.worker（服务层 M2）",
)


def _cass_project_file(tmp_path: Path) -> Path:
    """CASS 项目落盘（worker 正门载荷——test_worker 母本同款）。"""
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
        view=ViewState(timestamp="2026-09-12T00:00:00Z"),
        metadata=Metadata(
            format_version="1.0",
            content_hash="0" * 64,
            engine_version="0",
            data_version="0",
        ),
    )
    path = tmp_path / "enum-cond.wp.json"
    core.save_project(project, path)
    return path


class _NullSink:
    """进度替身（序无关稳健）：显式 sink 防 worker 模块全局 _PROGRESS_QUEUE
    回退面——client 基测试先跑时 app 关闭队列后全局残留已关对象。"""

    def put(self, message: object) -> None:
        return None


def _run_enumerate(test_settings, tmp_path: Path, conditions: list[str], task_id: str) -> dict:  # type: ignore[no-untyped-def]
    """run_task 正门（conditions=受检集——payload.conditions 同 worker 消费面；
    task_id 逐跑唯一防 artifacts 同名互覆；progress=替身不走模块全局）。"""
    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "enumerate",
        "task_id": task_id,
        "project_id": "p",
        "project_path": str(_cass_project_file(tmp_path)),
        "unit_id": "municipal_cass",
        "conditions": conditions,
        "options": {},
        "data_dir": str(test_settings.data_dir),
        "artifacts_dir": str(artifacts),
    }
    outcome = run_task(payload, None, _NullSink())
    assert outcome["state"] == "done"
    return dict(outcome)


def test_enumerate_condition_keys_payload(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ADR-018 D5：result.condition_keys=工况键清单（2+k——build_condition_set
    输出序；FE 方案表工况列筛选真源）。"""
    outcome = _run_enumerate(test_settings, tmp_path, ["municipal_cass"], "cond-checked")
    assert outcome["condition_keys"] == [
        "design",
        "avg",
        "design_offline_municipal_cass",
    ]  # 2+k 恰三键（iter_all 序）
    baseline = _run_enumerate(test_settings, tmp_path, [], "cond-baseline")
    assert baseline["condition_keys"] == ["design", "avg"]  # 空受检=仅基线两档


def test_enumerate_rows_scale_and_column_families(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ADR-018 D2：行数=grid.total×(2+k)；condition_key 列在 rows_file；
    grid_fields/dim_fields 载荷面零回归（拆件 enum_payload 后同形）。"""
    baseline = _run_enumerate(test_settings, tmp_path, [], "scale-baseline")
    checked = _run_enumerate(test_settings, tmp_path, ["municipal_cass"], "scale-checked")
    frame = pd.read_feather(str(checked["rows_file"]))
    baseline_frame = pd.read_feather(str(baseline["rows_file"]))
    assert len(baseline_frame) == 15 * 2  # CASS 15 档 × 双工况（ADR-018 D2）
    assert len(frame) == len(baseline_frame) + 15  # +1 受检=+1 工况块（2+k 线性）
    assert len(frame) == checked["feasible_count"]
    assert set(frame["condition_key"].unique()) == {
        "design", "avg", "design_offline_municipal_cass",
    }
    assert "condition_key" in checked["columns"]  # 列集回显含工况列
    # 两列族载荷零回归（拆件搬运面——形状与真源投影不变形）
    assert [item["key"] for item in checked["grid_fields"]] == ["n_pool", "t_cycle"]
    assert all(set(item) == {"key", "dim", "label_zh"} for item in checked["dim_fields"])
    # CASS 已声明 out_dims（ADR-018 批顺带 31 条）：dim 族中文名透传真源
    by_key = {item["key"]: item for item in checked["dim_fields"]}
    assert by_key["v_plant"]["label_zh"] == "全厂池容"
