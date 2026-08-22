# municipal_chenshachi —— 旋流沉砂池（市政污水线，M2）

利用旋流分离去除砂粒，减轻设备磨损与管道淤积。

- 输入：上游端口量（xigeshan 细格栅）
- 输出：下游端口量（chuchenchi 初沉池或 tiaojiechi 调节池（按工艺配置））
- 旧系统对应：mod `chenshachi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（交付期冻结）：表面负荷/停留时间、沉砂量
- 物理不变性（交付期进 tests/properties.py）：停留时间>0、沉砂量≥0（与矿井水平流沉砂各自独立成包）

本包为结构预留骨架（M0.5）：公式与参数依据随 M2 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
