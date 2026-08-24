"""io 镜像测试：项目文件确定性序列化（双跑字节相同/往返无损/防弹加载）。

输入:  waterprint.project.io 公开符号 + 最小项目数据
输出:  序列化契约断言（ADR-004 核心）
"""

from __future__ import annotations

import importlib
import json

import pytest

_mod = importlib.import_module("waterprint.project.io")
save_project = getattr(_mod, "save_project", None)
load_project = getattr(_mod, "load_project", None)
dumps = getattr(_mod, "dumps", None)
loads = getattr(_mod, "loads", None)
InvalidProjectError = getattr(_mod, "InvalidProjectError", None)
_schema = importlib.import_module("waterprint.contracts.project_schema")
ProjectFile = getattr(_schema, "ProjectFile", None)
DesignState = getattr(_schema, "DesignState", None)
ViewState = getattr(_schema, "ViewState", None)
Metadata = getattr(_schema, "Metadata", None)

pytestmark = pytest.mark.skipif(
    None in (save_project, load_project, dumps, loads),
    reason="实现未就绪：waterprint.project.io（M1）",
)


def _minimal_project() -> object:
    """最小项目：浮点参数（nodes/假设覆盖）+ 边 + 带零偏移时间戳的 view。"""
    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={"u1": {"pool_length": 10.5, "pool_width": 4.25}},
            edges=[{"src": "u1:p_out", "dst": "u2:p_in"}],
            assumption_overrides={"safety.superheight": 0.3},
        ),
        view=ViewState(timestamp="2026-08-25T00:00:00Z"),
        metadata=Metadata(
            format_version="1.0",
            content_hash="0" * 64,
            engine_version="0.1.0",
            data_version="coefficients@0.1.0",
        ),
    )


def test_double_save_is_byte_identical_wiring() -> None:
    """R1 接线断言：同对象两次 dumps 字节级相同（键排序/定点浮点/无时钟）。"""
    first = dumps(_minimal_project())
    second = dumps(_minimal_project())
    assert first == second
    assert "10.5" in first  # 浮点参数确在输出（数据面非空壳）
    assert first.endswith("\n") and "\r" not in first  # 尾换行统一 \n


def test_roundtrip_lossless_wiring(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：save→load→save 字节相同。"""
    path = tmp_path / "roundtrip.wp.json"
    save_project(_minimal_project(), path)
    first = path.read_text(encoding="utf-8")
    save_project(load_project(path), path)
    assert path.read_text(encoding="utf-8") == first


def test_malformed_input_rejected_wiring() -> None:
    """R3 接线断言：未知字段/超深 JSON 拒绝且错误消息含字段路径。"""
    payload = json.loads(dumps(_minimal_project()))
    payload["design"]["totally_unknown"] = 1
    with pytest.raises(InvalidProjectError, match="design.totally_unknown"):
        loads(json.dumps(payload))
    deep: dict = {}
    cursor = deep
    for _ in range(120):
        cursor["n"] = {}
        cursor = cursor["n"]
    bomb = {"format_version": "1.0", "design": {"influent": deep}, "view": {},
            "metadata": {"content_hash": "0", "engine_version": "0",
                         "data_version": "0"}}
    with pytest.raises(InvalidProjectError, match="深度"):
        loads(json.dumps(bomb))
