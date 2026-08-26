# municipal_34760 · notes（口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-26（GOLDEN 批，
> BASE `134d4a3`）。

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
   不入 golden 图，回流案例归 M3。
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
8. **M3 补录两项（禁造假）**：`m3_deferred.estimate_total`（概算总数）
   与 `m3_deferred.total_sludge`（全厂总泥量）——当前无 cost/污泥线，
   字段以"M3 补录"字串占位缺席，禁止填数。
9. **bench 实测余量（D4 记档）**：test_bench_full_calc 实测 mean
   286.7490 ms（min=max=mean，pedantic rounds=1 单轮，2026-08-26 实录）
   < 5.0 s 预算（§18.1 口径 32 单元、当前 13 单元子集），余量 ≈4.71 s
   （94.3%）——单元数扩至 32 或更慢单元入链时此守卫先红。

## 3. 追认点清单（待领域专家批量追认）

1. **期望值整体**（5 工况终水 30 项 + design 档主尺寸 41 项，共 71 项
   数值）——真源=主线实跑 2026-08-26 HEAD=134d4a3，AI 起草待追认。
2. **checked_units 勾选集合**（三大主体构筑物代表面）与承载位置
   （expected_summary 承载 + build_condition_set 正门，design 留空）。
3. **容差口径**（rel=1e-12/abs=1e-12 双容差不放宽）。
4. **M3 补录两项**（概算总数/全厂总泥量缺席记档，M3 批补录）。
5. **主控项选取裁量**（§2.6：高密 b/V 滤参数面承载等）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-08-26 | GOLDEN（起草基线） | 终水/主尺寸与 M2c、M2-SOL 探针数字微差 | 输入定点化（save_project round 10）+独立构造输入，非回归；本批起以本三件套为唯一锚 |
| （待续） | | | |

---

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN 批实现者，2026-08-26）
- 追认（领域专家）：＿＿＿ 日期：＿＿＿
