# municipal_34760 · notes（口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-26（GOLDEN 批，
> BASE `134d4a3`）；**升版：2026-08-28（GOLDEN2 批，BASE `63784ce`
> ——污泥链扩图 12→19 节点+m3_deferred 换真值，见 §6）**。

## 1. 来源说明（探针演变 → 输入固化）

- 本案例输入与期望值演变链：M2c 临时探针（脚本已按规自删、精确输入集
  不可复现）→ M2-SOL 探针①（十二节点主线 app 正门零扰动证明，
  127008 字节双跑同）→ **本批输入固化**：`input_project.json` 入库，
  期望值=该文件经 `app.load_project → app.run_full_calc` 一次实跑落盘
  （生成脚本实录见实现报告；脚本用后已删，禁手打数值纪律）。
- 输入固化根治 M2c 教训（探针不可复现）：此后任何批次的回归差异都能以
  本文件字节为锚复算。输入=十二节点主线（inlet 六指标全配 +
  11 个市政单元 manifest 默认参数），参照 `test_bench_enumerate._wiring()`
  与 server conftest `_cass_project_payload()` 同源形态。
- `q_avg_daily=0.4023229167`（m³/s）：由 34760.7/86400 经 `save_project`
  确定性序列化 round(x,10) 定点——**入库字节即输入**，期望值真源=
  load 回读后的实跑（与未定点原值的探针数字存在微差，属口径而非缺陷）。
- Metadata 四 str 实录：`format_version="1.0"`、
  `engine_version="waterprint-server 0.1.0"`（现行 server 正门口径）、
  `data_version="coefficients@0.4.0+unit_prices@0.0.0"`（UF-10 版本聚合）、
  `content_hash` = design_hash = `942b3271c905…41143c09`（与运行 repro
  三元组逐字同，结果绑定输入已闭环）。

## 2. 口径注记

1. **主线口径（Ruling ③）**：无回流十二节点主线——inlet→污水提升泵房→
   粗格栅→细格栅→旋流沉砂池→辐流初沉池→AAO→辐流二沉池→高密沉淀池→
   V 型滤池→紫外消毒→巴歇尔计量槽。CASS/调节池不在主线（CASS 为旁路
   工艺、调节池归矿井水线/市政缓冲另行案例）；浓缩上清液/脱水滤液回流
   不入 golden 图，回流案例归 M3。**GOLDEN2 扩面（2026-08-28）**：
   追加污泥链 7 节点（hebing→shusong→bengzhan→nongsuo→xiaohua→
   tuoshui→ganhua，水线 12 节点零扰动）——nongsuo sup/tuoshui
   filtrate 回流口声明不连边（UF-11 Ruling ②；Q1 已裁启用，回流边
   实装归 GOLDEN3）。
2. **checked_units 勾选（2+k 的 k=3）**：`["municipal_chuchenchi",
   "municipal_aao", "municipal_erchunchi"]`——三大主体构筑物（初沉/
   生物池/二沉）代表面。**承载位置**：`expected_summary.json` 顶层
   `checked_units` 字段 + 测试经 `build_condition_set` 正门构造工况集；
   `design.checked_units` 留空——负向实录：13 单元
   `manifest.condition_mappings` 当前全空，勾选入 design 会被装配资格
   校验拒（"须声明检修降级映射（ADR-007）"，InvalidAssemblyError）。
3. **敏感性工况与 design 同值**：工况映射全空 → `pool.all_pools` 绑定
   无消费面，5 工况（design/avg/design_offline_×3）终水与主尺寸完全
   相同（实跑实录）。condition_mappings 录入后敏感性面才会分化，
   届时本 golden 需升版重录。
4. **N/P 指标现状（重要差异记档）**：终水 NH3N=26.0/TN=43.0/TP=6.5
   与进水原值相同——当前系数面（0.4.0）对生物池 N/P 去除未建模
   （BOD5/COD/SS 去除链完整）。对照一级 A（GB 18918-2002）：
   BOD5 5.53≤10 ✓ / COD 19.19≤50 ✓ / SS 0.24≤10 ✓ /
   NH3N 26>5(8) ✗ / TN 43>15 ✗ / TP 6.5>0.5 ✗。N/P 去除建模
   属数据/单元批欠账，golden 如实记录现状，不造达标假象。
