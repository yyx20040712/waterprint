# conveyance_peishuiqu —— 配水渠（集配水线，M3c 已实装）

渠道形态分配构筑物：明渠输配 + 侧堰配水（m 反解堰顶水头）+ 不均匀
余量 + 变流量渠末流速校核（GB §4 最小流速防淤挂点）。

- 输入：上游端口量（配水井或上游处理单元——单股 WATER）；参数
  n/b_channel/v_channel/b（见 manifest.py 声明）
- 输出：下游端口量（**动态多口 out_1~out_n**——表内冻结口径：manifest
  ports 声明单 OUT 口 "out"，compute 按参数 n 产多键；每口
  q_avg_daily=入流/n、kz 透传、水质逐指标恒等透传——分流守恒+穿流）；
  dims=表结果全量（PQ-F1~F7）
- 旧系统对应：mod `peishuiqu`（交叉对照，非依据）
- golden 绑定：docs/norms/conveyance_peishuiqu.md（2026-08-27 起草，
  待追认）+ data/coefficients 0.7.0（factor.peishuiqu.* 12 键——
  removal 零键，穿流单元；无 wall_thickness_coef——渠长归布置面）
- 公式组（已冻结）：PQ-F1~F7（分流/渠道断面/水深/堰顶水头/不均匀
  余量/渠深/渠末流速校核）
- 物理不变性：流量守恒（分流守恒 Σ口=入流——golden 断言+D3 探针锚）、
  流速≥最小防淤流速（v_end 带校核面——副算例 Warning 路径）；性质归
  contracts 传播面锁定——包内 properties.py 维持结构预留注记

本包七固定件全实装（M0.5 骨架 → M3c 交付）；包内结构遵守
AGENTS.md §11 固定七件套，禁自由发挥。
