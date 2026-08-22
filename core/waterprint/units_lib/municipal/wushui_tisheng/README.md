# municipal_wushui_tisheng —— 污水提升泵房（市政污水线，M2）

进水提升，建立全厂自流水力高程起点。

- 输入：上游端口量（市政输入节点）
- 输出：下游端口量（cugeshan 粗格栅）
- 旧系统对应：mod `wushui_tisheng（社区）`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（交付期冻结）：扬程（与 elevation/pumps 联动）、泵组合数与备用率
- 物理不变性（交付期进 tests/properties.py）：扬程≥0、备用满足 n+1 规则

本包为结构预留骨架（M0.5）：公式与参数依据随 M2 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
