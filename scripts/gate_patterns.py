"""门禁特征串集中定义（拼接构造，避免脚本自身被扫描命中）。

输入:  无（常量定义）
输出:  占位符特征串 / 裸异常正则 / 乱码特征串（各检查脚本与测试共用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：见 docs/file-contracts.md §4。
# 英文特征串按单词拼接，防止本文件在扫描时自我命中（假阳性）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re

# 占位与未完成标记（AGENTS.md §3；命中数必须为 0）
# 命名避开特征词本身，防扫描自匹配
UNFINISHED_MARKERS: tuple[str, ...] = (
    "not" + " implemented",
    "place" + "holder",
    "TO" + "DO",
    "FIX" + "ME",
)

# 裸异常/过宽捕获（可预期错误必须用领域异常，AGENTS.md §3）
BARE_EXCEPT_RE = re.compile(r"except\s+Exception|except\s*:")

# GBK 双重编码乱码特征（教训 C4；命中数必须为 0，含 .md）
MOJIBAKE_TOKENS: tuple[str, ...] = (
    "锟斤" + "拷",
    "娌℃" + "湁",
    "鎵撳" + "紑",
    "鏄" + "痑",
    "涓" + "枃涔",
)

# 扫描的源码扩展（占位符/裸异常）；乱码额外覆盖 .md/.json/.yaml/.toml
SOURCE_SUFFIXES: tuple[str, ...] = (".py", ".ts", ".tsx")
DOC_SUFFIXES: tuple[str, ...] = (".md", ".json", ".yaml", ".yml", ".toml", ".txt")

# 扫描范围（相对仓库根；运行时产物与生成物排除）
SCAN_DIRS: tuple[str, ...] = (
    "core/waterprint",
    "core/tests",
    "server",
    "webapp/src",
    "scripts",
)

# 目录排除名（任何层级）
EXCLUDED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        "__snapshots__",
        "dist",
        "build",
        "generated",
        ".mimosa",
    }
)
