"""单元包模板：脚手架生成目标形态的规范样本（本包不注册为可用单元）。

输入:  无（模板）
输出:  暴露 UNIT_ID、make_unit、manifest 三名（单元包唯一对外白名单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【模板用途】`uv run python -m waterprint.cli new-unit <line> <name>`
#   （cli.py）复制本包为新单元并替换标识；结构一致性不靠文档靠工具。
# 【白名单】真实单元包 __init__ 只导出三名：UNIT_ID（str）、make_unit
#   （Unit 协议工厂）、manifest（UnitManifest 实例）；装配消费面按
#   manifest+make_unit 两名校验；多导出一个名字 = 评审拒绝。
# 【排除】模板包本身带 unit_id="__template__"，discover_units 跳过。
# ══════════════════════════════════════════════════════════════════
