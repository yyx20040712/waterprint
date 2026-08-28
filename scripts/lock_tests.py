"""锁定测试文件：生成/刷新 test-lock.manifest.json 并设置只读属性。

输入:  core/tests 与 server/tests 全部文件（+ 可选命令行追加路径）；
       --prune 显式放行既有条目删除（默认被键集只增不减守卫拦截）
输出:  根目录 test-lock.manifest.json（sha256 清单）+ 文件只读属性
"""

# ══════════════════════════════════════════════════════════════════
# 规格（流程约定，AGENTS.md §7）：
#   本脚本只能由人类在"显式修改/新增测试"之后执行，作为独立 commit
#   接受审查；AI 不得运行本脚本。变更测试 = 显式事件，不是顺手行为。
# 守卫（COST2 事故设防：裸跑曾挤掉 units_lib 包内 38 条 tests 条目）：
#   写出前比对现有 manifest 键集——既有条目将被删除且命令行未带
#   --prune 时拒绝写出（return 2，manifest 字节不变）；无路径参数
#   裸跑时先打印防呆警示。
# 用法：
#   python scripts/lock_tests.py                        锁定两测试根
#   python scripts/lock_tests.py core/waterprint/units_lib/municipal/aao/tests
#                                                      追加锁定某单元测试
#   python scripts/lock_tests.py --prune <路径...>       显式放行删除既有条目
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


def existing_keys() -> set[str] | None:
    """读现有 manifest 键集（守卫比对用）；不可读/损坏/非对象返回 None。"""
    try:
        raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return set(raw) if isinstance(raw, dict) else None


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    prune = False
    extra_paths: list[str] = []
    for token in argv[1:]:
        if token == "--prune":
            prune = True
        elif token.startswith("-"):
            print(f"[FAIL] 未知参数: {token}（仅支持 --prune；路径参数不以 - 开头）")
            return 2
        else:
            extra_paths.append(token)
    roots = [REPO / rel for rel in DEFAULT_ROOTS]
    for extra in extra_paths:
        target = (REPO / extra).resolve()
        if REPO not in target.parents:
            print(f"[FAIL] 拒绝仓库外路径: {extra}")
            return 2
        roots.append(target)

    print("本操作将（重新）生成测试锁定清单并设置只读属性——")
    print("仅限人类在显式测试变更后执行（AGENTS.md §7）。")
    if not extra_paths:
        print("[警示] 裸跑两默认根将不含 units_lib 包内 tests 条目——"
              "若既有条目被挤出将由守卫拦截")
    entries: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            print(f"[FAIL] 目录不存在: {root.relative_to(REPO)}")
            return 2
        entries.update(collect(root))

    if MANIFEST.exists():
        existing = existing_keys()
        if existing is None:
            if not prune:
                print("[FAIL] 现有 manifest 不可读/损坏——拒绝盲写；"
                      "确认后可用 --prune 显式放行重锁")
                return 2
            print("[警示] 现有 manifest 不可读，--prune 模式按全新清单重锁")
        else:
            dropped = sorted(existing - set(entries))
            if dropped and not prune:
                print(f"[FAIL] 拒绝写出：将删除 {len(dropped)} 个既有锁定条目"
                      "（键集只增不减）：")
                for key in dropped[:5]:
                    print(f"  - {key}")
                if len(dropped) > 5:
                    print(f"  …（余 {len(dropped) - 5} 条略）")
                print("正确姿势：显式携带覆盖旧条目的完整根清单重跑"
                      "（含 units_lib 包内 tests 路径）；")
                print("确属有意删除条目：加 --prune 显式放行（用法见 scripts/README.md）。")
                return 2

    payload = json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    MANIFEST.write_text(payload, encoding="utf-8", newline="\n")
    for rel in entries:
        set_readonly(REPO / rel)
    print(f"[OK] 已锁定 {len(entries)} 个测试文件 → {MANIFEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
