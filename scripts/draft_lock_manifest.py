"""锁面 manifest 草稿重生成器：工作树实测 → 应然 manifest 草稿+差异报告。

输入:  test-lock.manifest.json + check_readonly 同一扫描宇宙
       （core/tests + server/tests + units_lib 包内 tests）
输出:  一致=[OK]（退出码 0）；漂移=新增/删除/哈希变清单+重锁命令
       草稿（退出码 1）。**只读投影——绝不写出 manifest**（AGENTS §7：
       重锁=人类执行 lock_tests.py 的显式事件，本脚本把「拼根清单+
       算差异」的机器半边代劳，人审半边不变）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（GOV4 B1-1 / ADR-015，2026-09-12）：锁面是全仓最热治理文件
# （148 次重锁实录）——check_readonly 检测漂移，但修复动作的人类
# 成本在「拼对全根清单+定位差异」。本脚本（CI gates job 红面时跑，
# 本地可随时跑）输出：差异三类清单+可复制的全根清单重锁命令。
# 边界：AI 可跑本脚本（只读）；AI 仍禁跑 lock_tests.py/改 manifest
# （AGENTS §7 不变）。扫描/哈希口径单源=check_readonly（import 复用，
# 零信任根触碰——sha256 CRLF 归一与忽略集与校验端恒同）。
# 用法：
#   python scripts/draft_lock_manifest.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_readonly import locked_files, load_manifest, sha256_of  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = ("core/tests", "server/tests")


def scan_roots(rels: list[str]) -> list[str]:
    """实测键集 → 显式全根清单（与 GOV3 键集反推法同型：两默认根
    保持在前，units_lib 包内 tests 以包级 tests 目录呈列）。"""
    roots: list[str] = []
    for rel in rels:
        if rel.startswith(DEFAULT_ROOTS[0] + "/"):
            root = DEFAULT_ROOTS[0]
        elif rel.startswith(DEFAULT_ROOTS[1] + "/"):
            root = DEFAULT_ROOTS[1]
        else:
            root = rel.split("/tests/")[0] + "/tests"
        if root not in roots:
            roots.append(root)
    return sorted(roots)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    paths = locked_files()
    draft = {p.relative_to(REPO).as_posix(): sha256_of(p) for p in paths}
    manifest = load_manifest()
    if not manifest:
        print("[FAIL] 锁面 manifest 缺失/不可读——草稿无从比对"
              "（人类执行 scripts/lock_tests.py 初锁，AGENTS §7）")
        return 1
    added = sorted(set(draft) - set(manifest))
    removed = sorted(set(manifest) - set(draft))
    changed = sorted(
        rel for rel in set(draft) & set(manifest) if draft[rel] != manifest[rel]
    )
    if not (added or removed or changed):
        print(f"[OK] 锁面草稿：manifest 与工作树实测一致（{len(draft)} 键）"
              "——门禁红面在别处，与锁面无关")
        return 0
    print(f"[FAIL] 锁面漂移草稿（工作树实测 {len(draft)} 键 vs manifest"
          f" {len(manifest)} 键）：新增 {len(added)} / 删除 {len(removed)} /"
          f" 哈希变 {len(changed)}")
    for label, items in (("新增", added), ("删除", removed), ("哈希变", changed)):
        for rel in items[:10]:
            print(f"  - {label}: {rel}")
        if len(items) > 10:
            print(f"    …（{label}余 {len(items) - 10} 条略）")
    print()
    print("重锁草稿命令（人类执行；AGENTS §7——AI 禁跑 lock_tests.py）：")
    print("  python scripts/lock_tests.py " + " ".join(scan_roots(sorted(draft))))
    if removed:
        print("注意：含删除条目——确属有意删除须加 --prune 显式放行"
              "（键集只增不减守卫，COST2 事故设防）。")
    print("重锁后：只读位随脚本设置；独立 commit 必带 [HUMAN-LOCK] 标签"
          "+逐文件修改动机（check_trust_root 双面拦截）。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
