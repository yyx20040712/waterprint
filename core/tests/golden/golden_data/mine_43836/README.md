# mine_43836 —— 矿井水 golden 案例（43,836 m³/d，地表水 III 类）

三件套（录入要求见 `docs/golden-cases.md`）：

1. `input_project.json`——**v2 全图 11 节点**（8 主线+污泥线 3，MSLUDGE2
   段二 2026-08-28：input→调节池→沉砂→凝聚→磁分离→高密→V 型滤池→
   紫外 + hebing→nongsuo→tuoshui 两链边；主线八节点空字典=manifest
   默认与旧源 kuangjing.ddesign.json 全一致；污泥三节点参数注入
   [hebing 12 键全键照录——三股干基/含水率六键+产率链六键矿井口径；
   nongsuo q_solid=60/t=16/h_eff=4/n=2/p_out=0.90 带外直值；tuoshui
   dose_pam=3/p_cake=0.75/n_standby=1 带式档]；**std.gb3838_iii 实绑**
   standard_binding={"effluent": "std.gb3838_iii"}——I1 从严口径
   绑定面承载，透传 calc 零消费）；**污泥回流 R 环路不在 v2**（sup/
   filtrate 回流口默认关边不连——矿井真环归 GOLDEN4，回路收敛验证场
   归市政回流案例 GOLDEN3）；
2. `expected_summary.json`——关键结果 42 锚（终水 10+11 单元主尺寸 30+
   m3 双锚 2——MSLUDGE2 M3 收口：显式分解替代"主尺寸 42 锚"压缩措辞）
   [v2 污泥三单元+10 项+m3 双锚 2 项——v1 30 锚位级零扰动；GOLDEN4a
   2026-08-28 serialize 三元组重录 106996/3125bebe1fa35546——42 数值
   锚零扰动程序化实证]；**五指标面=SS/CODCR/NH3N/TN/TP——BOD5 不建**
   [Ruling BOD5-不建：矿井水 B/C=0.025 无生化性]；m3_deferred 双锚
   [estimate_total=cost 三正门直调 11 节点全图/total_sludge=hebing
   ds_total]），每项标注来源与容差；
3. `notes.md`——原始设计资料口径注记（空字典默认声明/m³/d 口径/
   污泥线参数注入档与 s0_bod 推导式记档/警告面记档/追认点清单）。

> 录入状态：**已录入（AI 起草 2026-08-28 v1+待追认；v2 升版
> 2026-08-28——§21-③ 追认通过）**——期望值真源=主线实跑（v1
> HEAD `3b6fce2`/v2 HEAD `bcfbc60`），数值真源手算表
> `docs/norms/mine_water_sludge_line.md`（主算例 35 项对照 0 项超
> 1e-9）；追认点与口径注记见 `notes.md` §2/§3。
>
> 录入人：＿＿＿（领域专家）日期：＿＿＿；差异解释逐条附于 notes。