5. **粪大肠**：不在 outqualities 面（主线输出仅六指标）；紫外消毒
   粪大肠灭活结果以 dims `c_fecal_out=10.0`（个/L）承载（design_dims
   已收录）。
6. **主尺寸主控项选取**：design_dims 每 unit ≥1 项，取 dims 全量字段
   中主控项。注记：高密沉淀池 dims 无 D（直径）字段，取池宽 b=8.5 为
   主控；V 型滤池分格数 n 是 manifest 参数（grid [4,6,8,10]）不在
   dims，取 b/l/a_total_act 承载；初沉 D×n 之 n 同为参数（默认 2），
   D=24.0 在 dims。此项选取属工程裁量，列入追认。
7. **容差口径（红线）**：逐项 rel=1e-12/abs=1e-12 双容差（M2-SOL 接线
   断言先例口径）。期望值存 float 全精度 repr，确定性系统双跑 serialize
   字节级相同（333886 bytes，sha256 前 16 位 4253f6eb0231d06d，
   生成时双跑实录），实际对照 diff=0，容差为工程冗余而非放松。
   **GOLDEN2 复录（19 节点，2026-08-28）**：497060 bytes，sha256
   前 16 位 a21ae93581e2b3db（双跑字节同）。
   **R2 更正（2026-08-28 修复轮）**：data_version 由 GOLDEN 批
   沿用串更正为生成日实拍（coefficients@0.4.0+unit_prices@0.0.0
   →coefficients@1.0.0+unit_prices@1.0.0，input metadata 同步，
   与 mine 同日同源）——二审 B6 实证版本串不进计算路径、数值
   零扰动（86 锚复跑 0 diff），属印记真值修正；serialize 双锚随
   复跑刷新（字节长 497060 不变——两串等长，sha 头
   a21ae93581e2b3db→8bbbf8a6770e6fa7——串经 repro 入 serialize）。
8. **M3 补录两项（禁造假→已换真值）**：`m3_deferred.estimate_total`
   （概算总数）与 `m3_deferred.total_sludge`（全厂总泥量）——GOLDEN
   批（2026-08-26）以"M3 补录"字串占位缺席；**GOLDEN2 批（2026-08-28）
   换真值**（结构 {value, source, abs, rel} 与 design_dims 条目同形态，
   见 §6.3/§6.4）。
9. **bench 实测余量（D4 记档）**：test_bench_full_calc 实测 mean
   286.7490 ms（min=max=mean，pedantic rounds=1 单轮，2026-08-26 实录）
   < 5.0 s 预算（§18.1 口径 32 单元、当前 13 单元子集），余量 ≈4.71 s
   （94.3%）——单元数扩至 32 或更慢单元入链时此守卫先红。
   **GOLDEN2 复测（19 节点，2026-08-28）**：mean 123.0758 ms
   （单轮）< 5.0 s 预算，余量 ≈4.88 s（97.5%）。
   **R4 环境注记（2026-08-28 修复轮）**：bench 读数=pedantic 单轮
   （rounds=1 iterations=1），受机器/负载环境影响显著——二审本机
   复测同代码 mean=1583.9 ms=记录值 12.9 倍，单轮噪声坐实；亦与
   2026-08-26 十三节点基线 286.7490 ms 不可直接横比（环境不同）。
   两值均 <5.0 s 预算（门禁面绿），记录值保留原实录不改。

## 3. 追认点清单（待领域专家批量追认）

1. **期望值整体**（5 工况终水 30 项 + design 档主尺寸 41 项，共 71 项
   数值）——真源=主线实跑 2026-08-26 HEAD=134d4a3，AI 起草待追认。
2. **checked_units 勾选集合**（三大主体构筑物代表面）与承载位置
   （expected_summary 承载 + build_condition_set 正门，design 留空）。
3. **容差口径**（rel=1e-12/abs=1e-12 双容差不放宽）。
4. **M3 补录两项**（概算总数/全厂总泥量——GOLDEN 批缺席记档，
   GOLDEN2 批换真值，见 §6）。
