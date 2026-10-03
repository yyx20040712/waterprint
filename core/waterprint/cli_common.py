"""CLI 域共享底座：退出码契约常量+数据根缺省+用户面输出/数据根裁定。

输入:  CLI 参数原值（out/data_dir 串或 None）
输出:  _EXIT_* 四常量+_DATA_DIR_DEFAULT+_user_out/_data_dir 裁定函数
       （cli.py/cli_calc.py 单向消费——same_layer_lib 先例同制共享库）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（kbwire-20261003 拆件：cli.py 500/500 贴墙——calc 命令域迁
#   cli_calc.py，本件承载 CLI 域共享底座；六符号自 cli.py 原文零迁移，
#   cli.py 经全名 import 保既有引用连续；依赖向 cli→cli_common/
#   cli_calc→cli_common 单向无环。镜像测试 tests/app/test_cli_calc.py ④
#   恒等钉（_EXIT 四值+'..' 拒+缺省解析）。）
#
# 【公开接口（CLI 域内部共享面）】
#   _EXIT_OK/_EXIT_USAGE/_EXIT_VALIDATION/_EXIT_CALCULATION: Final[int]
#       退出码契约（R1）：0=成功 2=用法错误 3=校验失败 4=计算失败
#       （3/4 经基值推导——字面量白名单 {0,1,2,10} 外须来自语义源）。
#   _DATA_DIR_DEFAULT: Final[Path]   仓库根 data（golden 同款 parents 解析）。
#   _user_out(out, default) -> Path | None   用户面输出路径裁定（R5 共用）：
#       '..' 分量拒（None+stderr）；相对路径以 cwd 为基准。
#   _data_dir(raw) -> Path   数据包根裁定：给定用之；缺省=仓库根 data。
#
# 【禁止事项】不持有子命令逻辑（命令域归 cli.py/cli_calc.py）；
#   零数值字面量（退出码经基值推导语义链）。
# 【参照】AGENTS §2 same_layer_lib 先例；cli.py（迁移源）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

# 退出码语义（R1）：0=成功 2=用法错误 3=校验失败 4=计算失败。
_EXIT_OK: Final[int] = 0
_EXIT_USAGE: Final[int] = 2
_EXIT_VALIDATION: Final[int] = _EXIT_USAGE + 1
_EXIT_CALCULATION: Final[int] = _EXIT_USAGE + 2
# 数据包根缺省（仓库根 data——golden 测试同款 parents 解析）。
_DATA_DIR_DEFAULT: Final[Path] = Path(__file__).resolve().parents[2] / "data"


def _user_out(out: str | None, default: Path) -> Path | None:
    """用户面输出路径裁定（R5 共用）：'..' 分量拒；相对路径以 cwd 为基准。"""
    if out is None:
        return default
    raw = Path(out)
    for part in raw.parts:
        if part == "..":
            print(f"[校验失败] 输出路径含越界分量 '..'：{raw}"
                  "（R5 同款口径——audit._validate_out）", file=sys.stderr)
            return None
    return (raw if raw.is_absolute() else Path.cwd() / raw).resolve()


def _data_dir(raw: str | None) -> Path:
    """数据包根裁定：--data-dir 给定用之；缺省=仓库根 data（golden 同款）。"""
    return Path(raw).resolve() if raw is not None else _DATA_DIR_DEFAULT
