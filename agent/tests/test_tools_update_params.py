"""test_tools_update_params——#7 wp_update_params：批量改参三面守护+undo 快照+种子扩展。

输入:  tmp_path 沙箱（env 覆盖）+ golden 四种子（正式区只读装载）
输出:  清单式接受/拒绝断言+digest 变化+undo 落 sessions/（AI1-INTEG §3 #7）
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.tools import projects

_GOLDEN_SEEDS = (
    ("municipal_34760", "municipal_34760"),
    ("municipal_loop_34760", "municipal_34760_loop"),
    ("municipal_recycle_34760", "municipal_34760_recycle"),
    ("mine_43836", "mine_43836"),
)


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


@pytest.mark.parametrize(("seed", "case_dir"), _GOLDEN_SEEDS)
def test_create_project_all_golden_seeds(
    sandbox_env: Path, seed: str, case_dir: str
) -> None:
    """种子扩展（预裁决②）：四 golden 种子皆可建项，节点数与真源一致。"""
    result = asyncio.run(projects.wp_create_project(name=seed, seed=seed))  # type: ignore[arg-type]
    assert set(result) == {"project_id", "name", "design_digest"}
    source = json.loads(
        (
            context_repo_root() / "core" / "tests" / "golden" / "golden_data"
            / case_dir / "input_project.json"
        ).read_text(encoding="utf-8")
    )
    stored = json.loads(
        (sandbox_env / "projects" / f"{result['project_id']}.wp.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(stored["design"]["nodes"]) == len(source["design"]["nodes"])
    assert stored["design"]["checked_units"] == source["design"]["checked_units"]


def context_repo_root() -> Path:
    """仓库根（测试面直取——与 sandbox.repo_root 同位）。"""
    from waterprint_agent import sandbox

    return sandbox.repo_root()


def test_update_params_mixed_accept_and_reject(sandbox_env: Path) -> None:
    """#7 清单式：grid 档内接受+档外拒+未知键拒——不拒整批，结果三键形态。"""
    created = asyncio.run(projects.wp_create_project(name="改参", seed="municipal_34760"))
    result = asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[
                {"unit_id": "municipal_chenshachi", "key": "n", "value": 2.0},
                {"unit_id": "municipal_chenshachi", "key": "n", "value": 7.0},
                {"unit_id": "municipal_chenshachi", "key": "__nope__", "value": 1.0},
                {"unit_id": "inlet", "key": "q_avg_daily", "value": "0.5"},
            ],
        )
    )
    assert set(result) == {"results", "accepted_count", "design_digest"}
    assert result["accepted_count"] == 1
    flags = [(r["key"], r["accepted"]) for r in result["results"]]
    assert flags == [("n", True), ("n", False), ("__nope__", False),
                     ("q_avg_daily", False)]
    reasons = {r["key"]: r["reason"] for r in result["results"] if not r["accepted"]}
    assert "档位" in reasons["n"]
    assert "不在单元" in reasons["__nope__"]
    assert result["design_digest"] != created["design_digest"]  # 接受项生效
    stored = json.loads(
        (sandbox_env / "projects" / f"{created['project_id']}.wp.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored["design"]["nodes"]["municipal_chenshachi"]["n"] == 2.0


def test_update_params_undo_snapshot_in_sessions(sandbox_env: Path) -> None:
    """#7 undo 快照：接受项写入前旧项目字节落 sessions/ 旁挂 .undo.json。"""
    created = asyncio.run(projects.wp_create_project(name="快照", seed="municipal_34760"))
    old_bytes = (
        sandbox_env / "projects" / f"{created['project_id']}.wp.json"
    ).read_bytes()
    asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 3.0}],
        )
    )
    undos = list((sandbox_env / "sessions").glob(f"{created['project_id']}-*.undo.json"))
    assert len(undos) == 1
    assert undos[0].name.startswith(
        f"{created['project_id']}-{created['design_digest'][:10]}.undo.json"
    )
    assert undos[0].read_bytes() == old_bytes  # 改前态逐字节


def test_update_params_all_rejected_keeps_digest(sandbox_env: Path) -> None:
    """#7 全拒：项目零改动（无 undo 产物），digest 原样回显。"""
    created = asyncio.run(projects.wp_create_project(name="全拒", seed="municipal_34760"))
    result = asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[{"unit_id": "municipal_aao", "key": "n", "value": 7.0}],
        )
    )
    assert result["accepted_count"] == 0
    assert result["design_digest"] == created["design_digest"]
    assert not list((sandbox_env / "sessions").glob(f"{created['project_id']}-*.undo.json"))


def test_update_params_unknown_unit_rejected(sandbox_env: Path) -> None:
    """#7 未知单元：params_guard 前置结构错误入清单（不拒整批）。"""
    created = asyncio.run(projects.wp_create_project(name="未知单元", seed="municipal_34760"))
    result = asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[{"unit_id": "ghost_unit", "key": "n", "value": 2.0}],
        )
    )
    assert result["accepted_count"] == 0
    assert "不在项目" in result["results"][0]["reason"]


def test_update_params_error_faces(sandbox_env: Path) -> None:
    """#7 错误面：未知项目/路径注入→错误 dict（不 raise 裸异常）。"""
    missing = asyncio.run(
        projects.wp_update_params("deadbeef", patches=[])
    )
    assert "error" in missing and "hint" in missing
    injected = asyncio.run(
        projects.wp_update_params("../../etc", patches=[])
    )
    assert "error" in injected


def test_update_params_bad_patch_shape(sandbox_env: Path) -> None:
    """#7 patch 形态非法（unit_id/key 非字符串）→该条入拒绝清单。"""
    created = asyncio.run(projects.wp_create_project(name="形态", seed="municipal_34760"))
    result = asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[{"unit_id": 123, "key": "n", "value": 2.0}],  # type: ignore[dict-item]
        )
    )
    assert result["accepted_count"] == 0
    assert result["results"][0]["accepted"] is False
    assert re.search(r"非法", result["results"][0]["reason"])


def test_update_params_save_failure_cleans_undo(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """门一 FIX-3/C1：save_project 抛异常→undo 快照 best-effort 清理（无孤儿）。"""
    from waterprint_server.services import projects as projects_service

    created = asyncio.run(projects.wp_create_project(name="孤儿", seed="municipal_34760"))
    old_bytes = (
        sandbox_env / "projects" / f"{created['project_id']}.wp.json"
    ).read_bytes()

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("模拟保存失败（锁冲突/深度闸）")

    monkeypatch.setattr(projects_service, "save_project", _boom)
    result = asyncio.run(
        projects.wp_update_params(
            created["project_id"],
            patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 3.0}],
        )
    )
    assert "error" in result and "hint" in result  # run_tool 兜底错误 dict
    assert "RuntimeError" in result["error"]
    assert not list(  # 无孤儿 undo（半写清理）
        (sandbox_env / "sessions").glob(f"{created['project_id']}-*.undo.json")
    )
    monkeypatch.undo()
    stored = (
        sandbox_env / "projects" / f"{created['project_id']}.wp.json"
    ).read_bytes()
    assert stored == old_bytes  # 项目本体未被改写
