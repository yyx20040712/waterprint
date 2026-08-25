# municipal_wushui_tisheng —— 污水提升泵房（市政污水线；M2c 已实装/M2 正式验收）

集水井 + 潜水排污泵（集水井调节容积法 + 泵扬程三分量主线：静扬程 +
管路损失[舍维列夫比阻估算法] + 自由水头；2 用 1 备选泵[整台 ceil] +
水位启停频率校核），进水提升，建立全厂自流水力高程起点；提升单元
零去除（原水穿流）。

- 输入：上游端口量（市政输入节点，入流=原水六指标链值）
- 输出：下游端口量（cugeshan 粗格栅）
- 旧系统对应：mod `wushui_tisheng（社区）`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2c 已实装，真源=docs/norms/wushui_tisheng.md 起草表
  2026-08-26 数据策略 v2，数值面待追认）：TS-F1~TS-F14（单泵概算锚
  选泵整台 ceil/泵组 2 用 1 备/压力管 DN 0.1 m 档 ceil+比阻档表键命中
  [DN300~DN800 八档，越表拒]/沿程+局部损失/泵扬程三分量[M2b1 追认点
  14 承接——扬程链进 elevation 面归出图批 UF-32 契约]/集水井调节容积/
  启停频率 ≤6 次/h/井体几何与混凝土量）
- 系数通道：factor.wushui_tisheng.\*（data/coefficients 0.4.0，经
  app._unit_params 投影；比阻=舍维列夫旧铸铁/钢管 v≥1.2 m/s 档——
  低流速修正未计归起草表追认点 3）；去除率 removal.wushui_tisheng.\*
  .mod_default 全 0.0（提升单元无处理——出水质=入水质逐键透传不经
  apply，扬程指标经 dims 的 h_pump 承载）
- 物理不变性（归后续批进 tests/properties.py）：扬程 ≥0、备用满足
  n+1 规则、流量守恒（水量不衰减）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
