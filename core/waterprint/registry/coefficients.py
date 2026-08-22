"""去除率/经验系数库加载：数据驱动，随规范版本演进（清单只存引用键）。

输入:  data/coefficients/ YAML 数据包（带版本与出处）
输出:  Coefficients 查询对象 + data_version（可复算三元组成员）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/registry/test_coefficients.py）
#
# 【公开接口】
#   class Coefficients(不可变)：
#       data_version: str          数据包版本（三元组成员，§16 A8）
#       get(key: str) -> CoefficientValue
#       keys(prefix: str) -> tuple[str, ...]   按前缀列举（单元/指标分组）
#   load_coefficients(path) -> Coefficients
#       加载正门：YAML → 严格校验 → 不可变对象
#   class CoefficientValue：value、unit、source（出处）、note
#
# 【行为规格】
#   R1 数据驱动：去除率、经验系数（如各单元 BOD5/COD/SS/NH3-N/TN/TP
#      去除率、曝气修正系数、污泥产率等）全部来自数据包；代码内出现
#      具体系数数值 = 评审拒绝（数值只允许出现在测试期望与数据包）。
#   R2 每条系数必须带 source；数据包整体带 data_version——数据更新
#      = 版本号变化 = 全部旧结果过期（可复算三元组）。
#   R3 manifest.removal_refs 引用的键必须可在包内解析，加载时静态校验，
#      失联键 = 启动失败。
#   R4 数据包只读：内核不写 data/（写入是数据维护流程，走版本化发布）。
#
# 【测试要求】加载往返、失联引用键拒绝、data_version 传播、
#   无 source 条目拒绝。
#
# 【参照】重写计划 §5/§16 A8；数据规格 data/coefficients/README.md
# ══════════════════════════════════════════════════════════════════
