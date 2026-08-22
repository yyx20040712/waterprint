# mine_water_ningjiao —— 混凝反应（矿井水线，M3）

药剂混合与絮凝反应，为固液分离创造条件。

- 输入：上游端口量（chenshachi 平流沉砂池）
- 输出：下游端口量（cifenli 磁分离或 gaomidu 高密沉淀）
- 旧系统对应：mod `kw_ningjiao`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（交付期冻结）：GT 值、搅拌分级功率、药剂投加量
- 物理不变性（交付期进 tests/properties.py）：GT 值在设计带内、药剂量≥0

本包为结构预留骨架（M0.5）：公式与参数依据随 M3 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
