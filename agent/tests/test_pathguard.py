"""test_pathguard——PathGuard 沙箱唯一 IO 门（前缀逃逸/../盘符/UNC/junction 条款）。

输入:  tmp_path 沙箱根 + 越界路径样本
输出:  拒绝路径断言（AI1-TRACK-B §3 预裁决 D4）
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from waterprint_agent.pathguard import AREAS, PathGuard, PathGuardError


def _make_root(tmp_path: Path) -> Path:
    root = tmp_path / "sb"
    for area in AREAS:
        (root / area).mkdir(parents=True, exist_ok=True)
    return root


def test_resolve_in_area_placement(tmp_path: Path) -> None:
    """area 归位：相对路径解析到 {root}/{area} 内的绝对路径。"""
    root = _make_root(tmp_path)
    guard = PathGuard(root)
    resolved = guard.resolve_in(Path("abc.wp.json"), area="projects")
    assert resolved == Path(os.path.normcase(os.path.realpath(root / "projects" / "abc.wp.json")))
    results_root = Path(os.path.normcase(os.path.realpath(root / "results")))
    nested = guard.resolve_in(Path("sub/dir/x.json"), area="results")
    assert nested.is_relative_to(results_root)  # 嵌套仍在 results 前缀内


def test_resolve_in_rejects_dotdot(tmp_path: Path) -> None:
    """拒 '..' 分量（显式逃逸）。"""
    guard = PathGuard(_make_root(tmp_path))
    with pytest.raises(PathGuardError):
        guard.resolve_in(Path("../escape.txt"), area="projects")
    with pytest.raises(PathGuardError):
        guard.resolve_in(Path("a/../../escape.txt"), area="exports")


def test_resolve_in_rejects_absolute_and_unc(tmp_path: Path) -> None:
    """拒绝对路径/UNC/盘符相对形态（跨盘符重定向面）。"""
    guard = PathGuard(_make_root(tmp_path))
    outside = tmp_path / "outside.txt"
    with pytest.raises(PathGuardError):
        guard.resolve_in(outside, area="projects")  # 绝对路径
    with pytest.raises(PathGuardError):
        # 盘符相对形态（非绝对但带 drive）
        guard.resolve_in(Path(r"C:windows/system32"), area="projects")
    with pytest.raises(PathGuardError):
        guard.resolve_in(Path(r"\\server\share\evil"), area="projects")  # UNC


def test_resolve_in_drive_letter_case_insensitive(tmp_path: Path) -> None:
    """Windows 盘符/大小写归一：根以异 Case 盘符形态传入仍归一同一前缀。"""
    root = _make_root(tmp_path)
    variant = Path(str(root).replace(root.drive, root.drive.lower(), 1))
    guard_lower = PathGuard(variant)
    guard_plain = PathGuard(root)
    assert guard_lower.root == guard_plain.root
    assert guard_lower.resolve_in(Path("x.json"), area="sessions") == guard_plain.resolve_in(
        Path("x.json"), area="sessions"
    )


def test_resolve_in_rejects_junction_escape(tmp_path: Path) -> None:
    """junction 前缀逃逸：area 内 junction 指向沙箱外 → realpath 解析后越前缀即拒。"""
    pytest.importorskip("_winapi")
    root = _make_root(tmp_path)
    outside = tmp_path / "outside-target"
    outside.mkdir()
    (outside / "secret.txt").write_text("x", encoding="utf-8")
    link = root / "projects" / "esc"
    import _winapi

    # Windows 3.12 无 os.junction（3.13 起）——私有通道
    _winapi.CreateJunction(str(outside), str(link))
    try:
        guard = PathGuard(root)
        with pytest.raises(PathGuardError):
            guard.resolve_in(Path("esc/secret.txt"), area="projects")
    finally:
        os.rmdir(link)  # junction 目录句柄（删链接不删目标）


def test_resolve_in_rejects_unknown_area(tmp_path: Path) -> None:
    """未知 area 拒绝（白名单五区）。"""
    guard = PathGuard(_make_root(tmp_path))
    with pytest.raises(PathGuardError):
        guard.resolve_in(Path("x"), area="evil")  # type: ignore[arg]


def test_open_readonly_external(tmp_path: Path) -> None:
    """正式区只读装载：白名单根内存在+是文件→返回解析路径；缺失/目录→拒。"""
    root = _make_root(tmp_path)
    external = tmp_path / "formal"
    external.mkdir()
    guard = PathGuard(root, external_roots=(external,))
    target = external / "formal.json"
    target.write_text("{}", encoding="utf-8")
    resolved = guard.open_readonly_external(target)
    assert resolved.is_file()
    assert resolved.name == "formal.json"
    with pytest.raises(PathGuardError):
        guard.open_readonly_external(external / "missing.json")
    with pytest.raises(PathGuardError):
        guard.open_readonly_external(external)  # 目录非文件


def test_open_readonly_external_whitelist(tmp_path: Path) -> None:
    """门一 FIX-2：外部根白名单——根内放行/根外现存文件拒/缺省全拒。"""
    root = _make_root(tmp_path)
    zone_a = tmp_path / "zone-a"
    zone_b = tmp_path / "nested" / "zone-b"
    (zone_a).mkdir()
    zone_b.mkdir(parents=True)
    (zone_a / "a.json").write_text("{}", encoding="utf-8")
    (zone_b / "b.json").write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    guard = PathGuard(root, external_roots=(zone_a, zone_b))
    # 根内（含嵌套根）放行
    assert guard.open_readonly_external(zone_a / "a.json").is_file()
    assert guard.open_readonly_external(zone_b / "b.json").is_file()
    # 根外现存文件：读行为本身即拒（FAIL-CLOSED——不再只校验存在性）
    with pytest.raises(PathGuardError, match="白名单"):
        guard.open_readonly_external(outside)
    # 兄弟前缀（zone-a-evil 字符串前缀）不误放行
    evil = tmp_path / "zone-a-evil"
    evil.mkdir()
    (evil / "x.json").write_text("{}", encoding="utf-8")
    with pytest.raises(PathGuardError):
        guard.open_readonly_external(evil / "x.json")


def test_open_readonly_external_fail_closed_without_roots(tmp_path: Path) -> None:
    """门一 FIX-2：缺省 external_roots=() → 任何外部路径全拒（fail-closed）。"""
    guard = PathGuard(_make_root(tmp_path))
    target = tmp_path / "anywhere.json"
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(PathGuardError, match="白名单"):
        guard.open_readonly_external(target)


def test_open_readonly_external_case_variant_root(tmp_path: Path) -> None:
    """门一 FIX-2：Windows 大小写归一——异 case 根形态仍识别为白名单根。"""
    root = _make_root(tmp_path)
    external = tmp_path / "Formal"
    external.mkdir()
    target = external / "f.json"
    target.write_text("{}", encoding="utf-8")
    variant = Path(str(external).replace(external.drive, external.drive.lower(), 1))
    guard = PathGuard(root, external_roots=(variant,))
    assert guard.open_readonly_external(target).is_file()
