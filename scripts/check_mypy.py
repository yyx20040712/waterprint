"""mypy 门禁：双根（core+server）本地聚合 CI quality 同款 strict 检查。

输入:  core/server 源码树 + 各自 .venv 内的 mypy（解释器逐根按 win/posix
       双路径定位——互不代偿）
输出:  逐根三态单行 [OK]/[FAIL]/[SKIP]（mypy 输出透传）；任一根 FAIL =
       退出码 1；venv 缺失根 = SKIP（双根皆缺 = 双 SKIP 退出码 0）；
       venv 解释器在但子进程不可用（OSError 族）= 该根 FAIL 兜底
       （SC1 D9①——禁裸抛 traceback；SKIP 语义红线不破）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（出处：CI .github/workflows/ci.yml core/server quality job
# 同款命令 `uv run mypy`；conv-golden 批 2026-10-02 曾因本地门禁不含
# mypy 致 executor.py:280 arg-type 逃逸至 CI 三处红——本脚本补齐本地
# 聚合口径，消灭"本地绿、CI 红"盲区；check_ruff/check_lint_imports
# 同制第三例，三态口径与 OSError 兜底逐条同款（T7a C416 教训族））。
#   a) SCAN_ROOTS 双根（core/server）：逐根定位各自虚拟环境解释器
#      （win=`<root>/.venv/Scripts/python.exe`、posix=`<root>/.venv/bin/
#      python`）；缺失根 = 该根单行 [SKIP] 退出码不计失败——CI「架构门禁
#      （零依赖，系统 Python）」job 不装 venv，双 SKIP=退出码 0 属预期
#      路径（mypy 由 core/server quality job 各自承担）；本地同样 SKIP
#      但提示属 CI 预期（宪法环境在册）——逐根独立无跨根耦合；
#   b) 根 venv 存在：以该解释器执行 `-m mypy`（cwd=该根——mypy 按 cwd
#      取各自 pyproject.toml 的 [tool.mypy] 配置[含 files 清单与 strict]，
#      零配置改动），stdout/stderr 捕获后透传；mypy 未装或退出码非 0
#      （1=类型错/2=致命错，均红）= 该根 [FAIL]，任一根 FAIL 即退出
#      码 1。耗时注记：core 全量 strict 冷跑约 1 分钟（增量缓存
#      .mypy_cache 自动生效）——慢于 ruff 属类型检查固有成本。
#   残余盲区记档（mypy-gate 批门一 k2-N1/N3、d1-W1/W3——先例继承面，
#      本门禁不消灭仅如实显化）：①SKIP≠已检（venv 缺根该根类型面本次
#      未执行——SKIP 行显式声明）；②[tool.mypy].files 为覆盖面子真源，
#      收窄即静默（CI 同配置同盲区，不另设断言——同制范围外）；③本地
#      单版本 venv 不覆盖 CI 版本矩阵（core 3.12/3.13、server 3.13/
#      3.14——stdlib stubs/新语法面可分叉，本地绿≠四面全绿）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# 双根扫描面（根名, 根路径）——mypy 按 cwd 取各自 pyproject 配置。
SCAN_ROOTS: tuple[tuple[str, Path], ...] = (
    ("core", REPO / "core"),
    ("server", REPO / "server"),
)


def locate_venv_python(root: Path) -> Path | None:
    """返回首个存在的该根 venv 解释器；win/posix 双路径均缺失返回 None。"""
    for candidate in (
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return candidate
    return None


def emit(text: str) -> None:
    """透传子进程输出（确保按行结尾规整，空串不打）。"""
    if text:
        print(text, end="" if text.endswith("\n") else "\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failed = False
    for name, root in SCAN_ROOTS:
        python = locate_venv_python(root)
        if python is None:
            print(f"[SKIP] check_mypy：{name}（venv 缺失——SKIP≠已检，该根类型面本次未执行；"
                  f"CI 零依赖 job 预期路径；本地运行请在 {name}/ 下 uv sync 安装 dev 依赖）")
            continue
        print(f"[INFO] 解释器 {python.relative_to(REPO).as_posix()}（透传 mypy）")
        # SC1 D9①：OSError 现实异常族显式枚举兜底（venv 解释器在但不可执行/
        # 已损坏——PermissionError/FileNotFoundError 等禁裸抛 traceback；
        # SKIP 语义红线不破：仅 venv 解释器路径缺失才 SKIP，此处=FAIL）。
        try:
            result = subprocess.run(
                [str(python), "-m", "mypy"],
                cwd=root,
                check=False,
                capture_output=True,
            )
        except (OSError, PermissionError, FileNotFoundError) as exc:
            print(f"[FAIL] check_mypy：{name}（子进程不可用：{exc}——"
                  "venv 解释器异常，请重建 venv：uv sync）")
            failed = True
            continue
        emit(result.stdout.decode("utf-8", errors="replace"))
        emit(result.stderr.decode("utf-8", errors="replace"))
        if result.returncode != 0:
            print(f"[FAIL] check_mypy：{name}")
            failed = True
        else:
            print(f"[OK] check_mypy：{name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
