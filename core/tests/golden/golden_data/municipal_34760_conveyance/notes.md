# municipal_34760_conveyance · notes（口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2）。
> 起草：2026-10-02（conv-golden 批，BASE `e0f0a94bf`——UF-61④ 缺口闭：
> 首个 conveyance golden 图落地，conveyance 四单元引擎 offline 计算链
> 行为锚自此有载体）。

## 1. 来源说明（基案衍生 + 实跑录制）

- 本案例=基案 `municipal_34760`（2026-10-02 inlet-m3d 收口态，inlet
  34760.7 m³/d 面）的拓扑衍生：水线 11 边改 3 处撤 3 边（xigeshan→chenshachi/chuchenchi→
  aao/erchunchi→gaomidu）插 10 边+插
  4 节点（conveyance 四单元，params 全空 dict=manifest 默认值：peishuijing
  n=2/peishuiqu n=2/jipeishuijing n=2·t_well=4·h_well=2.5/jishuijing
  t_well=5·h_well=3），污泥链 6 边 7 节点零触碰；inlet/
  assumption_overrides/site/standard_binding 零触碰。输入经
  `save_project` 确定性序列化落盘（content_hash 随 design 变更重算
  `0092a6b0…4db2`——design_hash 正门回填，生成脚本实录见 impl-report）。
- 期望值两类来源**严格分开**（§16 A9 录入纪律）：
  1. **直引面**（effluent design/avg 帧+市政/污泥 18 单元 design_dims）：
     值逐字直引基案 expected_summary（2026-10-02 重录值）。合法性=
     零去除穿流+流量恒等——UF-61① 数学性质：conveyance 单入多出均匀
     分流（每口 q_avg_daily=入流/n）+汇流口 Σq 恢复（q/2+q/2==q 二进制
     精确、双精度位串级）+水质逐指标恒等透传（零去除），故市政单元
     入流位串与基案恒等→其 dims/effluent 位串恒等（生成脚本逐键
     struct.pack 对拍 0 diff 实证，非假设）。
  2. **实跑面**（conveyance 四单元 dims+generated serialize 双锚+
     m3_deferred）：值=本案例 input 经 `app.load_project →
     app.run_full_calc` 一次实跑录制（HEAD=e0f0a94bf+包内公式锚
     PJ-F1~F12/JS-F1~F7/PQ-F1~F7/JP-F1~F9+守恒断言；脚本用后已删，
     禁手打数值纪律）。

## 2. 口径注记

1. **插入点位与旧系统对照**：旧系统全厂图
   （`Graduation_design/ddesign_tool/resources/yyx.ddesign.json`，34 节点：
   水线 13 单元+污泥线+**集配水**+高程配置；constraint_overrides 含
   peishuijing/peishuiqu/jipeishuijing/jishuijing 四键）本有集配水段，
   基案 golden 落图时未携带——本批补插：细格栅后配水井（双口）→
   集水井（汇流）→旋流沉砂池；初沉池后配水渠（双口）→AAO；二沉池后
   集配水井（双口）→高密沉淀池。插入点位=旧系统集配水段在主线中的
   相对位置（格栅/沉淀池后分送、泵前集水），非逐节点复刻（旧系统
   34 节点含高程配置节点，golden 面不追平——集配水四单元行为锚为
   本批目的）。
2. **多出流口口径（表内冻结）**：三配水类单元 manifest ports 声明单
   OUT 口 "out"（流体/方向声明锚点），compute 按参数 n 动态产
   out_1~out_n（每口 WaterFlow(q_avg_daily=入流/n, kz 透传)+水质恒等
   透传）；图边直接引 out_1/out_2 口（app 装配不对账边与端口声明——
   T6 装配对账挂账在册口径）。集水井/集配水井多股入一经 propagate
   按 dst 分组加权合并（汇流面）。
3. **checked_units 勾选（2+k 的 k=3）**：`["conveyance_peishuijing",
   "conveyance_jipeishuijing", "conveyance_peishuiqu"]`——三配水类
   多口单元（condition_mappings=n 并联系列数降级三元式在册）。
   **jishuijing 不勾**：单井容蓄无并联系列数（condition_mappings=()
   明示不映射，cond3 批 2026-10-01 D4 诚实行为），勾选=装配期
   InvalidAssemblyError 拒检（e2e 拒检面锚承载）。承载位置=
   expected_summary 顶层 checked_units+design.checked_units 双录
   （本案例与基案不同：基案 design 侧留空，本案例 design 侧同录——
   正门 run_full_calc 消费 design.checked_units 面经资格校验）。
4. **offline 帧（检修饥饿边）**：offline 档参数 n 降 n−1=1 → 单元只产
   out_1（承载全流量），设计期布线的 out_2 边饥饿。引擎承接口径=
   executor_assembly.forward_stocks 检修饥饿边零股（conv-golden 批缺陷即修：
   修复前裸 KeyError 逃逸——impl-report 缺陷清单；回炉轮 1 判据钳制=仅缺股
   源单元==offline 目标单元时承接，非目标缺股维持原生 KeyError）——零股
   WaterFlow(0, kz=1)+空水质，Σ边股==入流守恒成立（e2e 守恒锚）。
   offline 帧 effluent==design 值、其余全部单元 dims 与 design 帧
   IEEE 位串恒等（n-不变常数去除率性质+「该单元 n−1、其余全池」
   ADR-007 冻结语义——e2e 位串级锚）。
5. **容差口径（红线）**：逐项 rel=1e-12/abs=1e-12 双容差（基案同款）。
   serialize 双锚（643273 bytes，sha256 前 16 位 16b18ff38b8bd9d1，
   生成时双跑字节同——确定性 R3）。
6. **m3_deferred**：estimate_total=19572799.39726267 元（≠基案
   19415730.31——takeoff field-wide v_concrete 行自动计入 conveyance
   peishuijing/jishuijing/jipeishuijing 三口新工程量；peishuiqu 无
   v_concrete 键不计入）；total_sludge=5306.514999999999 kg/d（污泥链
   零触碰与基案同值）。grand_total 逐级自洽先证后录（e2e m3 双断言）。
7. **N/P 指标现状**：承基案 §2.4 记档（系数面对生物池 N/P 去除未
   建模），本案例六指标值与基案逐字同（穿流性质+常数去除率）。

## 3. 追认点清单（待领域专家批量追认）

1. **插入点位裁量**（§2.1 三处插入位置=旧系统集配水段相对位置，
   非逐节点复刻）。
2. **conveyance 四单元 dims 全量键**（14+8+7+10=39 项——实跑录制，
   公式锚=包内 golden 例在册）。
3. **checked_units 集合**（三配水类+jishuijing 不勾）与双录承载位置。
4. **检修饥饿边零股口径**（§2.4——executor 承接语义，规格头
   【检修饥饿边口径】节全文）。
5. **estimate_total 新工程量计入**（§2.6 三口 v_concrete）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-10-02 | conv-golden（起草基线） | 首录 | 基案衍生新案：水线 18 边/23 节点（基案 11 边撤 3 插 10）；offline 帧 out_2 饥饿边裸 KeyError 修复（executor_assembly.forward_stocks 零股承接——仅目标单元饥饿边）；effluent/市政 dims 直引基案（位串级 0 diff 实证） |
| （待续） | | | |

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（conv-golden 批实现者，2026-10-02）
- 追认（领域专家）：＿＿＿
