# mine_water_chenshachi —— 平流沉砂池（矿井水线，M3a2 已实装）

平流式除砂，去除高悬浮物中的砂粒与粗煤粉，保护下游混凝/分离段。

- 输入：上游端口量（mine_water_tiaojiechi 调节池）
- 输出：下游端口量（mine_water_ningjiao 混凝反应池）
- 旧系统对应：mod `kw_chenshachi`（交叉对照，非依据）
- golden 绑定：mine_43836
- 公式组（KC-F1~F10，已实装）：池长/单格断面/池宽/实际流速校核/
  沉砂量/贮砂斗容积/堰负荷/总高/混凝土概算
- 物理不变性（后续批进 tests/properties.py）：水平流速在设计带内
  （与市政旋流沉砂各自独立成包）
- 数值真源：docs/norms/mine_water_chenshachi.md（M3a1 表，待追认）+
  data/coefficients 0.5.0（factor.mine_chenshachi.* 13 键 +
  removal.mine_chenshachi.ss 0.15；COD/BOD5 不建键）
- 物理隔离：与市政同名包（旋流型）零 import 零参数复用——平流型
  主控三带（流速/停留/浅池水深）独立起草，§14.3 可审计面

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
