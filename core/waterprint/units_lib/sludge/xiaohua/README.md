# sludge_xiaohua —— 污泥消化池（污泥线，M3b2 已实装）

中温厌氧消化（35 ℃——参数 t_digest_temp 承载，UF-09 未裁口径）：
消化时间容积式 + 挥发分降解 + 产气量三面，消化减量 DS 守恒链
（VS 降解→沼气离开+出泥三量链）显式。

- 输入：上游端口量（sludge_nongsuo 底流，SLUDGE 入流三量）
- 输出：下游端口量（sludge_tuoshui 污泥脱水，SLUDGE 出流三量）
- 旧系统对应：mod `wuni_xiaohua`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例 v_total=2387.93 m³/d=11.5 m 池/
  产气 1257.246066375 m³/d/ds_out=3378.92342625——tuoshui 入流锚）
- 公式组（已实装）：XH-F1~F11——进泥挥发分/总容积/单池/降解/产气/
  VS 负荷校核/消化减量 DS 守恒/出泥三量链联立/池径立方根式/概算
- 物理不变性（后续批进 tests/properties.py）：DS 守恒（进=出+沼气
  带走 VS）、产气量≥0
- 数值真源：docs/norms/sludge_xiaohua.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.xiaohua.* 裸短名 13 键——temp 键
  登记不消费[UF-09 注记]；removal 零键）
- 语义注记：CJJ 131-2009 仅叙述性依据（数值 source 不标，I3 挂账）；
  沼气联动潜力见 ganhua 表注记

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
