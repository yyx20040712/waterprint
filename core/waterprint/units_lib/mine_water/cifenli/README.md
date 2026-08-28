# mine_water_cifenli —— 磁分离（矿井水线，M3a3 已实装）

磁磁盘分离机：磁盘表面负荷 20~40 m³/(m²·h) 主控定盘面积，盘缘线速度
与磁种回收循环衡算（磁加载混凝路线的核心分离单元）。

- 输入：上游端口量（mine_water_ningjiao 混凝反应池）
- 输出：下游端口量（mine_water_gaomidu 高密沉淀）
- 产股口（GOLDEN4a D3，2026-08-28）：sludge_out SLUDGE 无条件产股——ds=MS-F1
  w_ss×1000 干基（26827.632 直对 MSLUDGE2 锚，hebing ds_primary 注入位
  同源）+q_wet=KS-F7 ρ=1100 直算口径+moisture 0.92 系数键
- 旧系统对应：mod `kw_cifenli`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KS-F1~F8，已实装）：单台流量/单盘双面有效面积/需盘面面积/
  盘片数（整台 ceil）/盘缘线速度/截留泥量/磁泥湿量/磁种净耗
- 物理不变性（后续批进 tests/properties.py）：磁回收率∈(0,1]、出水 SS 随投加量单调改善
- 数值真源：docs/norms/mine_water_cifenli.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_cifenli.* 14 键 +
  removal.mine_cifenli.{ss,cod}——SS 0.90 磁絮体磁盘截留/COD 0.60
  颗粒态煤粉随絮体带出；BOD5 全线不建键）
- 语义注记：磁种投加量 m_seed 经参数面衔接上游（ningjiao KN-F13 口径，
  上游 dims 不跨单元传递）；流道停留/流速两键为设备选型校核键（流道
  几何归厂商样本），本包不落几何公式

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
