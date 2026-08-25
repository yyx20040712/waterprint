# vxinglvchi 手算对照表（golden 期望值唯一来源）【已起草待追认】

> 状态：**已起草待追认**——数据策略 v2（工程常用范围口径，GB 国标 +
> 《给水排水设计手册》，见 AGENTS §14）；路线 = **均质滤料正常滤速
> 主线 + 强制滤速校核**（V 型滤池：恒水位均质滤料、气水反冲洗+表面
> 扫洗三阶段），分格数 ≥4（business-logic §7 离散档）。
> 本表数值出处仅标 GB 国标与《给水排水设计手册》两类，其余来源不标。

## 单元信息

- UNIT_ID：vxinglvchi（新系统身份 municipal/vxinglvchi）
- 中文名 / 业务线：V 型滤池（均质滤料、气水反冲洗）/ 市政污水处理
- 规范依据（主）：GB 50013-2018 §9.5（滤池：均质滤料滤速、强制滤速
  与气水反冲洗强度——具体小条号随 M2b2 实装逐条核对）；《给水排水
  设计手册》V 型滤池构造（长宽比/砂层/滤板/扫洗）常用值
- 流量口径：过滤面积与冲洗强度按**最高时设计流量**（含自用水系数）
  Q_filter = q_design_h × 1.05；冲洗耗水率按**平均日流量**复核
  （q_design_h = 2027.70 m³/h = 0.56325×3600，与 docs/norms 各表
  同源口径）

## 公式表（XL-F1~XL-F19，DSL 公式串供 FormulaSpec 直用）

> DSL 语法子集：`OUT = RHS`，算术 + 白名单函数 {min,max,abs,sqrt,log10}；
> 取整不入 DSL——离散化后的值（B、L）作为下游公式输入符号；
> ×3600/60 形态为小时-秒换算条文常量（与 M2a2 等价形态惯例一致）。

| formula_id | 表达式（受限 DSL） | 变量 | 系数列（factor.vxinglvchi.*） | 出处 |
|-----------|--------------------|------|-------------------------------|------|
| XL-F1 | `q_filter = q_design_h * selfuse_coef` | q_design_h 最高时流量 m³/h；selfuse_coef 自用水系数（反冲耗水补偿） | selfuse_coef | 给水排水设计手册（自用水常用） |
| XL-F2 | `a_total_req = q_filter / v_filter` | v_filter 正常滤速 m/h（主控参数） | v_filter_band.min/max | GB 50013-2018 §9.5 |
| XL-F3 | `a_cell = a_total_req / n` | n 分格数（≥4，离散档位 business-logic §7） | — | GB 50013-2018 §9.5 |
| XL-F4 | `b_raw = sqrt(a_cell / ratio_lb)` | ratio_lb 单格长宽比（b_raw 按 0.5 m 档向上取整得 B） | cell_ratio_lb_band.min/max | 给水排水设计手册（V 型滤池单格工程常用） |
| XL-F5 | `l_raw = a_cell / B` | l_raw 格长（按 0.5 m 档向上取整得 L） | — | 同上 |
| XL-F6 | `a_cell_act = B * L` | 单格实取过滤面积 m² | — | 同上 |
| XL-F7 | `a_total_act = a_cell_act * n` | 全池实取过滤面积 m² | — | 同上 |
| XL-F8 | `v_filter_act = q_filter / a_total_act` | 实际正常滤速校核 | v_filter_band.min/max | GB 50013-2018 §9.5 |
| XL-F9 | `v_forced_act = q_filter / (a_total_act - a_cell_act)` | 一格冲洗时强制滤速校核（≤11~13） | v_forced_band.min/max | GB 50013-2018 §9.5（强制滤速） |
| XL-F10 | `q_air = a_cell_act * w_air / 1000` | w_air 气冲强度 L/(m²·s)（单格） | wash.air | GB 50013-2018 §9.5；给水排水设计手册 |
| XL-F11 | `q_wash_sim = a_cell_act * w_water_sim / 1000` | w_water_sim 气水同时冲洗水强度 | wash.water_sim | 给水排水设计手册（V 滤三阶段） |
| XL-F12 | `q_wash = a_cell_act * w_water / 1000` | w_water 单独水冲（漂洗）强度 | wash.water | GB 50013-2018 §9.5；给水排水设计手册 |
| XL-F13 | `q_sweep = a_cell_act * w_sweep / 1000` | w_sweep 表面扫洗强度（V 型槽进水扫洗） | wash.sweep | 给水排水设计手册（V 滤特色工法） |
| XL-F14 | `v_air_per = q_air * (t_air + t_sim) * 60` | t_air/t_sim 气冲/气水同时历时 min（单格次耗气 m³） | wash.t_air；wash.t_sim | GB 50013-2018 §9.5 |
| XL-F15 | `v_wash_per = (q_wash_sim * t_sim + q_wash * t_water + q_sweep * (t_air + t_sim + t_water)) * 60` | t_water 水冲历时 min（单格次耗水 m³） | wash.t_water | 同上 |
| XL-F16 | `v_wash_daily = v_wash_per * n * 24 / t_cycle` | t_cycle 过滤周期 h | cycle_band.min/max | 给水排水设计手册 |
| XL-F17 | `ratio_wash = v_wash_daily / q_avg_daily` | 反冲耗水率校核（≤5%，被 selfuse_coef 覆盖） | — | 给水排水设计手册 |
| XL-F18 | `h_total = h_super + h_water_above + h_sand + h_bottom` | h_water_above 砂上水深/h_sand 砂层厚/h_bottom 滤板气水区高 | superheight；media.depth_band；water_above_band | 给水排水设计手册（V 滤池深组成） |
| XL-F19 | `v_concrete = a_total_act * h_total * wall_coef` | 概算口径混凝土量 | wall_thickness_coef | 给水排水设计手册（概算口径） |

