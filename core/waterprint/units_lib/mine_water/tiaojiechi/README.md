# mine_water_tiaojiechi —— 矿井水调节池（矿井水线，M3a2 已实装）

均化矿井水涌水量波动（井下排水脉动），稳定处理负荷；主线取纯均化
功能（零去除穿流），防沉积搅拌。

- 输入：上游端口量（mine_water_input 矿井水输入）
- 输出：下游端口量（mine_water_chenshachi 平流沉砂池；出水管按平均时均匀输出）
- 旧系统对应：mod `kw_tiaojiechi`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KT-F1~F12，已实装）：调节容积法（停留时间法）主线/单格
  几何/搅拌功率/出水管 DN/总高/混凝土概算
- 物理不变性（后续批进 tests/properties.py）：容积≥时段累积水量
  （与市政调节池各自独立成包）
- 数值真源：docs/norms/mine_water_tiaojiechi.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_tiaojiechi.* 11 键 +
  removal.mine_tiaojiechi.{ss,cod} 显式 0.0 穿流；BOD5 全线不建键）
- 物理隔离：与市政同名包零 import 零参数复用（hrt 8~12/depth 3~5/
  搅拌 8 W/m³ 独立起草——§14.3 可审计面）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
