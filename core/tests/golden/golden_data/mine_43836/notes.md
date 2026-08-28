# mine_43836 · notes（口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-28（GOLDEN2 批，
> BASE `63784ce`，起草 commit 段一②）。

## 1. 来源说明（v1 主线口径）

- 案例源数据=旧系统 `Graduation_design/ddesign_tool/resources/
  kuangjing.ddesign.json`（8 节点矿井水线）；本批 v1=**主线 8 节点**
  （GOLDEN2 D4）：mine_water_input→tiaojiechi→chenshachi→ningjiao→
  cifenli→gaomidu→vxinglvchi→ziwai 七条链边。
- **节点全空字典**：八包 manifest 参数默认值与旧源
  kuangjing.ddesign.json 全一致（M3a 冻结核实——q_avg_daily=43836.0
  为 **m³/d 口径**（KI-F1 q_design=q_avg_daily×kz/86400），非市政
  inlet 的 m³/s 口径；kz=1.5/dn_inlet=800/z_water_inlet=100/
  z_ground=102/h_pool=3/ss_in=800/cod_in=200/nh3n_in=1/tn_in=60/
  tp_in=2 十一键），空 dict=默认即旧源值，无需参数注入
  （M3D1 `_MINE_CHAIN` 链式单点图先例同型）。
- 期望值真源=`input_project.json` 经 `app.load_project →
  app.run_full_calc` 一次实跑落盘（生成脚本实录见实现报告；脚本用后
  已删，禁手打数值纪律——与 municipal 先例同口径）。
- Metadata 实录：`engine_version="waterprint-server 0.1.0"`、
  `data_version="coefficients@1.0.0+unit_prices@1.0.0"`（UF-10 聚合
  串=worker.py sorted-join 口径，起草当日双库版本）、
  `content_hash`=design_hash=`e18e0f02…b7f3fc19`（运行 repro 三元组
  逐字同）。

## 2. 口径注记

1. **五指标面（BOD5RM）**：矿井水 B/C=0.025 无生化性（§11.15），
   Ruling BOD5-不建——全链无 bod5 键，effluent/summary 键族=
   SS/CODCR/NH3N/TN/TP 五指标（BOD5 缺席合法——`_summary_of`
   交集语义）。NH3N=1.0/TN=60.0/TP=2.0 全线透传原值（去除键仅
   SS/CODCR——chenshachi 仅 SS；ziwai 物理 0.0 穿流）。终水
   SS=1.36/COD=51.8 与 M3a3 记档逐字吻合。
2. **I1（GB 3838 III 类从严）**：案例标准=地表水 III 类（GB 3838），
   环评从严口径以本 notes 与 expected source 文字承载——coefficients
   数据包无 std.* 键族（standard_binding 透传字段写 {}，calc 零消费），
   std 键族补建归数据批挂账（G 冻结口径）。
3. **checked_units=[]**：八包 condition_mappings 全空——矿井单元不可
   入 checked_units（装配资格校验拒"须声明检修降级映射（ADR-007）"），
   两工况=design/avg（2+0）。工况间终水与主尺寸全同（映射无消费面，
   与 municipal §2.3 同现象）。
4. **无污泥线/无回流/无 m3_deferred（承诺面 v1）**：矿井污泥链手算
   表未备——污泥线/回流/m3_deferred 均不入 v1 图（README 承诺面
   已同步改写）；升版归后续批（手算表就绪后追加）。cifenli 排泥
   （q_sludge=304.8594545 m³/d 计算值）仅入 design_dims 记档，
   不接污泥边。
5. **容差口径（红线）**：逐项 rel=1e-12/abs=1e-12 双容差（municipal
   先例）；期望值存 float 全精度 repr；serialize 双跑字节级相同
   （78313 bytes，sha256 头 ed61ce1339685717，生成时双跑实录）。
6. **概算面未断言**：矿井 5 单元 v_concrete（tiaojiechi/chenshachi/
   ningjiao/gaomidu/vxinglvchi）在 field_mapping v_concrete 行
   field-wide 语义下可命中（mine 图概算可算——COST 冻结记档），
   但 v1 无 m3_deferred 键不设断言；earthwork 行 unit_id 限定市政
   单元，mine v_total/v_act_total 不命中。

## 3. 追认点清单（待领域专家批量追认）

1. **期望值整体**（2 工况终水 10 项+design 档主尺寸 20 项，共 30 项
   数值）——真源=主线实跑 2026-08-28 HEAD=3b6fce2，AI 起草待追认。
2. **主控项选取裁量**（§2 各单元 ≥2 条：input q_design/v_inlet、
   调节池 b/l/h_total、沉砂 l_cell/l_weir、凝聚 b/h_total/t_total、
   磁分离 n_disks/q_sludge、高密 b/l/q_surf_act、V 滤 b/l/f_total、
   紫外 n_rows/t_contact）。
3. **空字典默认=旧源值一致性声明**（manifest 默认与
   kuangjing.ddesign.json 十一键全等——M3a 冻结面，随本批 golden
   落盘转为机器锚定）。
4. **q_avg_daily m³/d 口径**（43836.0 非换算 m³/s——与市政 inlet
   口径差异属新架构契约派生口径，golden 如实承载）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| （待续） | | | |

---

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN2 批实现者，2026-08-28）
- 追认（领域专家）：yyx 2026-08-28（用户批复"6.追认"·Ruling 会话尾）
