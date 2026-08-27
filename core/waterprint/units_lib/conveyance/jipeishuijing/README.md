# conveyance_jipeishuijing —— 集配水井（集配水线，M3c 已实装）

集水/配水合一构筑物：汇流调蓄 + 向并联处理系列分 N 路——汇流集水
容积法 + 停留校核 + 均匀分流不均匀余量（jishuijing 容积主线 +
peishuijing 分流主线的单节点合并形态）。

- 输入：上游端口量（各线来水——多股经图入边汇流，propagate 合并面
  承载）；参数 t_well/h_well/n（见 manifest.py 声明）
- 输出：下游端口量（**动态多口 out_1~out_n**——表内冻结口径：manifest
  ports 声明单 OUT 口 "out"，compute 按参数 n 产多键；每口
  q_avg_daily=入流/n、kz 透传、水质逐指标恒等透传——分流守恒+穿流）；
  dims=表结果全量（JP-F1~F9）
- 旧系统对应：mod `jipeishuijing`（交叉对照，非依据）
- golden 绑定：docs/norms/conveyance_jipeishuijing.md（2026-08-27 起草，
  待追认）+ data/coefficients 0.7.0（factor.jipeishuijing.* 12 键——
  removal 零键，穿流单元）
- 公式组（已冻结）：JP-F1~F9（汇流容积/面积/井径/实际面积/停留校核/
  分流/不均匀余量/总深/概算）
- 物理不变性：流量守恒（分流守恒 Σ口=入流——golden 断言+D3 探针锚）、
  容积/停留非负（性质归 contracts 传播面锁定——包内 properties.py
  维持结构预留注记，hebing 先例同型）

本包七固定件全实装（M0.5 骨架 → M3c 交付）；包内结构遵守
AGENTS.md §11 固定七件套，禁自由发挥。