其他数据键：factor.vxinglvchi.elevation_loss（高程链经验水损，
含滤层过滤水头，语义异于沉淀类单元）；去除率键
removal.vxinglvchi.{bod5,cod,ss}.mod_default（见衔接式）。

## 参数档（工程常用范围，出处两类）

| 参数 | 键 | 取值/带 | 主算例取值 | 出处 |
|------|----|---------|-----------|------|
| 正常滤速 v | v_filter_band | 7~10 m/h | 8.0 | GB 50013-2018 §9.5 |
| 强制滤速 v_f（校核带） | v_forced_band | 11~13 m/h | 计算 9.4626 | GB 50013-2018 §9.5 |
| 自用水系数 | selfuse_coef | 1.05~1.10（取 1.05） | 1.05 | 给水排水设计手册（工程常用） |
| 单格长宽比 L/B | cell_ratio_lb_band | 2.0~3.0（取 2.5） | 2.5 | 给水排水设计手册（V 滤单格工程常用） |
| 砂层厚度 | media.depth_band | 1.2~1.5 m | 1.3 | GB 50013-2018 §9.5（均质滤料） |
| 均质滤料 d10 | media.d10_band | 0.9~1.2（取 1.0）mm | 1.0 | GB 50013-2018 §9.5；给水排水设计手册 |
| 砂上水深 | water_above_band | 1.2~1.5（取 1.3）m | 1.3 | 给水排水设计手册（恒水位过滤） |
| 超高 h_super | superheight | 0.3 m | 0.3 | GB 50013-2018 §9.5；给水排水设计手册 |
| 气冲强度 | wash.air | 13~17（取 15）L/(m²·s) | 15 | GB 50013-2018 §9.5；给水排水设计手册 |
| 气水同时水强度 | wash.water_sim | 2~3（取 2.5）L/(m²·s) | 2.5 | 给水排水设计手册（V 滤三阶段） |
| 水冲强度 | wash.water | 4~6（取 5）L/(m²·s) | 5 | GB 50013-2018 §9.5；给水排水设计手册 |
| 表面扫洗强度 | wash.sweep | 1.4~2.3（取 1.8）L/(m²·s) | 1.8 | 给水排水设计手册（V 滤特色工法） |
| 气冲历时 | wash.t_air | 1~3（取 2）min | 2 | 给水排水设计手册 |
| 气水同时历时 | wash.t_sim | 3~5（取 4）min | 4 | 给水排水设计手册 |
| 水冲历时 | wash.t_water | 3~6（取 4）min | 4 | 给水排水设计手册 |
| 过滤周期 | cycle_band | 24~48（取 24）h | 24 | 给水排水设计手册（V 滤长周期） |
| 壁厚系数（概算） | wall_thickness_coef | 0.30~0.40（取 0.35） | 0.35 | 给水排水设计手册（概算口径） |
| 高程水损 | elevation_loss | 2.0~3.0（取保守 2.5）m | 2.5 | 给水排水设计手册（含滤层过滤水头，工程常用） |
| SS 去除率 η | removal.vxinglvchi.ss | 60%~75%（中值 0.675） | 0.675 | 给水排水设计手册（深层过滤常用带） |
| BOD5 去除率 | removal.vxinglvchi.bod5 | 5%~10%（中值 0.075，颗粒态随 SS 带出） | 0.075 | 给水排水设计手册（工程常用保守档） |
| COD 去除率 | removal.vxinglvchi.cod | 5%~10%（中值 0.075） | 0.075 | 给水排水设计手册（工程常用保守档） |

