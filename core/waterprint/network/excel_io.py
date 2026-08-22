"""管网 Excel 读写：管段模型进、设计结果 sheet 出（M3 Excel 闭环）。

输入:  .xlsx 管网表（模板驱动：data/templates 管网模板）
输出:  PipeSegment 序列（读） / 带结果 sheet 的 .xlsx（写）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/network/test_excel_io.py）
#
# 【公开接口】
#   read_network_excel(path: Path) -> tuple[PipeSegment, ...]
#   write_result_sheet(path: Path, design: NetworkDesign) -> Path
#       原文件追加/更新结果 sheet（幂等：重写同 sheet 不重复）
#
# 【行为规格】
#   R1 模板驱动（§2 Excel 行）：读取按 data/templates 管网模板的
#      列位映射（模板版本号写入文件）；列位变更走模板版本化，
#      代码按模板描述取列，禁止硬编码列字母。
#   R2 安全面（§18 Excel zip 炸弹行）：大小上限（Settings 配置）、
#      行数上限、只读模式解析（openpyxl read_only）；超限抛领域异常。
#   R3 校验前置：必填列缺失/类型错误/标高倒置 → 带行号的错误清单
#      （一次性全报，禁止逐行崩溃）；读入结果进 solver 前已合法。
#   R4 输出无公式（§11 R12）：结果 sheet 只写数值与文本（计算全部
#      在 Python 完成），Excel 打开仅作展示。
#   R5 编码：openpyxl 读写显式 UTF-8 语义；文件路径限制在配置
#      工作目录内（§18 路径安全，同 dxf_writer 规则）。
#
# 【测试要求】模板往返（读→写→重读一致）、错误清单带行号、
#   行数/大小上限触发、幂等重写。
#
# 【参照】重写计划 §2 Excel 行/§11 R12/§18；data/templates/README.md
# ══════════════════════════════════════════════════════════════════
