# ADR-024：能耗药耗计算面——单元级 power/dose 输出+summary 全厂聚合（B4-2a 碳核算前置一）

- 状态：**Accepted**（授权链=《复杂度治理裁决书》方案五②前置探针结论
  三段路线第一段+2026-09-19 用户裁决「计算逻辑呈用户审查」R-B42a-1；
  计算逻辑呈批=本 ADR 决策表+系数档表）
- 背景：
  - 碳核算探针（2026-09-18，《裁决书》方案五节）实测：电耗计算空白
    （无任何单元输出功率/电耗；曝气/泵/搅拌三大耗电源均无功率计算）、
    药耗部分存在（gaomidu/ningjiao 有 m_pac/m_pam、cifenli 磁种、
    tuoshui w_pam——无全厂聚合口径）、运行成本不存在。结论=碳核算
    前置是先建运营消耗计算面，三段路线：①能耗药耗计算批（本 ADR）
    →②运行成本面（opex，B4-2b）→③碳核算本体。
  - 锁面约束：PlantResult 顶层 _ROOT_KEYS 严格校验（ADR-012 D1 已裁定
    顶层加键=旧结果文件全拒读）；summary 内层=开放 float 映射
    （result_schema.py:169-193——免破键扩展槽）；golden 四案 serialize
    字节/哈希锚+summary 键集钳制=锁面（曝气头数据面批 14f1efa 先例：
    解锁→更新→重锁+[HUMAN-LOCK]）；units_lib compute.py ≤400 行+
    全文件 ≤500 行预算墙（aao/cass manifest 479/499+compute 双 400
    顶墙——本批必须拆文件）。
- 决策：

