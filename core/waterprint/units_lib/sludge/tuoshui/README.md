# sludge_tuoshui —— 污泥脱水间（污泥线，M3b2 已实装）

机械脱水双机档（带式压滤主线/离心脱水副档）：PAM 投加 + 泥饼含水率
75~80% + 固体回收率 DS 守恒链（泥饼/滤液分流闭合显式——旧式未计
回收率系口径缺陷本批修正）。

- 输入：上游端口量（sludge_xiaohua 消化出流主线或 sludge_nongsuo
  浓缩底流直连，SLUDGE 入流三量）
- 输出：泥饼 SLUDGE 出流三量（sludge_ganhua 干化主线或外运）；
  filtrate 滤液回流口（recycle 声明先行——Q1 未裁默认关）
- 旧系统对应：mod `wuni_tuoshui`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例带式 1 用 1 备/ds_cake=
  3209.9772549375/q_cake=14.5908057043——ganhua 入流锚）
- 公式组（已实装）：TU-F1~F8——PAM 日投加/进泥时流量/台数整台
  取整+备用/固体回收 DS 守恒/泥饼三量链/滤液分流/守恒闭合
- 物理不变性（后续批进 tests/properties.py）：DS 守恒（泥饼+滤液）、
  泥饼含水率∈档位
- 数值真源：docs/norms/sludge_tuoshui.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.tuoshui.* 裸短名 8 键；removal
  零键——滤液带出 DS 走泥量链）
- 语义注记：车间设备单元不建 wall_thickness_coef（bashi_jiliangcao
  先例口径）；CJJ 131-2009 已纳出处白名单（I3 改标 2026-08-28 九裁②）
  ——本包 4 键 source 规程级标注

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
