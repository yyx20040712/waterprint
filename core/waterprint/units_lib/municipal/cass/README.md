# municipal_cass —— CASS 生物池（市政污水线；M2c 已实装/M2 正式验收）

周期循环活性污泥法（CASS：4h 周期档主线 + 预反应生物选择区；负荷法
主容积[AAO 同族口径] + 滗水容积 ≤ 池深 1/3 双控池面积 + 滗水器选型 +
需氧量/剩余污泥 AAO 同族公式口径），单池周期内完成反应与泥水分离。

- 输入：上游端口量（chuchenchi 初沉池或 tiaojiechi 调节池；入流=初沉
  出流，与 aao 表同入流——两工艺互为备选对比记档见起草表衔接式）
- 输出：下游端口量（erchunchi 辐流二沉池）
- 旧系统对应：mod `cass`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2c 已实装，真源=docs/norms/cass.md 起草表 2026-08-26
  数据策略 v2，数值面待追认）：CA-F1~CA-F27（周期循环主线：周期数/
  单池单周期滗水容积/负荷法主容积+选择区/滗水 1/3 池深双控单池面积/
  时段和=周期不变性[域拒]/滗水器整台 ceil/剩余污泥与泥龄/需氧量三式/
  实际负荷校核/池体几何 0.5 m 档/混凝土量）；池数 n_pool grid=[2,3,4,5,6]、
  周期 t_cycle grid=[4,6,8]（Ruling ④：档位下限经 grid 声明，compute
  只保 n>0）
- 系数通道：factor.cass.\*（data/coefficients 0.4.0，经 app._unit_params
  投影；需氧量/剩余污泥系数与 aao 同族同值）；去除率 removal.cass.\*
  .mod_default AAO 同族档（0.90/0.85/0.90——出水质 ×(1−r) 形态）
- 物理不变性（business-logic §8 行 8 联动，包内测试断言）：时段和=
  周期（破坏配比域拒）、滗水容积 ≤ 池容（h_draw ≤ h2/3 双控构造）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
