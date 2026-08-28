# mine_43836 —— 矿井水 golden 案例（43,836 m³/d，地表水 III 类）

三件套（录入要求见 `docs/golden-cases.md`）：

1. `input_project.json`——**v1 主线 8 节点** design 态（GOLDEN2 段一，
   2026-08-28：input→调节池→沉砂→凝聚→磁分离→高密→V 型滤池→紫外；
   节点全空字典=manifest 默认与旧源 kuangjing.ddesign.json 全一致）；
   **污泥线/污泥回流 R 环路不在 v1**——矿井污泥链手算表未备，升版归
   后续批（原"含污泥回流 R 环路"承诺面就此改写记档，回路收敛验证场
   归市政回流案例 GOLDEN3）；
2. `expected_summary.json`——关键结果期望值（2 工况终水五指标+
   8 单元主尺寸 30 锚；**五指标面=SS/CODCR/NH3N/TN/TP——BOD5 不建**
   [Ruling BOD5-不建：矿井水 B/C=0.025 无生化性]；无 m3_deferred 键
   ——概算/泥量随污泥链升版补录），每项标注来源与容差；
3. `notes.md`——原始设计资料口径注记（空字典默认声明/m³/d 口径/
   追认点清单）。

> 录入状态：**已录入（AI 起草 2026-08-28，待追认）**——v1 三件套齐
> （GOLDEN2 批，HEAD `3b6fce2` 起草）；期望值真源=主线实跑，追认点
> 与口径注记见 `notes.md` §2/§3。
>
> 录入人：＿＿＿（领域专家）日期：＿＿＿；差异解释逐条附于 notes。
