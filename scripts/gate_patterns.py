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
from dataclasses import dataclass

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
# AUDIT-#20（b30，用户裁决 D7）：agent/ 全量纳管（tests/skills 一并在扫，
# .venv 由 EXCLUDED_DIR_NAMES 排除）——纳管前 agent 面为三查盲区。
SCAN_DIRS: tuple[str, ...] = (
    "core/waterprint",
    "core/tests",
    "server",
    "webapp/src",
    "agent",
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

# ══════════════════════════════════════════════════════════════════
# 宽族 except 精确豁免登记（AUDIT-#20，b30 2026-11-18，用户裁决 D7：
# agent 全量纳管 + 三处精确豁免——登记不窄化兜底本体，agent 源零改动）。
# 键 = 文件路径（仓库相对 posix）+ 函数限定名（check_grep_gates 按 AST
# 定位违规行所在函数，嵌套取最内层链；模块级=“<module>”）+ 异常族
# （"Exception"=捕获 Exception 基类形态 / "bare"=except 后直接冒号形态）；
# 行号不作键——豁免不随代码行漂移失效。
# reason 非空强制（check_grep_gates 启动校验——空理由=无审查依据），
# 内容转录自兜底注释在案的设计意图。
# 失效条件（任一触发该处立即转红=审查信号）：函数改名（键漂移）、
# 异常族变化（收窄/换族）、兜底删除（登记未被消费=腐烂报警）；
# 审查后重登记或收窄兜底，不得改为整文件/整目录排除形态。
# 第四处宽族不在表内必红。
# ══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class WaiverEntry:
    """单条宽族 except 豁免（四字段缺一即门禁红）。"""

    file: str
    symbol: str
    family: str
    reason: str


WIDE_EXCEPT_WAIVERS: tuple[WaiverEntry, ...] = (
    WaiverEntry(
        file="agent/waterprint_agent/context.py",
        symbol="run_tool",
        family="Exception",
        reason=(
            "run_tool 工具运行兜底面：run 抛任何异常一律转 {error, hint} "
            "错误 dict 返回 MCP 客户端（禁 raise 裸异常穿透——AGENTS §3 "
            "工具条款；session_log 同 span 记账失败）"
        ),
    ),
    WaiverEntry(
        file="agent/waterprint_agent/tools/projects.py",
        symbol="_update_params_impl",
        family="Exception",
        reason=(
            "undo 快照守护（门一 FIX-3/C1）：save_project 失败（锁冲突/"
            "深度闸族）时半写 undo 快照 best-effort 清理后原样重抛，"
            "交 run_tool 兜底转错误 dict"
        ),
    ),
    WaiverEntry(
        file="agent/waterprint_agent/tools/solution.py",
        symbol="_run_joint_enumeration_impl",
        family="Exception",
        reason=(
            "联合枚举护栏族统一收敛（R3）：core 正门 TooLarge/Invalid 等"
            "护栏异常不穿透 MCP 面，统一转 rejected dict（调用方按 "
            "status=rejected 处理）"
        ),
    ),
)
