"""量纲与规范单位定义、pint 边界包装（全库唯一接触 pint 的文件）。

输入:  外部边界的带单位数值与单位字符串（UI/API/项目文件/Excel 读取）
输出:  规范单位裸值（float）、Quantity 包装、量纲校验结果（ADR-002 §12.1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；实现必须逐条满足，镜像测试 tests/contracts/test_quantity.py）
#
# 【公开接口】
#   class DimKey(str, Enum)      量类枚举：FLOW/CONCENTRATION/LENGTH/AREA/
#                                VOLUME/MASS/TIME/VELOCITY/POWER/DIMENSIONLESS…
#   class Quantity               (magnitude: float, unit: str) 不可变值对象
#   class InvalidUnitError(Exception)  单位非法/量纲不匹配（领域异常，禁止静默）
#   CANONICAL_UNITS: dict[DimKey, str]  量类 → 规范单位，唯一真源
#   parse(value, unit, expect: DimKey) -> float
#       边界入口：接受外部单位，换算为规范单位裸值并校验量纲
#   attach(value: float, dim: DimKey) -> Quantity
#       出口：规范单位裸值 → 带单位 Quantity（供显示/序列化层）
#
# 【行为规格】
#   R1 规范单位表初版必须至少包含（重写计划 §12.1 明示三项）：
#      FLOW→"m3/s"，CONCENTRATION→"mg/L"，LENGTH→"m"；
#      其余条目实现时经评审补充，且必须与 registry/dimensions.py 一致。
#   R2 换算必须经 pint 完成，禁止手写换算系数；1 m3/d == 1/86400 m3/s、
#      1 mg/L == 1 g/m3 等换算正确性由性质测试覆盖（往返/结合律）。
#   R3 非法单位字符串、量纲不匹配（expect=FLOW 却给 "mg/L"）→ InvalidUnitError，
#      禁止默认单位、禁止静默 None。
#   R4 落盘序列化一律"规范单位数值 + 显式 unit 字段"，读取方零换算（§12.1 R15）。
#
# 【禁止】
#   - 出现任何手写换算系数（0.001、86400 等魔法数只能出现在测试的期望值里）
#   - pint 泄漏到返回值：内核热路径拿到的是 float 裸值
#
# 【测试要求】tests/contracts/test_quantity.py + properties_quantity.py
#   （换算正确性、非法拒绝、往返恒等；性质：attach(parse(x)) == x）
#
# 【参照】重写计划 §2/§12.1；ADR-002；病灶 Q_design/Q_avg 双轨、P_sludge 标 kW
# ══════════════════════════════════════════════════════════════════
