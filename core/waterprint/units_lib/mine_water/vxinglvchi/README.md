# mine_water_vxinglvchi —— V型滤池（矿井水线，M3a3 已实装）

均质滤料低滤速精滤：正常滤速 4~6 m/h（低于市政 7~10 档的精滤口径，
保回用水浊度），强制滤速与反冲耗水率双校核，V 型气水反冲三阶段。

- 输入：上游端口量（mine_water_gaomidu 高密沉淀）
- 输出：下游端口量（mine_water_ziwai 紫外消毒）
- 旧系统对应：mod `kw_vxinglvchi`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KV-F1~F11，已实装）：日处理量（自用水系数）/有效过滤时长/
  总与单格过滤面积/强制滤速/单格尺寸（0.1 m 档）/反冲水量三阶段族/
  反冲耗水率/滤池总高/混凝土概算
- 物理不变性（后续批进 tests/properties.py）：滤速≤强制滤速限值
- 数值真源：docs/norms/mine_water_vxinglvchi.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_vxinglvchi.* 21 键 +
  removal.mine_vxinglvchi.{ss,cod}——SS 0.80 低浊进水档/COD 0.075
  微量去除保守档；BOD5 全线不建键）
- 语义注记：过滤面积按平均日×自用水系数的日处理量口径（异于沉淀类
  最高时口径）；t_bw=三阶段反冲停滤历时合成（t_air+t_sim+t_water）；
  出水 COD 51.8 mg/L 贴 GB 20426-2006 限值 50 上方为键中值链客观
  呈现（表内注记，追认点 12）；与市政同名构筑物跨线独立成包（键
  空间经 mine_ 限定物理隔离 §14.3）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
