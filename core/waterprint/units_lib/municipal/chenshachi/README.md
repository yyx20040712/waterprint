# municipal_chenshachi —— 旋流沉砂池（市政污水线；M1 先行示范（已实装）/M2 正式验收）

利用旋流分离去除砂粒，减轻设备磨损与管道淤积。

- 输入：上游端口量（xigeshan 细格栅）
- 输出：下游端口量（chuchenchi 初沉池或 tiaojiechi 调节池（按工艺配置））
- 旧系统对应：mod `chenshachi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M1a 实装，真源=docs/norms/chenshachi.md 签字表 2026-08-23）：
  CS-F1~F18（单池流量/池径/有效水深/径深比/停留时间/沉砂量/砂斗组/总高/
  进出水渠/沉砂污泥口/混凝土量；式 (3-21)~(3-29)/(4-26)~(4-29) 引
  中期报告 §3.3——毕业设计内部资料，待核对映射条文，挂账保留）
- 系数通道：factor.chenshachi.\*（data/coefficients 0.1.0，经 app._unit_params
  投影）；去除率 removal.chenshachi.\*.mod_default
- 矛盾 3 挂账：mod.json t min=30 与停留时间校核带 25~60 s 不一致——待领域专家裁定
- 物理不变性（归 M1b/M2 批进 tests/properties.py）：停留时间>0、沉砂量≥0
  （与矿井水平流沉砂各自独立成包）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
