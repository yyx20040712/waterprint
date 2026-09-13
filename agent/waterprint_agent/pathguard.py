"""沙箱路径守卫（PathGuard）：agent 面一切文件 IO 的唯一正门（D4）。

输入:  沙箱根 + 相对路径（area 归位）或正式区绝对路径（只读装载）
输出:  归一后的沙箱内绝对路径 / 校验通过的只读路径；越界 raise PathGuardError
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13；门一 FIX-2 2026-09-13 回炉增补）
#   路径：agent/waterprint_agent/pathguard.py
#   职责：Windows 专项条款（盘符/大小写/junction 归一）下的沙箱前缀守卫；
#       工具面文件路径参数一律先过本门（设计书 v2 D4 修订点 1）。外部
#       只读装载（open_readonly_external）经 external_roots 白名单根
#       前缀校验（门一审查§九：正式区语义收口——任何绝对路径可过的
#       缺口闭合，缺省 ()=全拒 fail-closed）。
#   禁区：本模块禁 import core/server/fastmcp（纯 stdlib——main 顶层
#       懒加载链的一环）；禁在此读写文件（守卫只做解析与判定）；禁
#       硬编码绝对路径（白名单根由 context 装配注入）。
#
# 【公开接口】（任务书 §3 预裁决冻结+门一 FIX-2 增补）
#   class PathGuardError(ValueError)：拒绝统一载体。
#   class PathGuard：
#       __init__(sandbox_root: Path, external_roots: tuple[Path, ...] = ())
#       resolve_in(relative: Path, *, area) -> Path
#       open_readonly_external(path: Path) -> Path
#   AREAS：五区白名单（projects/exports/results/sessions/reports）。
#
# 【行为规格】
#   R1 归一：统一 os.path.realpath（解 symlink/junction）+os.path.normcase
#      （盘符与大小写归一）后做前缀比较——Windows 分隔符/大小写/短名
#      变体全部折叠到同一规范形（N 级吸收条款）。
#   R2 拒绝面：'..' 分量、绝对路径、盘符相对形态（C:xxx）、UNC（\\\\srv\\share）、
#      跨盘符重定向、area 内 junction/symlink 解析后逃逸前缀——一律
#      PathGuardError（fail-closed）。
#   R3 前缀判定：归一后须落在 {root}/{area} 组件前缀内（is_relative_to
#      组件级比较，杜绝 "projects_x" 字符串前缀误放行）。
#   R4 正式区只读门（门一 FIX-2 收口）：open_readonly_external 校验
#      存在+是文件+归一后落某一 external_roots 白名单根组件前缀内
#      （同盘符+is_relative_to——"zone-a-evil" 字符串前缀不误放行）；
#      白名单缺席（缺省 ()）=全拒（fail-closed）；越界读取行为本身
#      即拒（不再只校验存在性）；写路径不走此门（写入只经 resolve_in
#      落沙箱；正式区文件 mtime/权限零触碰）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
from pathlib import Path
from typing import Final, Literal

__all__ = ["AREAS", "Area", "PathGuard", "PathGuardError"]

Area = Literal["projects", "exports", "results", "sessions", "reports"]
AREAS: Final[tuple[str, ...]] = ("projects", "exports", "results", "sessions", "reports")


class PathGuardError(ValueError):
    """沙箱路径守卫拒绝（前缀逃逸/../UNC/跨盘符/junction 越界/只读门缺失）。"""


def _normalize(path: Path) -> Path:
    """R1 归一：realpath（解 junction/symlink，非严格——不存在路径解到最深）+normcase。"""
    return Path(os.path.normcase(os.path.realpath(path)))


class PathGuard:
    """沙箱唯一 IO 门（无状态守卫——线程安全）。

    external_roots：正式区只读装载白名单根（门一 FIX-2——R4 条款）；
    归一口径与沙箱根一致（realpath+normcase），缺省空元组=全拒。
    """

    def __init__(
        self, sandbox_root: Path, external_roots: tuple[Path, ...] = ()
    ) -> None:
        self._root = _normalize(Path(sandbox_root))
        self._area_roots: dict[str, Path] = {area: _normalize(self._root / area) for area in AREAS}
        self._external_roots = tuple(_normalize(Path(root)) for root in external_roots)

    @property
    def root(self) -> Path:
        """归一后的沙箱根（比较面公开只读）。"""
        return self._root

    def resolve_in(self, relative: Path, *, area: Area) -> Path:
        """相对路径 → {root}/{area} 内绝对路径（越界即拒——R2/R3）。"""
        rel = Path(relative)
        if rel.is_absolute():
            raise PathGuardError(
                f"拒绝绝对路径 {relative!s}（沙箱内 IO 只收相对路径，"
                f"area={area} 基点内拼接是唯一合法构造）"
            )
        if rel.drive:  # 盘符相对（C:xxx）与 UNC（\\\\srv\\share）均带 drive 形态
            raise PathGuardError(
                f"拒绝盘符/UNC 形态路径 {relative!s}（跨盘符重定向与网络路径不走沙箱门）"
            )
        if any(part == ".." for part in rel.parts):
            raise PathGuardError(f"拒绝 '..' 分量路径 {relative!s}（前缀逃逸防护）")
        if area not in self._area_roots:
            raise PathGuardError(f"未知 area {area!r}（白名单 {AREAS}）")
        base = self._area_roots[area]
        candidate = _normalize(base / rel)
        if candidate.drive != base.drive or not candidate.is_relative_to(base):
            raise PathGuardError(
                f"路径 {relative!s} 解析越界（realpath 后={candidate}，须落 {base} 前缀内"
                "——junction/symlink 逃逸或跨盘符重定向）"
            )
        return candidate

    def open_readonly_external(self, path: Path) -> Path:
        """正式区只读装载门（R4——门一 FIX-2 收口）。

        存在+是文件+归一后落某一 external_roots 白名单根组件前缀内
        （同盘符+is_relative_to）→ 返回解析路径；白名单缺席或越界
        =PathGuardError（fail-closed——读取行为本身即拒）。"""
        resolved = Path(os.path.realpath(Path(path)))
        if not resolved.exists():
            raise PathGuardError(f"正式区只读装载失败：{path!s} 不存在")
        if not resolved.is_file():
            raise PathGuardError(f"正式区只读装载失败：{path!s} 非文件（目录不可装载）")
        normalized = _normalize(resolved)
        if not any(
            normalized.drive == root.drive and normalized.is_relative_to(root)
            for root in self._external_roots
        ):
            raise PathGuardError(
                f"正式区只读装载越界：{path!s} 不在外部根白名单内"
                f"（白名单 {len(self._external_roots)} 根，缺省=全拒"
                "——D4 正式区语义，门一 FIX-2）"
            )
        return resolved
