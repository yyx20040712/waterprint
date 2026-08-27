# conveyance_peishuijing —— 配水井（集配水线，M3c 已实装）

均匀分配构筑物：向并联处理系列分 N 路——均匀分流 + 孔口出流水力
（μ 反解作用水头）+ 配水不均匀系数设计余量 + 井室构造。

- 输入：上游端口量（集水设施或上游处理单元——单股 WATER）；参数
  n/v/v_channel/h_well（见 manifest.py 声明）
- 输出：下游端口量（**动态多口 out_1~out_n**——表内冻结口径：manifest
  ports 声明单 OUT 口 "out"，compute 按参数 n 产多键；每口 q_avg_daily
  =入流/n、kz 透传、水质逐指标恒等透传——分流守恒+穿流）；dims=表
  结果全量（PJ-F1~F12）
- 旧系统对应：mod `peishuijing`（交叉对照，非依据）
- golden 绑定：docs/norms/conveyance_peishuijing.md（2026-08-27 起草，
  待追认）+ data/coefficients 0.7.0（factor.peishuijing.* 15 键——
  removal 零键，穿流单元）
- 公式组（已冻结）：PJ-F1~F12（分流/出流口面积/流速校核/作用水头/
  不均匀余量/井室断面/井径/总深/概算）
- 物理不变性：分配流量和=总流量（守恒——golden 断言+D3 探针锚）、
  各支路流量非负（性质归 contracts 传播面锁定——包内 properties.py
  维持结构预留注记，hebing 先例同型）

本包七固定件全实装（M0.5 骨架 → M3c 交付）；包内结构遵守
AGENTS.md §11 固定七件套，禁自由发挥。
