# mine_water_ningjiao —— 混凝反应（矿井水线，M3a2 已实装）

四分区机械搅拌混凝反应（混合→磁种混合→絮凝→熟化，G 值梯度递减
600/300/80/30 s⁻¹，磁加载型），为下游固液分离创造条件。

- 输入：上游端口量（mine_water_chenshachi 平流沉砂池）
- 输出：下游端口量（mine_water_cifenli 磁分离或 mine_water_gaomidu 高密沉淀）
- 旧系统对应：mod `kw_ningjiao`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KN-F1~F15，已实装）：四分区容积/总停留/G 值法功率（P=μG²V）/
  分区布置/GT 总量校核/PAC·PAM·磁种投加/总高/混凝土概算
- 物理不变性（后续批进 tests/properties.py）：GT 值在设计带内、药剂量≥0
- 数值真源：docs/norms/mine_water_ningjiao.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_ningjiao.* 24 键 +
  removal.mine_ningjiao.{ss,cod} 显式 0.0 穿流；BOD5 全线不建键）
- 语义注记：反应池无固液分离功能，水质零变化穿流（药耗面不改水质面，
  絮体分离在下游 cifenli/gaomidu——两线键挂口径镜像自洽）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