5. **主控项选取裁量**（§2.6：高密 b/V 滤参数面承载等）。
6. **GOLDEN2 扩面新增追认**（2026-08-28，待追认）：
   a. **污泥链链序裁量**——shusong（输送）位置取 hebing→shusong→
      bengzhan（sludge_shusong.md 表"工艺位置"行原文；M3D2
      `_SLUDGE_CHAIN` 先例同序）；
   b. **hebing 三股注入值出处**——manifest params 键 ds/p 六键
      逐字（docs/norms/sludge_hebing.md 主算例：ds_primary=3240.12/
      p_primary=0.96/ds_bio=1928.690/p_bio=0.994/ds_chem=137.7050/
      p_chem=0.98；湿量 q 三股 81.003/321.4483333333/6.88525 m³/d
      为 HB-F1~F3 派生值不入参数面）；
   c. **污泥 7 单元主控项裁量**（§5.2 的 15 项）；
   d. **概算基数变化**（§6.3——19 节点 vs COST2 12 节点记档金数差）；
   e. **m3_deferred 真值**（§6.3/§6.4 两数值+双断言锚）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-08-26 | GOLDEN（起草基线） | 终水/主尺寸与 M2c、M2-SOL 探针数字微差 | 输入定点化（save_project round 10）+独立构造输入，非回归；本批起以本三件套为唯一锚 |
| 2026-08-28 | GOLDEN2（扩污泥链） | estimate_total=11908574.59503396 ≠ COST2 记档 10536911.04824766（12 节点图） | 概算基数 12→19 节点：污泥 bengzhan/nongsuo/xiaohua 三单元 v_concrete（0.6218+234.0173+835.7761 m³）经 field_mapping field-wide 行自动计入，差 +1371663.55 元；COST2 金数语义=12 节点图，两者各自成立 |
| （待续） | | | |

## 5. GOLDEN2 升版记档（2026-08-28，污泥链扩面+m3 真值）

1. **扩图零扰动实证**：水线 12 节点数值零扰动=DoD 硬项——生成脚本
   实跑逐项对照旧 71 锚 0 diff；expected 文件 git diff 删除行仅
   generated 3 行（serialize 刷新）+m3_deferred 2 占位串，71 锚
   （effluent 30+design_dims 41）只增不改。content_hash 随 design
   变更重算：`942b3271…`→`5c0575e8…a039b8`（design_hash 正门回填）。
2. **污泥 7 单元 design_dims 主控项**（15 项新增，2026-08-28
   HEAD=63784ce）：hebing ds_total/q_total/p_merged、shusong
   d_pipe/v_act、bengzhan n_total/h_pump、nongsuo d/q_thick、
   xiaohua d/v_total、tuoshui n_machine_total/q_cake、ganhua
   m_out/w_evap。污泥链衔接值与 M3b1 手算表逐字全等（ds_total
   5306.515/q_total 409.3365833333/p_merged 0.9870363041/q_sup
   289.9399958333/ds_sup 530.6515/q_thick 119.3965875/p 0.96/
   q_filtrate 103.408841722/泥饼含水率 0.78）。
3. **estimate_total=11908574.59503396 元**：全图（19 节点）design 档
   takeoff 14 项（COST2 12 节点 11 项+污泥三单元 v_concrete）→
   build_estimate grand_total；grand_total 逐级自洽
   （subtotal 9932088.903281035+reserve 993208.8903281036+
   Σtax 983276.8014248224）。**取数口径**：app 正门未接 cost
   （result_schema"愿景未落"注记）——测试直调 cost 三正门
   （tests/cost/test_estimate.py 先例）。与 COST2 记档差异见 §4。
4. **total_sludge=5306.514999999999 kg/d**：hebing ds_total（干基
   主口径）；湿基 q_total=409.33658333333295 m³/d 以
   design_dims["sludge_hebing"]["q_total"] 锚承载双断言。
5. **D3 summary 多汇点未触发**：扩图首跑实测定夺——拓扑执行序
   municipal_bashi_jiliangcao 仍居末位（19 序最后），`_summary_of`
   现行 terminal 口径取 bashi 六指标全，ganhua 空水质汇点在其前
   被跳过；最小改动纪律 app.py 零触碰。

---

## 6. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN 批实现者，2026-08-26；GOLDEN2 升版
  实现者，2026-08-28）
- 追认（领域专家）：＿＿＿ 日期：＿＿＿
