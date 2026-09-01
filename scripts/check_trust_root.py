"""信任根守卫门禁：触碰三信任根的 commit 必须在首行携带 [HUMAN-LOCK] 标签。

输入:  git 历史与工作树——CI 模式=GITHUB_ACTIONS+GITHUB_EVENT_NAME 双
       条件下取 PR（GITHUB_PR_BASE）或 push（GITHUB_EVENT_BEFORE）
       range 逐 commit；本地模式=工作树 porcelain + HEAD commit
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：外审整改#3 H1——测试只读机制的"守卫的守卫"。三信任根=
#   test-lock.manifest.json / scripts/lock_tests.py /
#   scripts/check_readonly.py——AI 可改校验器让锁定形同虚设，故
#   三者自身变更=人类显式事件：commit message 首行必带 [HUMAN-LOCK]
#   （AGENTS.md §7 批准标记；限 subject 行，正文提及不豁免——G1-05）。
# CI 模式（G1-01/A-01）：GITHUB_ACTIONS=true 且 GITHUB_EVENT_NAME
#   非空才启用。PR 事件 range=GITHUB_PR_BASE..GITHUB_SHA（ci.yml 注入
#   base sha；直接 range 不可解析时 git merge-base 兜底折算共同祖先）；
#   push 事件 range=GITHUB_EVENT_BEFORE..GITHUB_SHA。
#   range 无法确定（首推/workflow_dispatch/基不可达）=直接 FAIL
#   拒绝放行（fail-closed，G1-02——无"退化 HEAD 单查"路径；手跑可
#   env GITHUB_EVENT_BEFORE 显式给定 range）。
# merge commit（G1-03）：git log --name-only 对 merge 恒输出 0 文件
#   ——检测到 ^2 父存在时改用 git diff-tree -m --first-parent 取
#   双亲 diff 并集（实证：8af4070 log 0 文件 vs diff-tree 并集 11
#   文件含 test-lock.manifest.json）。
# 本地模式：①porcelain 三信任根改动/未跟踪 FAIL（rename 行新旧
#   两端任一命中即违规——G1-04）②HEAD commit 触三件且首行无标签
#   FAIL。git 调用仅 stdlib subprocess（log/diff-tree/rev-parse/
#   merge-base/status --porcelain）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRUST_ROOTS = (
    "test-lock.manifest.json",
    "scripts/lock_tests.py",
    "scripts/check_readonly.py",
)
HUMAN_LOCK_TAG = "[HUMAN-LOCK]"


def git_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO,
        check=False,
    )


def git_output(args: list[str]) -> str:
    """跑一条 git 命令并返回 stdout；失败抛 RuntimeError（fail-closed）。"""
    result = git_run(args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} 失败")
    return result.stdout


def is_merge(sha: str) -> bool:
    """merge commit 判定：第二父（^2）可解析（G1-03）。"""
    return git_run(["rev-parse", "--verify", "--quiet", f"{sha}^2"]).returncode == 0


def commit_files(sha: str) -> set[str]:
    """commit 触碰的文件集。merge 的 log --name-only 恒空——改用
    diff-tree 双亲 diff 并集（G1-03；-r 递归到文件路径）。"""
    out = git_output(["log", "--name-only", "--format=%H", "-1", sha])
    lines = [ln.strip().strip('"') for ln in out.splitlines()]
    files = {ln for ln in lines[1:] if ln}
    if files or not is_merge(sha):
        return files
    out2 = git_output(
        ["diff-tree", "-r", "--name-only", "--no-commit-id", "-m", "--first-parent", sha]
    )
    return {ln.strip().strip('"') for ln in out2.splitlines() if ln.strip()}


def commit_message(sha: str) -> str:
    """commit 完整 message（%B=subject+body）。"""
    return git_output(["log", "--format=%B", "-1", sha])


def subject_line(sha: str) -> str:
    """message 首行（subject）——[HUMAN-LOCK] 只认此处（G1-05）。"""
    message = commit_message(sha).strip()
    return message.splitlines()[0] if message else ""


def check_commit(sha: str) -> list[str]:
    """单个 commit 的违规：触信任根且 subject 首行无 [HUMAN-LOCK]。"""
    touched = sorted(set(TRUST_ROOTS) & commit_files(sha))
    subject = "" if not touched else subject_line(sha)
    if not touched or HUMAN_LOCK_TAG in subject:
        return []
    preview = subject if len(subject) <= 40 else subject[:40] + "…"
    return [
        f"commit {sha[:12]}（{preview}）触碰信任根 "
        f"{', '.join(touched)} 且 message 首行无 {HUMAN_LOCK_TAG}"
    ]


def working_tree_offenders() -> list[str]:
    """工作树中三信任根的改动/未跟踪（rename 行新旧两端双校验——G1-04）。"""
    offenders: list[str] = []
    for line in git_output(["status", "--porcelain"]).splitlines():
        if len(line) <= 3:
            continue
        entry = line[3:].strip()
        endpoints = entry.split(" -> ", 1) if " -> " in entry else [entry]
        if any(e.strip().strip('"') in TRUST_ROOTS for e in endpoints):
            offenders.append(f"{line[:2].strip()} {entry}")
    return offenders


def range_commit_shas(before: str, after: str) -> list[str]:
    out = git_output(["log", "--format=%H", f"{before}..{after}"])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def try_range(candidates: list[str], after: str) -> tuple[list[str], str] | None:
    """按序尝试 before 候选；返回（shas, 实际使用的 before）或 None。"""
    for before in candidates:
        if not before:
            continue
        try:
            return range_commit_shas(before, after), before
        except RuntimeError:
            continue
    return None


def fail_closed(event: str) -> tuple[list[str], str]:
    return (
        ["range 不可解析：信任根守卫拒绝放行（fail-closed）——首推/workflow_dispatch"
         "等场景可 env GITHUB_EVENT_BEFORE（或 PR 场景 GITHUB_PR_BASE）显式给定后重跑"],
        f"CI 模式：GITHUB_EVENT_NAME={event}，range 无法确定",
    )


def ci_problems() -> tuple[list[str], str]:
    """CI 模式：PR/push range 逐 commit；range 不可定=fail-closed（G1-02）。"""
    event = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    after = os.environ.get("GITHUB_SHA", "").strip() or "HEAD"
    pr_base = os.environ.get("GITHUB_PR_BASE", "").strip()
    before = os.environ.get("GITHUB_EVENT_BEFORE", "").strip()
    candidates: list[str] = []
    kind = "push range"
    if pr_base:
        kind = "PR range"
        candidates.append(pr_base)
        try:  # 兜底：base sha 不在本地历史时折算共同祖先（G1-01）
            candidates.append(
                git_output(["merge-base", pr_base, after]).strip().splitlines()[0]
            )
        except (RuntimeError, IndexError):
            pass
    elif before and set(before) != {"0"}:
        candidates.append(before)
    else:
        return fail_closed(event)
    resolved = try_range(candidates, after)
    if resolved is None:
        return fail_closed(event)
    shas, used = resolved
    problems: list[str] = []
    for sha in shas:
        problems.extend(check_commit(sha))
    return problems, f"{kind} {used[:12]}..{after[:12]}（{len(shas)} commits）"


def local_problems() -> tuple[list[str], str]:
    """本地模式：工作树 porcelain 三件 + HEAD commit 首行标签。"""
    problems: list[str] = []
    for item in working_tree_offenders():
        problems.append(
            f"工作树信任根有未提交改动/未跟踪（{item}）——"
            f"须走 {HUMAN_LOCK_TAG} 人类呈报流程，AI 不得自行提交"
        )
    head = git_output(["log", "-1", "--format=%H"]).strip()
    problems.extend(check_commit(head))
    return problems, f"本地模式：工作树 porcelain + HEAD {head[:12]}"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        # CI 模式双条件（A-01）：防本地意外携带 GITHUB_ACTIONS 旁路工作树检测
        in_ci = (
            os.environ.get("GITHUB_ACTIONS") == "true"
            and bool(os.environ.get("GITHUB_EVENT_NAME", "").strip())
        )
        problems, scope = ci_problems() if in_ci else local_problems()
    except RuntimeError as exc:
        print(f"[FAIL] 信任根守卫无法执行（git 不可用？）：{exc}")
        return 1
    if problems:
        print(f"[FAIL] 信任根守卫违规 {len(problems)} 处（{scope}）：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[OK] 信任根守卫（{scope}）：三信任根无未批准触碰")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