构造参数（分格数 n=6 ≥4、滤板/长柄滤头气水区高 1.0 m、V 型进水槽
双侧进水+中央排水渠）为单元 manifest 声明面默认值（工程常用构造，
出处给水排水设计手册）；均质滤料不设砾石承托层（滤板+长柄滤头
直接支撑，K80 ≤1.4~1.6 均匀性注记）。

## 水质衔接式（全厂去除链，上游 = 高密沉淀池表出流）

- 入流（gaomidu 表出流链值）：BOD5_in = **5.918378 mg/L**、
  COD_in = **17.84431 mg/L**、SS_in = **0.6990908 mg/L**
  （满足进水 SS <20 mg/L 联动承诺，business-logic §5 链 1）
- 出流（衔接下游 ziwai 表 = 全厂终水）：BOD5_out = 5.918378×(1−0.075)
  = **5.474500 mg/L**（≤10 一级 A 合格）；COD_out = 17.84431×
  (1−0.075) = **16.50599 mg/L**（≤50 合格）；SS_out = 0.6990908×
  (1−0.675) = **0.2272045 mg/L**（≤10 合格）
- NH3N/TN/TP 穿流不变（无去除键）
- 语义注记：深度处理段链入流 SS 已低于 5 mg/L，过滤去除的绝对量
  小、出水值极低属链式口径客观呈现（专家抽验面）

## 手算主算例（golden 全厂口径，未来 test_compute.py 期望值来源）

输入：q_design_h = 2027.70 m³/h、Q_avg_daily = 34760.7 m³/d、
selfuse_coef = 1.05、v_filter = 8.0 m/h、n = 6、ratio_lb = 2.5、
w_air = 15、w_water_sim = 2.5、w_water = 5、w_sweep = 1.8 L/(m²·s)、
t_air = 2、t_sim = 4、t_water = 4 min、t_cycle = 24 h、h_super = 0.3、
h_water_above = 1.3、h_sand = 1.3、h_bottom = 1.0 m、wall_coef = 0.35。

| 量 | 手算过程摘要 | 期望值 |
|----|--------------|--------|
| q_filter（XL-F1） | 2027.70×1.05 | **2129.085 m³/h** |
| a_total_req（XL-F2） | 2129.085/8.0 | **266.1356 m²** |
| a_cell（XL-F3） | 266.135625/6 | **44.35594 m²** |
| b_raw（XL-F4） | √(44.35594/2.5) = 4.212170 → 0.5 m 档取整 | B = **4.5 m** |
| l_raw（XL-F5） | 44.3559375/4.5 → 0.5 m 档取整 | L = **10.0 m** |
| a_cell_act（XL-F6） | 4.5×10.0 | **45.0 m²** |
| a_total_act（XL-F7） | 45.0×6 | **270.0 m²** |
| v_filter_act（XL-F8） | 2129.085/270.0（带 7~10 内，合格） | **7.88550 m/h** |
| v_forced_act（XL-F9） | 2129.085/(270−45)（≤11 合格） | **9.46260 m/h** |
| q_air（XL-F10） | 45×15/1000（单格） | **0.675 m³/s** |
| q_wash_sim（XL-F11） | 45×2.5/1000 | **0.1125 m³/s** |
| q_wash（XL-F12） | 45×5/1000 | **0.225 m³/s** |
| q_sweep（XL-F13） | 45×1.8/1000 | **0.081 m³/s** |
| v_air_per（XL-F14） | 0.675×(2+4)×60（单格次） | **243.0 m³** |
| v_wash_per（XL-F15） | (0.1125×4+0.225×4+0.081×10)×60 | **129.6 m³** |
| v_wash_daily（XL-F16） | 129.6×6×24/24 | **777.6 m³/d** |
| ratio_wash（XL-F17） | 777.6/34760.7（2.24% ≤5%，合格） | **0.02237009** |
| h_total（XL-F18） | 0.3+1.3+1.3+1.0 | **3.9 m** |
| v_concrete（XL-F19） | 270.0×3.9×0.35 | **368.55 m³**（概算口径） |

## 签字

- 实现者（摘录 + 手算）：AI-GLM5.3 起草 2026-08-25（数据策略 v2，工程常用范围口径）
- 领域专家追认（签字/日期）：＿＿＿
