# sludge_bengzhan —— 污泥泵站（污泥线，M3b2 已实装）

集泥井（调节容积）+ 污泥泵组（工作+备用）+ 出泥压力管——照市政
wushui_tisheng 泵族先例形态（扬程三分量+集泥井+启停校核，比阻表改
λ 式[污泥管细管档]+污泥粘度修正 1.2）。

- 输入：上游端口量（sludge_shusong 污泥输送，SLUDGE 入流三量）
- 输出：下游端口量（sludge_nongsuo 污泥浓缩，SLUDGE 出流三量穿流）
- 旧系统对应：mod `wuni_bengzhan`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例 2 用 1 备/单泵 8.5278 m³/h/
  h_pump=16.396 m/DN50 出泥管 v_act=1.206 m/s 带内/启停 1.5 次/h 合格）
- 公式组（已实装）：BZ-F1~F18——泵组锚值取整+均分反算、扬程三分量
  （λ 沿程+ζ 局部×污泥修正+自由水头）、集泥井容积/面积/启停/概算、
  DS/含水率穿流
- 物理不变性（后续批进 tests/properties.py）：扬程≥0、备用满足规范
- 数值真源：docs/norms/sludge_bengzhan.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.bengzhan.* 裸短名 17 键；removal 零键）
- 语义注记：elevation_loss=站内过流水损经验值（提升能量由 h_pump 公式
  承载——wushui_tisheng 追认点 6 同款语义分工）；CJJ 131-2009 已纳
  出处白名单（I3 改标 2026-08-28 九裁②）——本包 2 键 source 规程级标注

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
