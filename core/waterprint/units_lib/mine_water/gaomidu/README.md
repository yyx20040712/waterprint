# mine_water_gaomidu —— 高密沉淀（矿井水线，M3a3 已实装）

无污泥回流斜管高密沉淀：清水区液面负荷 5~8 m³/(m²·h) 低负荷主控
（保出水浊度，异于市政 10~20 档），斜管轴向流速 ≤5 mm/s 校核，
泥渣浓缩区直接外排（无回流——磁分离段已载泥）。

- 输入：上游端口量（mine_water_cifenli 磁分离）
- 输出：下游端口量（mine_water_vxinglvchi V 型滤池）
- 旧系统对应：mod `kw_gaomidu`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KG-F1~F10，已实装）：单池流量/快混絮凝容积/沉淀面积/
  池宽池长（0.5 m 档）/实际液面负荷/轴向流速/池总高/混凝土概算
- 物理不变性（后续批进 tests/properties.py）：上升流速≤限值、参数域与市政线互不引用
- 数值真源：docs/norms/mine_water_gaomidu.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_gaomidu.* 12 键 +
  removal.mine_gaomidu.{ss,cod}——SS 0.90/COD 0.30 低浓度进水保安段；
  BOD5 全线不建键）
- 语义注记：与市政同名构筑物跨线独立成包（市政=Densadeg 污泥回流型
  含 r_sludge/q_return 键族；本表无回流键族）——键空间经 mine_ 限定
  物理隔离（§14.3）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
