# mine_43836 · notes（口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-28（GOLDEN2 批，
> BASE `63784ce`，起草 commit 段一②）；**v2 升版：2026-08-28
> （MSLUDGE2 批 7b 段二，BASE `bcfbc60`——污泥线三节点参数注入+
> std.gb3838_iii 实绑+m3 双锚补录，数值真源手算表
> docs/norms/mine_water_sludge_line.md §21-③ 已追认）**。

## 1. 来源说明（v1 主线口径 + v2 污泥线升版）

- 案例源数据=旧系统 `Graduation_design/ddesign_tool/resources/
  kuangjing.ddesign.json`（8 节点矿井水线）；v1=**主线 8 节点**
  （GOLDEN2 D4）：mine_water_input→tiaojiechi→chenshachi→ningjiao→
  cifenli→gaomidu→vxinglvchi→ziwai 七条链边。
- **节点全空字典**：八包 manifest 参数默认值与旧源
  kuangjing.ddesign.json 全一致（M3a 冻结核实——q_avg_daily=43836.0
  为 **m³/d 口径**（KI-F1 q_design=q_avg_daily×kz/86400），非市政
  inlet 的 m³/s 口径；kz=1.5/dn_inlet=800/z_water_inlet=100/
  z_ground=102/h_pool=3/ss_in=800/cod_in=200/nh3n_in=1/tn_in=60/
  tp_in=2 十一键），空 dict=默认即旧源值，无需参数注入
  （M3D1 `_MINE_CHAIN` 链式单点图先例同型）。
- **v2 图形态**：8+3 节点（+sludge_hebing/sludge_nongsuo/
  sludge_tuoshui）/7+2 边（hebing.out→nongsuo.in→tuoshui.in 两链边
  ——SLUDGE forward）；hebing 无上游=图源单元（三股排泥经参数注入，
  GOLDEN2 市政 hebing 同构）；ziwai 与污泥线无关联（无回流边——
  nongsuo sup/tuoshui filtrate 回流口默认关=边不连，矿井真环归
  GOLDEN4）。
- 期望值真源=`input_project.json` 经 `app.load_project →
  app.run_full_calc` 一次实跑落盘（生成脚本实录见实现报告；脚本用后
  已删，禁手打数值纪律——与 municipal 先例同口径）。v1 锚 source=
  主线实跑 HEAD=3b6fce2；v2 新锚 source=主线实跑 HEAD=bcfbc60。
- Metadata 实录：`engine_version="waterprint-server 0.1.0"`、
  `data_version="coefficients@1.1.0+unit_prices@1.0.0"`（v2 起随
  生成日库实拍——worker.py sorted-join 口径；v1 曾为 1.0.0 库值）、
  `content_hash`=design_hash=`ec714e47…1e4be14`（v2 图+绑定后重算；
  v1 曾为 e18e0f02…b7f3fc19——运行 repro 三元组逐字同）。

## 2. 口径注记

1. **五指标面（BOD5RM）**：矿井水 B/C=0.025 无生化性（§11.15），
   Ruling BOD5-不建——全链无 bod5 键，effluent/summary 键族=
   SS/CODCR/NH3N/TN/TP 五指标（BOD5 缺席合法——`_summary_of`
   交集语义）。NH3N=1.0/TN=60.0/TP=2.0 全线透传原值（去除键仅
   SS/CODCR——chenshachi 仅 SS；ziwai 物理 0.0 穿流）。终水
   SS=1.36/COD=51.8 与 M3a3 记档逐字吻合。v2 污泥线 SLUDGE 通道
   零水质指标（outqualities 空 WaterQuality 单元元）——键族不变。
2. **I1（GB 3838 III 类从严）**：案例标准=地表水 III 类（GB 3838），
   环评从严口径 v2 起以 **standard_binding 实绑**承载——
   `{"effluent": "std.gb3838_iii"}`（golden-cases.md Step1
   "std.<数据包键>"指引形态；coefficients 1.1.0 std 键族五键
   [GOLDEN3 D3 补建——v1 旧口径"sync 键族补建归数据批挂账"就此
   收口兑现]）。绑定面透传 calc 零消费（只入 content_hash）；e2e
   断言=绑定前缀键集钳制恰五键（表 1 无 SS 项）+五键逐值
   cod=20/bod5=4/nh3n=1/tn=1/tp=0.2 mg/L。
