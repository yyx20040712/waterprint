"""tests/report 公共夹具：golden 项目（仓内）+ report golden 产物（仓内入库）。

result.json/diag.json 由 tools/report_golden.py（批6k 脚本化入库——增补
六十二②）直调 core app 正门跑 golden municipal_34760 产出入库；管线测试经
waterprint.contracts.result_schema.deserialize 读它——产物入库后缺失=
仓库损坏 belt（skip 通道保留；CI agent job 的 skip==0 拦截兜底红显）。
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
# 仓内入库产物（批6k——tools/report_golden.py --write 重录；原系统临时目录
# 一次性产物口径退役，env 覆盖通道保留）
_SNAP_DIR = Path(__file__).resolve().parent / "__snapshots__"
_DEFAULT_INREPO = _SNAP_DIR / "result.json"
_DEFAULT_INREPO_DIAG = _SNAP_DIR / "diag.json"


def golden_result_path() -> Path:
    """result.json 路径解析：环境变量优先，缺省仓内入库产物。"""
    return Path(os.environ.get(_RESULT_ENV, str(_DEFAULT_INREPO)))


def golden_diag_path() -> Path:
    """diag.json 路径解析（与 result.json 同批产出入库）。"""
    return Path(os.environ.get(_DIAG_ENV, str(_DEFAULT_INREPO_DIAG)))


@pytest.fixture(scope="session")
def golden_project_path() -> Path:
    """golden 项目文件路径（仓内——必定存在）。"""
    path = _GOLDEN_CASE / "input_project.json"
    assert path.is_file(), f"golden 项目文件缺失：{path}"
    return path


@pytest.fixture(scope="session")
def golden_plant() -> PlantResult:
    """golden PlantResult（仓内入库产物——缺失即 skip=仓库损坏 belt）。"""
    path = golden_result_path()
    if not path.is_file():
        pytest.skip(f"golden result.json 缺失（一次性脚本未跑）：{path}")
    return deserialize(path.read_bytes())


@pytest.fixture(scope="session")
def golden_diag() -> DiagnosticsReport:
    """golden DiagnosticsReport（与 result.json 同批入库——缺失即 skip belt）。"""
    path = golden_diag_path()
    if not path.is_file():
        pytest.skip(f"golden diag.json 缺失（一次性脚本未跑）：{path}")
    return deserialize_diag(path.read_bytes())