| # | 决策 | 理由 |
|------|------|------|
| D1 | **曝气/生物池单元预算墙拆件**：aao/cass 各立 `formulas_energy.py`（AO-F21~F25/CA-F29~F33 规格声明件）+`energy.py`（计算段——_oxygen 自 compute 迁入+能耗求值）；manifest 并组注册（`_FORMULAS = (*_FORMULAS, *FORMULAS_ENERGY)`）保持单注册口 | manifest/compute 双顶 500/400 墙（AGENTS §2 超限拆文件无豁免）；B2-5 D1-B「条目留 manifest 原位」读作**单元包原位**（条目仍在单元包内、manifest 仍是注册口——预算墙逼出的最小背离，规格头注记）；_oxygen 迁移=O2→供气→风机功率主题连续性 |
| D2 | **summary 开放映射槽位扩展**（路线 A）：新平键族 `power_{aeration,pump,stir}_kwh_d`+`power_total_kwh_d`+`dose_{pac,pam,seed}_kg_d`；聚合器=新根模块 `app_energy.py`（app_trust 拆分先例同构第五例），`app._with_energy` 与六指标族合并注入 | result_schema 零改（ADR-012 D1 总线稳定红线保持——旧结果文件可读）；server/webapp 零变更（本批无端点/响应模型变更——前端重生成步不触发）；calcbook `{{summary.*}}` 平键自动可用 |
| D3 | **键名约定聚合**（零单元耦合表）：单元以标准键名自报消耗——e_aeration/e_pump/e_stir（kWh/d）与 m_pac/m_pam/w_pam/m_seed_net（kg/d）；聚合器 sparse Σ（有则录无则略，_summary_of 同口径）；w_pam 并入 dose_pam（PAM 族）；m_seed 毛耗不聚合（磁种循环投加非净消耗——cifenli m_seed_net 承载补充口径） | 单元自报+聚合器纯投影=计算逻辑留在单元公式（可审计、呈用户审查）；耦合表（unit_id→字段映射）方案弃——键名约定零注册、新单元零改造接入 |
| D4 | **单元级日耗能键设计**：单元输出物理中间量（q_air/p_blower/p_pump/p_stir kW·m³/s）+日耗能键（e_* = 功率×24h 运行口径）；×24h 连续运行假设落在单元公式（AO-F23/F25、CA-F31/F33、TJ-F14/KT-F13/GM-F21/KN-F16——每条 norm_ref 注记） | 假设显式入公式=呈审查可追溯；聚合器不藏口径知识；CASS 特化=CA-F31 含 duty_ratio 0.5（周期曝气间歇运行——4h 周期 2h 曝气典型档，异于 AAO 连续流×24 满时） |
| D5 | **泵日耗电能量法**：e_pump = ρg·Q_日均·H_设计点/η×24h（TS-F16）/ρg·q_wet·H/η÷3.6e6（BZ-F20——q_wet m³/d 直除式）；**不引入运行时数参数** | 能量守恒口径：日提升量×扬程=日功——间歇启停由能量法自然消化（无需 t_run 参数与台数×时数口径分叉）；扬程按设计点、流量按平均日双口径注记在 norm_ref |
| D6 | **量纲策略**：q_air=FLOW（V 型滤池 XL-F10 先例）；功率/日电耗=DIMENSIONLESS（kW/kWh/d 语义 meaning 承载——TJ-F9/KN-F6 先例）；**不扩 DimKey 能量成员**（ENERGY/kWh 量纲+白名单三表同步=扩成员批 [HUMAN-LOCK] 面，收益不抵成本） | 既有两先例并存择一从众（DJ 审查点）；量纲体系零触碰=UF-20 冻结保持 |
| D7 | **系数档**（data 1.3.0，factors.yaml +18 键）：aao/cass blower 五键同族同值（f_sor=1.33/0.28/EA=0.20/Δp=70 kPa/η=0.70）+cass duty_ratio 0.5+两 stir 密度 6 W/m³+ts/bz 泵效率 0.75/0.70+水密度 1000×2+bz 重力 9.81 | AOR→SOR 五系数分列修正（α/β/ρ/DO/Cs）以综合折算系数 f_sor 承载——工程常用带中值，完整修正挂账 B4-2b；全部 AI 起草待领域专家追认（数据策略 v2） |
| D8 | **范围边界**：三族（曝气风机/泵/搅拌）+既有药耗聚合；**挂账 B4-2b**——紫外电耗（ziwai 灯管数不在 dims）/污泥脱水与消化设备电耗/电机效率与装机功率口径/旋流沉砂池驱动电机/完整 SOR 五系数修正/ENERGY 量纲正名 | 《裁决书》三段路线第一段范围=三大耗电源；边界外项目显式挂账防静默漏项 |

- 后果：
  - 正面：碳核算第一段落地——全厂电耗/药耗聚合字段进 result 总线
    （summary 平键，旧消费方零破坏）；单元级中间量（供气量/风机功率/
    泵轴功率）同时可供导出面与后续 opex/碳核算直接消费；比电耗工程
    合理性锚=municipal 案 0.208 kWh/m³（三族覆盖口径，典型市政厂带）。
  - 代价：锁面批（golden 四案 serialize 锚+summary 键集+单元测试期望
    +m3 seed+snapshots 重录+[HUMAN-LOCK] 重锁——曝气头批同款工序）；
    aao/cass 包结构+1 文件×2/单元（包内 4→6 件）。
  - 风险与对策：f_sor/Ea/Δp 档位偏差传导全厂电耗±20% 量级——档位带
    注记在系数库、B4-2b 分列修正后收敛；p_total（ningjiao 搅拌）与
    n_pump_total（ts）等近似键名零冲突已 grep 实证（聚合键面仅白名单
    七键显式列举，无裸键面）。
- 参照：《裁决书》方案五②探针节；ADR-012 D1（总线稳定）；ADR-011 D1
  （批量同源向量路径——能耗公式经 _apply_batch/_apply 正门）；14f1efa
  （曝气头批锁面工序先例）；factors.yaml B4-2a 节（系数档真源）。
