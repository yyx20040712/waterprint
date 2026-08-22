# municipal_chuchenchi —— 辐流初沉池（市政污水线，M2）

去除可沉悬浮物与部分 SS/BOD，降低生物处理负荷。

- 输入：上游端口量（chenshachi 旋流沉砂池）
- 输出：下游端口量（aao 生物池或 cass 生物池）
- 旧系统对应：mod `chuchenchi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（交付期冻结）：表面负荷、停留时间、SS/BOD 去除率（coefficients 引用）
- 物理不变性（交付期进 tests/properties.py）：去除率∈(0,1)、池容≥0、排泥 DS 与 SS 去除量守恒

本包为结构预留骨架（M0.5）：公式与参数依据随 M2 由领域专家复核冻结；
包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
