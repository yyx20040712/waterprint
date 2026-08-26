"""锁定测试文件：生成/刷新 test-lock.manifest.json 并设置只读属性。

输入:  core/tests 与 server/tests 全部文件（+ 可选命令行追加路径）
输出:  根目录 test-lock.manifest.json（sha256 清单）+ 文件只读属性
"""

# ══════════════════════════════════════════════════════════════════
# 规格（流程约定，AGENTS.md §7）：
#   本脚本只能由人类在"显式修改/新增测试"之后执行，作为独立 commit
#   接受审查；AI 不得运行本脚本。变更测试 = 显式事件，不是顺手行为。
# 用法：
#   python scripts/lock_tests.py                        锁定两测试根
#   python scripts/lock_tests.py core/waterprint/units_lib/municipal/aao/tests
#                                                      追加锁定某单元测试
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "test-lock.manifest.json"
DEFAULT_ROOTS = ("core/tests", "server/tests")
IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".hypothesis", "__snapshots__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256_of(path: Path) -> str:
    """哈希口径：文本内容 CRLF 归一为 LF 后哈希——对齐 .gitattributes
    eol=lf 的入库口径，本地 CRLF 检出（工具写入习惯）与 CI LF 检出同
    哈希；二进制（UTF-8 解码失败，如 .xlsx）保持原字节哈希。与
    scripts/check_readonly.py 同口径实现（校验端/锁定端一致）。"""
    data = path.read_bytes()
    with contextlib.suppress(UnicodeDecodeError):
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def collect(root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if IGNORED_DIR_NAMES.intersection(path.relative_to(REPO).parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        entries[path.relative_to(REPO).as_posix()] = sha256_of(path)
    return entries


def set_readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    roots = [REPO / rel for rel in DEFAULT_ROOTS]
    for extra in argv[1:]:
        target = (REPO / extra).resolve()
        if REPO not in target.parents:
            print(f"[FAIL] 拒绝仓库外路径: {extra}")
            return 2
        roots.append(target)

    print("本操作将（重新）生成测试锁定清单并设置只读属性——")
    print("仅限人类在显式测试变更后执行（AGENTS.md §7）。")
    entries: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            print(f"[FAIL] 目录不存在: {root.relative_to(REPO)}")
            return 2
        entries.update(collect(root))

    payload = json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    MANIFEST.write_text(payload, encoding="utf-8", newline="\n")
    for rel in entries:
        set_readonly(REPO / rel)
    print(f"[OK] 已锁定 {len(entries)} 个测试文件 → {MANIFEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
