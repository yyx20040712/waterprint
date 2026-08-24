"""设计态内容哈希：design 态 → sha256（可复算三元组成员、dirty 判定核心）。

输入:  DesignState（design 态全部参与哈希的内容）
输出:  sha256 十六进制字符串（64 位，稳定）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D5 裁决 2026-08-25；镜像测试 tests/project/test_content_hash.py）
#
# 【公开接口】
#   design_hash(design: DesignState) -> str
#       = sha256(io.dumps_design(design) 的 UTF-8 字节).hexdigest()
#
# 【行为规格】
#   R1 只覆盖 design 态：view 态（布局/相机/窗口/时间戳）任何变化
#      不得改变哈希（R10 病灶根除，测试显式构造 view 变更断言；
#      签名只收 DesignState——view 天然不在参与面）。
#   R2 哈希稳定性：先经 io.dumps_design 的确定性序列化（键排序/
#      round(x,10) 定点浮点 + format_version 头）再 sha256——对象
#      构造顺序无关；同设计两次哈希相同。头部 format_version 保证
#      未来版本迁移后哈希自然失效（防旧哈希冒充新语义，T7a D5）。
#   R3 参与项完备：DesignState 七字段全量（nodes/edges/
#      constraint_choices/checked_units/assumption_overrides/
#      influent/standard_binding——model_dump 全量；"单元版本"经
#      nodes 值结构携带，后续收紧 GR-21——T7a 注记修正）。清单
#      变更必须同步本规格与测试。
#   R4 哈希是重算与 stale 判定的唯一依据：编辑 → 新 hash → 运行中
#      任务结果落地即标 stale（§17.1）；缓存键含 design_hash（§17.2）。
#
# 【T7a 冻结注记】
#   - project 包内 content_hash→io import 合法（包内先例 manifest→
#     manifest_validation，§1b 零新边）；不 import registry/L3。
#   - 数值纪律：本文件零数值面（哈希与编码无字面量）。
#
# 【测试要求】view 变更不变、design 各参与项逐项变更必变、
#   序列化顺序无关、与 io 联合（save→load→hash 相同）。
#
# 【参照】重写计划 §12.3/§17.1；ADR-004；简报 T7a D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from hashlib import sha256

from waterprint.contracts.project_schema import DesignState
from waterprint.project.io import dumps_design


def design_hash(design: DesignState) -> str:
    """design 态内容哈希：确定性序列化（含版本头）→ sha256 hex（R1~R3）。"""
    return sha256(dumps_design(design).encode("utf-8")).hexdigest()
