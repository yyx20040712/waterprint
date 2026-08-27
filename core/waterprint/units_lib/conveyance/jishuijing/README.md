# conveyance_jishuijing —— 集水井（集配水线，M3c 已实装）

汇流集水构筑物：汇集各线来水、稳定下游取水条件——汇流集水容积法
+ 停留校核 + 圆形井构造（无泵工况，泵衔接归泵族单元面）。

- 输入：上游端口量（各线来水——多股经图入边汇流，propagate 合并面
  承载）；参数 t_well/h_well（见 manifest.py 声明）
- 输出：下游端口量（单口 WATER 穿流透传——q_avg_daily/kz 双量恒等，
  水质逐指标恒等）；dims=表结果全量（JS-F1~F7）
- 旧系统对应：mod `jishuijing`（交叉对照，非依据）
- golden 绑定：docs/norms/conveyance_jishuijing.md（2026-08-27 起草，
  待追认）+ data/coefficients 0.7.0（factor.jishuijing.* 9 键——
  removal 零键，穿流单元）
- 公式组（已冻结）：JS-F1~F7（汇流容积/面积/井径/实际面积/停留校核/
  总深/概算）
- 物理不变性：容积≥0、停留非负（性质归 contracts 传播面锁定——包内
  properties.py 维持结构预留注记，hebing 先例同型）

本包七固定件全实装（M0.5 骨架 → M3c 交付）；包内结构遵守
AGENTS.md §11 固定七件套，禁自由发挥。
