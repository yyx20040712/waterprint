# mine_water_input —— 矿井水输入（矿井水线，M3a2 已实装）

矿井水线起点：全厂流量口径（平均日/最高时）与进水水质（GB/T 19223-2015
含悬浮物类核定）的唯一注入点，附进水高程基准与管口衔接。

- 输入：零入边（executor 源节点——流量与水质经参数面注入）
- 输出：下游端口量（mine_water_tiaojiechi 调节池）
- 旧系统对应：mod `kw_input`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KI-F1~F7，已实装）：设计流量/平均时流量/进水管流速/高程链/超高
- 物理不变性（后续批进 tests/properties.py）：流量>0、各浓度非负
- 数值真源：docs/norms/mine_water_input.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_input.*；去除率零键）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