3. **checked_units=[]**：八包+污泥三包 condition_mappings 全空——
   矿井/污泥单元不可入 checked_units（装配资格校验拒"须声明检修
   降级映射（ADR-007）"），两工况=design/avg（2+0）。工况间终水与
   主尺寸全同（映射无消费面，与 municipal §2.3 同现象）。
4. **污泥线三节点参数注入（v2 兑现——v1 承诺面收口）**：
   - **sludge_hebing 12 键全键照录**（D3 注值面覆盖——manifest
     默认=市政 34760 案例值，不覆盖则产率链照跑市政口径）：六注入键
     =手算表三股语义映射链值（磁泥→ds_primary=26827.632/p_primary
     =0.92[MS-F1=KS-F6 w_ss×1000]；沉砂→ds_bio=3787.4304/p_bio=
     0.10[MS-F2=KC-F5 湿砂×1.6×0.90×1000]；泥渣→ds_chem=2682.7632/
     p_chem=0.97[MS-F3=SS 去除衡算]）；产率链六键矿井口径——
     q_avg_daily=43836.0（算例同源）；s0_bod/se_bod 手算表无值
     （BOD5 不建）按 B/C=0.025 关联推导记档：**s0_bod=cod_in
     200×0.025=5.0，se_bod=终水 CODCR 51.8×0.025=1.295**（s0>se
     校验满足；推导占位值——互校面结构性不激活）；v_bio=10714.95/
     x_vss=3000/t_design=15 无矿井参照面（无生化单元）=manifest
     默认原值显式携带（记档呈总控）。产率链衍生 dims（s_y/dx_bio/
     dev_pct/ds_check/dev_close）**不入锚**（手算表"互校面矿井
     结构性不激活"声明在册——锚只取 HB 三主控键 q_total/ds_total/
     p_merged）。
   - **sludge_nongsuo 五键**：q_solid=60（带上限档）/t_thicken=16/
     h_eff=4.0/n=2/p_out=**0.90 带外直值**（§21-③ 追认点 3 裁
     "案例注入直值"路线——带内任一值致负上清液 q_sup=−170.38
     物理矛盾；coefficients band 扩带不做）；h_cone=2.0 构造默认
     不入注。
   - **sludge_tuoshui 三键**：dose_pam=3（无机泥低耗档）/p_cake=
     0.75（带式主算例——副档 0.72 呈报不取）/n_standby=1；
     machine_type 默认 1=带式档选键 factor.tuoshui.machine.
     belt_capacity=20.0 **库值恰=手算表主算例 q_machine 20——
     不入节点注入面**（q_machine 系机型档系数键非 manifest 参数）；
     NS/TU **eta_capture 两键**（0.90/0.95——手算表"固体截留率/
     固体回收率"行）=manifest 默认恰合手算表取值，未入注入面
     （MSLUDGE2 M1 收口记档：生效值经手算对照 0 残差反证——
     NS ds_out=33297.8256×0.90、TU ds_cake=28469.640888 精确成立，
     默认漂移即锚红）。
   - **cifenli 排泥下游闭环**：v1 q_sludge=304.8594545 m³/d 计算
     值搁置无下游——v2 经 MS-F1 干基链（ρ=1100 口径）入 hebing
     磁泥股（HB-F1 ρ=1000 简化投影 335.3454——9.1% 密度口径差
     声明见手算表映射表节，DS 守恒面不受影响）。
5. **容差口径（红线）**：逐项 rel=1e-12/abs=1e-12 双容差（municipal
   先例）；期望值存 float 全精度 repr；serialize 双跑字节级相同
   （**GOLDEN4a 2026-08-28：106996 bytes**[v2 曾 106134——六单元产泥口
   sludge_out 无条件产股使三键×2 工况入 serialize，42 数值锚零扰动
   程序化实证]，**sha256 头 3125bebe1fa35546**，生成时双跑实录）。
