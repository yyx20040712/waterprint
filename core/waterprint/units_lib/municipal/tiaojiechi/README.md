# municipal_tiaojiechi —— 调节池（市政污水线，M2）

均化进水水质水量，稳定后续处理负荷。

- 输入：上游端口量（chenshachi 旋流沉砂池）
- 输出：下游端口量（aao 生物池或 cass 生物池）
- 旧系统对应：mod `tiaojiechi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（交付期冻结）：调节容积（进水时序水量平衡）、停留时间
- 物理不变性（交付期进 tests/properties.py）：容积≥时段累积水量、水位非负

本包为结构预留骨架（M0.5）：公式与参数依据随 M2 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
