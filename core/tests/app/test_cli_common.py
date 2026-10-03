"""cli_common 镜像测试：CLI 域共享底座恒等钉（kbwire-20261003）。

输入:  waterprint.cli_common（_EXIT_* 四常量+_DATA_DIR_DEFAULT+
       _user_out/_data_dir——cli.py 原文零迁移面）
输出:  恒等断言——退出码契约 0/2/3/4+'..' 分量拒+数据根缺省解析。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint.cli_common import (
    _DATA_DIR_DEFAULT,
    _EXIT_CALCULATION,
    _EXIT_OK,
    _EXIT_USAGE,
    _EXIT_VALIDATION,
    _data_dir,
    _user_out,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_exit_code_contract_and_path_pins(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """恒等钉：_EXIT 四值 0/2/3/4（R1 语义链）+_user_out 三态（None=缺省
    原值直返/'..'/相对路径 cwd 基准 resolve）+_data_dir 缺省解析（回炉 R4）。"""
    assert (_EXIT_OK, _EXIT_USAGE, _EXIT_VALIDATION, _EXIT_CALCULATION) == (0, 2, 3, 4)
    default = tmp_path / "d.result.json"
    assert _user_out(None, default) == default  # 回炉 R4：None=缺省原值直返
    assert _user_out("..", default) is None  # '..' 分量拒
    assert "越界分量" in capsys.readouterr().err
    assert _user_out("rel.json", default) == (Path.cwd() / "rel.json").resolve()
    assert _data_dir(None) == _DATA_DIR_DEFAULT
    assert (_REPO_ROOT / "data").resolve() == _DATA_DIR_DEFAULT
    assert _data_dir(str(tmp_path)) == tmp_path.resolve()
