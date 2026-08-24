# ADR-002：单位制三层策略（pint 边界 / 裸数组内核 / 注册表元数据）

- 状态：**已接受**（计划 §2/§12.1；M1 落地）
- 背景：pint 无法作用于 numpy 结构化数组字段（§11 R1）；旧系统单位双轨
  是第一大 bug 源（Q_design/Q_avg 双轨、P_sludge 标 kW）。
- 决策：
  1. 边界层：外部输入经 pint 换算到规范单位 + 量纲校验，非法即拒绝；
  2. 内核层：热路径使用规范单位裸数组（流量 m3/s、浓度 mg/L、几何 m），
     代码不出现换算逻辑；
  3. 元数据层：dtype 注册表（dimensions）为字段声明单位；公式注册表
     登记量纲签名，**加载时静态校验，不匹配 = 启动失败**；
  4. 落盘一律"规范单位数值 + 显式 unit 字段"，读取方零换算（R15）；
  5. `contracts/quantity.py` 是全库唯一允许 import pint 的文件
     （import-linter 强制。forbidden 契约按**直查口径**
     （allow_indirect_imports=true，T3-G1 追认、T4 D3 记档）——上层
     引用 quantity 重导出的类型符号（DimKey/CANONICAL_UNITS）合法，
     任何文件直接 import pint 仍禁；pint 对象不出 quantity 边界，
     R2 既有语义不变）。
- 后果：换算只发生在边界一处；手写换算系数 = 评审拒绝。
- 细化归属：M1 quantity/dimensions/formulas 实现。
