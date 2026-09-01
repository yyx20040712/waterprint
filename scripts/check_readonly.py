"""测试只读门禁：manifest 哈希一致 + 只读属性齐备 + 无未登记文件。

输入:  仓库根 test-lock.manifest.json + core/tests、server/tests、
       core/waterprint/units_lib 包内 tests 目录实际文件
       （+ 追加锁定路径：清单登记即逐条校验存在性/哈希/只读属性——
       lock_tests.py <路径> 追加先例的读取面闭合，M1b R1-d）
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS.md §7——测试文件只读，防"改测试让失败消失"。
# 三重校验：哈希未变、写权限已除、无 manifest 外新增文件。
# 运行时产物（__pycache__ 等）在忽略清单内，不参与校验。
# 属性校验仅在 Windows 本地开发环境强制（git clone 丢失只读位；
# CI/Linux 侧内容完整性由哈希校验承担，属性是本地写屏障）。
# H2 扩根（外审整改#3，WP2）：units_lib 包内 tests 目录纳入常驻
# 扫描面——此前仅在 manifest 逐条校验，"未登记即 FAIL"强制面不含
# 包内新增测试（缺口闭合）。glob 形态自 manifest 66 键实测归纳：
#   core/waterprint/units_lib/_template/tests/*          一层（模板直挂）
#   core/waterprint/units_lib/<line>/<package>/tests/*   两层（线/包）
# 判定口径=路径含段名 tests（只收 tests 目录，不收单元源码）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "test-lock.manifest.json"
LOCKED_ROOTS = ("core/tests", "server/tests")
# H2 扩根：units_lib 全树扫描但只收路径段名含 tests 的文件（见头注
# glob 形态）——新单元 tests/ 2 文件在人类 lock_tests.py 重锁前会被
# 判"未登记" FAIL，属预期流程闸（AGENTS §11 重锁口径）。
TESTS_SEGMENT_ROOTS = ("core/waterprint/units_lib",)
IGNORED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".hypothesis",
    "__snapshots__",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}

ATTR_BARRIER_ACTIVE = sys.platform == "win32" and os.environ.get("CI") != "true"


def sha256_of(path: Path) -> str:
    """哈希口径：文本内容 CRLF 归一为 LF 后哈希——对齐 .gitattributes
    eol=lf 的入库口径，本地 CRLF 检出（工具写入习惯）与 CI LF 检出同
    哈希；二进制（UTF-8 解码失败，如 .xlsx）保持原字节哈希。与
    scripts/lock_tests.py 同口径实现（锁定端/校验端一致）。"""
    data = path.read_bytes()
    with contextlib.suppress(UnicodeDecodeError):
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def locked_files() -> list[Path]:
    found: list[Path] = []
    for rel in LOCKED_ROOTS:
        root = REPO / rel
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relparts = path.relative_to(REPO).parts
            if IGNORED_DIR_NAMES.intersection(relparts):
                continue
            if path.suffix in IGNORED_SUFFIXES:
                continue
            found.append(path)
    for rel in TESTS_SEGMENT_ROOTS:
        root = REPO / rel
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if "tests" not in path.relative_to(root).parts:
                continue  # H2 扩根只收 tests 目录，不收单元源码
            relparts = path.relative_to(REPO).parts
            if IGNORED_DIR_NAMES.intersection(relparts):
                continue
            if path.suffix in IGNORED_SUFFIXES:
                continue
            found.append(path)
    return found


def load_manifest() -> dict[str, str]:
    if not MANIFEST.is_file():
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    entries = load_manifest()
    if not entries:
        problems.append(
            f"缺少锁定清单 {MANIFEST.relative_to(REPO)}（由人类运行 scripts/lock_tests.py 生成）"
        )

    actual = {p.relative_to(REPO).as_posix() for p in locked_files()}
    for rel in sorted(actual - set(entries)):
        problems.append(f"未登记的测试文件（疑似绕过锁定流程新增）: {rel}")
    for rel in sorted(set(entries) - actual):
        # 清单登记但不在任何常驻扫描根内的路径（H2 扩根后 units_lib
        # 包内 tests 已入扫描面；其余假想追加路径）仍逐条校验存在性/
        # 哈希/只读属性——"无未登记新增"在全部常驻扫描根内强制。
        path = REPO / rel
        if not path.is_file():
            problems.append(f"清单中的文件已不存在（删除测试须走解锁流程）: {rel}")
            continue
        if sha256_of(path) != entries[rel]:
            problems.append(f"内容与锁定清单不符（被改动）: {rel}")
        if ATTR_BARRIER_ACTIVE and os.access(path, os.W_OK):
            problems.append(f"只读属性缺失: {rel}")
    for path in locked_files():
        rel = path.relative_to(REPO).as_posix()
        expected = entries.get(rel)
        if expected is None:
            continue
        if sha256_of(path) != expected:
            problems.append(f"内容与锁定清单不符（被改动）: {rel}")
        if ATTR_BARRIER_ACTIVE and os.access(path, os.W_OK):
            problems.append(f"只读属性缺失: {rel}")

    if problems:
        print(f"[FAIL] 测试只读校验违规 {len(problems)} 处：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[OK] 测试只读：{len(entries)} 个文件哈希与属性校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
