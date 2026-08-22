# mine_water_vxinglvchi —— V型滤池（矿井水线，M3）

滤池深度净化，保障回用/排放 III 类目标。

- 输入：上游端口量（gaomidu 高密沉淀）
- 输出：下游端口量（ziwai 紫外消毒）
- 旧系统对应：mod `kw_vxinglvchi`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（交付期冻结）：滤速、分格、反冲洗
- 物理不变性（交付期进 tests/properties.py）：滤速≤强制滤速限值

本包为结构预留骨架（M0.5）：公式与参数依据随 M3 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
