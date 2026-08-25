# municipal_aao —— AAO 生物池（市政污水线；M2a2 已实装/M2 正式验收）

厌氧-缺氧-好氧工艺同步脱氮除磷与有机物去除。

- 输入：上游端口量（chuchenchi 初沉池或 tiaojiechi 调节池）
- 输出：下游端口量（erchunchi 辐流二沉池）
- 旧系统对应：mod `aao`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2a2 已实装，真源=docs/norms/aao.md 起草表 2026-08-25 数据
  策略 v2，数值面待追认；路线=ADR-008 ①负荷法主线+泥龄校核带）：
  AO-F1~F14（污泥负荷与分区容积[厌氧/缺氧/好氧]、需氧量、内回流与
  外回流比、剩余污泥量、污泥龄校核）；追认口径按表冻结：好氧泥龄判断
  口径（AO-F8，全池口径备考注记）、回流泵双口径（AO-F13 外回流最高时
  /AO-F14 内回流平均时，相差 Kz 倍）
- 系数通道：factor.aao.\*（data/coefficients 0.2.0，经 app._unit_params
  投影）；去除率 removal.aao.\*.mod_default；TN_eff=15 mg/L 为出水标准
  数据条目（manifest 参数 tn_eff，非本表系数）
- 物理不变性（归后续批进 tests/properties.py）：分区容积和=总容积、
  需氧量≥0、回流比>0、剩余污泥≥0

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
