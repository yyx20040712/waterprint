"""tests/report 公共夹具：golden 项目（仓内）+ 一次性 result.json（系统临时目录）。

result.json 由一次性脚本（系统临时目录，不入库）直调 core app 正门跑
golden municipal_34760 产出；管线测试经 waterprint.contracts.result_schema
.deserialize 读它——数据缺失时整组 skip（不锁死 CI）。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from waterprint.contracts.result_schema import PlantResult, deserialize
from waterprint.contracts.trust import DiagnosticsReport, deserialize_diag

_REPO = Path(__file__).resolve().parents[3]
_GOLDEN_CASE = (
    _REPO / "core" / "tests" / "golden" / "golden_data" / "municipal_34760"
)
_RESULT_ENV = "WATERPRINT_REPORT_GOLDEN_RESULT"
_DIAG_ENV = "WATERPRINT_REPORT_GOLDEN_DIAG"
_DEFAULT_TMP = (
    Path(os.environ.get("TEMP", "/tmp")) / "waterprint-track-c" / "result.json"
)
_DEFAULT_TMP_DIAG = (
    Path(os.environ.get("TEMP", "/tmp")) / "waterprint-track-c" / "diag.json"
)


def golden_result_path() -> Path:
    """result.json 路径解析：环境变量优先，缺省系统临时目录一次性产物。"""
    return Path(os.environ.get(_RESULT_ENV, str(_DEFAULT_TMP)))


def golden_diag_path() -> Path:
    """diag.json 路径解析（与 result.json 同批产出）。"""
    return Path(os.environ.get(_DIAG_ENV, str(_DEFAULT_TMP_DIAG)))


@pytest.fixture(scope="session")
def golden_project_path() -> Path:
    """golden 项目文件路径（仓内——必定存在）。"""
    path = _GOLDEN_CASE / "input_project.json"
    assert path.is_file(), f"golden 项目文件缺失：{path}"
    return path


@pytest.fixture(scope="session")
def golden_plant() -> PlantResult:
    """golden PlantResult（一次性脚本产物——缺失即 skip）。"""
    path = golden_result_path()
    if not path.is_file():
        pytest.skip(f"golden result.json 缺失（一次性脚本未跑）：{path}")
    return deserialize(path.read_bytes())


@pytest.fixture(scope="session")
def golden_diag() -> DiagnosticsReport:
    """golden DiagnosticsReport（与 result.json 同批——缺失即 skip）。"""
    path = golden_diag_path()
    if not path.is_file():
        pytest.skip(f"golden diag.json 缺失（一次性脚本未跑）：{path}")
    return deserialize_diag(path.read_bytes())
