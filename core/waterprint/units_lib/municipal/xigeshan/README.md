# municipal_xigeshan —— 细格栅（市政污水线；M1 先行示范（已实装）/M2 正式验收）

拦截较小悬浮物，保护沉砂池与生物处理系统。

- 输入：上游端口量（cugeshan 粗格栅）
- 输出：下游端口量（chenshachi 旋流沉砂池）
- 旧系统对应：mod `xigeshan`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M1a 实装，真源=docs/norms/xigeshan.md 签字表 2026-08-23）：
  XG-F1~XG-F14（公式体系同粗格栅共用 _BarScreenBase，差异仅常数——
  W₁=factor.xigeshan.w1_slag；栅隙流速/过栅水头损失/栅渣量/DS/混凝土量）
- 系数通道：factor.screen.\*（格栅共用）|factor.xigeshan.\*（data/
  coefficients 0.1.0，经 app._unit_params 投影）；去除率
  removal.xigeshan.\*.mod_default
- 物理不变性（归 M1b/M2 批进 tests/properties.py）：过栅流速在设计档位内、
  水头损失≥0、栅渣量≥0

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
