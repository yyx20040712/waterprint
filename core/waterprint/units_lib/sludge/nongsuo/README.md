# sludge_nongsuo —— 污泥浓缩池（污泥线，M3b2 已实装）

重力浓缩圆形池：固体通量/浓缩时间双主线面积取大 + 截留 DS 守恒链
（底流/上清液分流显式）。

- 输入：上游端口量（sludge_bengzhan 污泥泵站，SLUDGE 入流三量）
- 输出：底流 SLUDGE 出流三量（sludge_xiaohua 主线或 sludge_tuoshui 直连）；
  sup 上清液回流口（recycle 声明先行——Q1 未裁默认关，business-logic §6）
- 旧系统对应：mod `wuni_nongsuo`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例固体负荷主控 a_req=106.1303 m²/
  d=8.5 m/ds_out=4775.8635/q_thick=119.3965875——xiaohua 入流锚）
- 公式组（已实装）：NS-F1~F12——双主线面积 max/单池面积/池径
  （0.5 m 档）/实际负荷校核/截留 DS 守恒/底流三量链/上清液分流/
  总高/概算
- 物理不变性（后续批进 tests/properties.py）：DS 守恒（浓缩污泥+
  上清液）、含水率单调下降
- 数值真源：docs/norms/sludge_nongsuo.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.nongsuo.* 裸短名 12 键；removal 零键
  ——上清液带出 DS 走泥量链不走水质去除键）
- 语义注记：CJJ 131-2009 已纳出处白名单（I3 改标 2026-08-28 九裁②）
  ——本包 6 键 source 规程级标注

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
