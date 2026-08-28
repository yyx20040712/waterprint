"""cli 镜像测试：命令行入口（退出码语义/new-unit 幂等保护/编码防线）。

输入:  waterprint.cli.main 公开符号
输出:  CLI 契约断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.cli")
main = getattr(_mod, "main", None)

pytestmark = pytest.mark.skipif(
    main is None,
    reason="实现未就绪：waterprint.cli（M1）",
)


def test_exit_code_semantics_wiring(tmp_path: Path) -> None:
    """R1 接线断言（NET2 填真实现）：0 成功 / 2 用法错误 / 3 校验失败。

    无参调用→2（argparse required 子命令缺失）；坏项目文件→3（network
    子命令读入不存在文件=读入校验失败口径——v2 首发子命令语义同 R1）。
    """
    assert main([]) == 2
    assert main(["network", str(tmp_path / "nonexistent.xlsx")]) == 3


def test_new_unit_refuses_existing_target_wiring(tmp_path: Path) -> None:
    """R2 接线断言（NET2 填真实现）：目标单元包已存在 = 拒绝（防误覆盖）。

    --root 指向 tmp 复制的模板根：首次生成成功（0）；同参再生成同一
    'test_demo' 目标 → 第二次拒绝（非 0——幂等保护）。
    """
    import shutil

    template = Path(__file__).resolve().parents[2] / "waterprint" / "units_lib" / "_template"
    root = tmp_path / "units_lib"
    shutil.copytree(template, root / "_template", ignore=shutil.ignore_patterns("__pycache__"))
    first = main(["new-unit", "municipal", "test_demo", "--root", str(root)])
    assert first == 0
    assert (root / "municipal" / "test_demo").is_dir()
    second = main(["new-unit", "municipal", "test_demo", "--root", str(root)])
    assert second != 0
