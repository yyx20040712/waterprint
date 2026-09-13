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
# 中文硬封族（GOV1 2026-09-12 深度审计裁决 A1 修正版）：六词入库时源码
# 零命中（实测 2026-09-12），封堵"新写中文存根"词汇盲区。占位/未就绪/
# 挂起为过载域词（模板占位符/限流槽/loading 态/挂起态流——337 处合法
# 用法），不封；其语义靠 UF 登记+诚实 501+代数不变式测试保障（ADR-013）。
UNFINISHED_MARKERS: tuple[str, ...] = (
    "not" + " implemented",
    "TO" + "DO",
    "FIX" + "ME",
    "未" + "实现",
    "待" + "实现",
    "待" + "实装",
    "暂不" + "实现",
    "留空" + "待",
    "待" + "接入",
)
# 英文 place"holder" 豁免注记（批3 段三 2026-09-13，GOV1 A1 对称裁定；
# 门一 P1 论证勘正同批）：该词为过载域词——合法载体两类实证在案=
# antd placeholder UI 属性（JSX 属性位 place"holder"="…"，等号/引号
# 构成词边界——unitLibrary.tsx 曾以拼接规避）+spec §11 用户签核冻结
# 签名 missingSlotPlaceholders（子串匹配误伤标识符段；词边界正则不
# 命中驼峰标识符[前邻恒词字符]但误伤 JSX 属性位——两形态均不可用，
# 故整词移出特征表）。与中文「占位」同待遇（GOV1 A1 过载域词不封；
# 语义靠 UF 登记+诚实 501+代数不变式测试保障，ADR-013）。**已接受
# 残余风险（显式登记）**：英文 place"holder" 作存根注释的形态（如
# "// place"holder": wire later"）不再拦截——英文存根拦截主力="TO"+
# "DO"/"FIX"+"ME"/"not"+" implemented" 三特征兜底，中文六词硬封不变。

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