6. **m3_deferred 双锚（v2 补录——v1 概算面未断言收口）**：
   estimate_total=**10980598.97665583**（cost 三正门直调
   [takeoff→estimate]——11 节点全图 design 档 grand_total；app 未
   接 cost 属既定架构，测试直调 municipal 先例；takeoff 6 项——
   mine 5 单元 v_concrete+NS v_concrete 概算可算面，earthwork 行
   unit_id 限定市政单元不命中）；total_sludge=**33297.8256**（hebing
   ds_total 干基 kg/d 主口径；湿基 q_total=428.979096 以 design_
   dims 锚承载双断言）。DS 守恒链断言：hebing ds_total=三股注入
   干基之和（HB-F4/contracts.sludge.mix R1 镜像）。
7. **警告面记档（非阻断 WARN——机制性呈报）**：hebing dev_pct=
   1241.41% 超上限 20%（B/C=0.025 无生化——经验产率/机理互校面
   矿井结构性不激活，BOD 对为推导占位值，提示核对 SS/BOD 比系
   机制面诚实呈报）；nongsuo p_out=0.90 越出建议带 [0.95,0.98]
   （矿井重定义档直值路线——§21-③ 追认点 3 在册）。两警告×2
   工况入 serialize（确定性——双跑字节同实证）。

## 3. 追认点清单（待领域专家批量追认）

1. **v1 期望值整体**（2 工况终水 10 项+design 档主尺寸 20 项，共 30 项
   数值）——真源=主线实跑 2026-08-28 HEAD=3b6fce2，AI 起草待追认
   （v2 已程序化实证零扰动）。
2. **v1 主控项选取裁量**（§2 各单元 ≥2 条：input q_design/v_inlet、
   调节池 b/l/h_total、沉砂 l_cell/l_weir、凝聚 b/h_total/t_total、
   磁分离 n_disks/q_sludge、高密 b/l/q_surf_act、V 滤 b/l/f_total、
   紫外 n_rows/t_contact）。
3. **空字典默认=旧源值一致性声明**（manifest 默认与
   kuangjing.ddesign.json 十一键全等——M3a 冻结面，随本批 golden
   落盘转为机器锚定）。
4. **q_avg_daily m³/d 口径**（43836.0 非换算 m³/s——与市政 inlet
   口径差异属新架构契约派生口径，golden 如实承载）。
5. **v2 新锚 12 项**（design_dims 三单元 10 项[HB q_total/ds_total/
   p_merged+NS a_load/d/q_thick/q_sup+TU q_cake/ds_cake/
   n_machine_total]+m3 双锚 2 项）——真源=主线实跑+cost 直调
   2026-08-28 HEAD=bcfbc60；参数注入档（hebing 12 键/nongsuo 5 键/
   tuoshui 3 键+s0_bod/se_bod B/C 推导式+v_bio 三键默认携带记档）
   随 §21-③ 追认（2026-08-28 用户批复"2.批准"）落盘——手算表
   主算例 35 项对照 0 项超 1e-9（最大残差 NS d_raw rel=5.7e-10，
   系表内联 3.14159265 八位 π vs math.pi 全精度口径差；取整后 d
   同为 19.0 不入差异面）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-08-28 | MSLUDGE2（v2 升版） | serialize 78313→106134 bytes/三元组与 data_version 1.0.0→1.1.0/content_hash 重算 | 只增面：三单元×2 工况快照+警告入 serialize；生成日库实拍（R2 真值化先例）；旧 30 锚数值位级零扰动（程序化实证） |
| 2026-08-28 | GOLDEN4a（产泥口实体化） | serialize 106134→106996 bytes/sha 头 e5a528a7→3125bebe | 只增面：cifenli/chenshachi/gaomidu 六单元产泥口 sludge_out 无条件产股（三键×2 工况入 serialize——nongsuo sup 先例同构）；42 数值锚位级零扰动（程序化实证 removed=0，变更恰 generated 三元组）；e2e 断言零改动（三元组读 expected） |
| （待续） | | | |

---

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN2 批实现者，2026-08-28）
- 追认（领域专家）：yyx 2026-08-28（用户批复"6.追认"·Ruling 会话尾）
- v2 升版（AI）：＿＿＿（MSLUDGE2 批实现者，2026-08-28——BASE
  bcfbc60，§21-③ 追认通过后开工）
