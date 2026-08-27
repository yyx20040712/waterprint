# mine_water_ziwai —— 紫外消毒（矿井水线，M3a3 已实装）

灯管布置实算剂量：辐照强度 I=P·N_layer·η_geo·T_eff·k_aging·k_foul/(10A)
→ 单排剂量 → 排数 ceil 满足设计剂量——含结垢系数 f_fouling 矿井水
特征键（灯套管矿物垢衰减，市政面无此键）。

- 输入：上游端口量（mine_water_vxinglvchi V 型滤池）
- 输出：下游端口量（回用/外排——全厂末段）
- 旧系统对应：mod `kw_ziwai`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KZ-F1~F11，已实装）：单渠流量/断面积/渠内流速/穿透率
  （t254 百分数口径 (t254/100)**n_t）/辐照强度/单排剂量/排数（ceil）/
  实算剂量/接触时间/渠道水损（max(ξv²/2g, 构造下限)）/渠总高
- 物理不变性（后续批进 tests/properties.py）：剂量≥设计最小值
- 数值真源：docs/norms/mine_water_ziwai.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_ziwai.* 11 键 +
  removal.mine_ziwai.{ss,cod} 显式 0.0 穿流——物理消毒无去除；BOD5
  全线不建键）
- 语义注记：与市政同名构筑物跨线独立成包（市政=单灯处理量概算锚
  路线含 q_per_lamp/粪大肠键族；本表灯管布置实算、T254 60~70 高档、
  f_fouling 结垢特征键）——键空间经 mine_ 限定物理隔离（§14.3）；
  渠内公式水损与 elevation_loss 经验键双轨（公式值走校核面/经验值
  走高程链——表追认点 14）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
