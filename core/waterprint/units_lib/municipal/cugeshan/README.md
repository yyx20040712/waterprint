# municipal_cugeshan —— 粗格栅（市政污水线；M1 先行示范（已实装）/M2 正式验收）

拦截进水中粗大漂浮物，保护后续水泵与设备。

- 输入：上游端口量（市政输入节点或 wushui_tisheng 提升泵房）
- 输出：下游端口量（xigeshan 细格栅）
- 旧系统对应：mod `cugeshan`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M1a 实装，真源=docs/norms/cugeshan.md 签字表 2026-08-23）：
  CG-F1~F14（单台流量/间隙数/栅槽宽/渠宽/流速校核/阻力/水头损失/总高总长/
  栅渣量/清渣判别/DS/混凝土量）
- 系数通道：factor.screen.\*|factor.cugeshan.\*（data/coefficients 0.1.0，
  经 app._unit_params 投影）；去除率 removal.cugeshan.\*.mod_default
- 物理不变性（归 M1b/M2 批进 tests/properties.py）：过栅流速在设计档位内、
  水头损失≥0、栅渣量≥0

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
