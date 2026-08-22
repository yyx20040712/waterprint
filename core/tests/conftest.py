"""core 测试系统装配：路径 fixtures 与 hypothesis 配置（薄装配，禁业务断言）。

输入:  无
输出:  core_root / golden_data_dir fixtures；scripts 与 core 入 sys.path；hypothesis 档案
"""

# ══════════════════════════════════════════════════════════════════
# 规格：本文件是唯一可承载装配逻辑的测试文件；禁止：业务断言、
# 自动 skip 全部测试的钩子（休眠判定只存在于各只读测试文件内的
# getattr 守卫，防"改 conftest 一处让全套测试失活"的投机路径）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

import pytest

CORE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = CORE_ROOT.parent
GOLDEN_DATA = Path(__file__).resolve().parent / "golden" / "golden_data"

# 门禁特征串定义（scripts/ 纯标准库）与内核包路径
for extra in (str(REPO_ROOT / "scripts"), str(CORE_ROOT)):
    if extra not in sys.path:
        sys.path.insert(0, extra)


@pytest.fixture(scope="session")
def core_root() -> Path:
    """core 项目根（core/）。"""
    return CORE_ROOT


@pytest.fixture(scope="session")
def golden_data_dir() -> Path:
    """golden 数据目录（两大案例 + 迁移样本）。"""
    return GOLDEN_DATA


def pytest_configure(config: pytest.Config) -> None:
    """注册并加载 hypothesis 档案（未安装时静默，性质测试自行守卫）。"""
    try:
        from hypothesis import settings
    except ModuleNotFoundError:
        return
    settings.register_profile("ci", max_examples=200, deadline=None)
    settings.register_profile("dev", max_examples=50, deadline=None)
    settings.load_profile("dev")
