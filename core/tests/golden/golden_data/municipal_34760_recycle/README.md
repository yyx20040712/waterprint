# municipal_34760_recycle —— 市政回流 golden 案例（34,760 m³/d+上清液/滤液回流）

三件套（录入要求见 `docs/golden-cases.md`；GOLDEN3 D5 起草 2026-08-28）：

1. `input_project.json`——主线 19 节点（=municipal_34760 基例：水线 12+
   污泥链 7）+2 `recycle_junction` 转换节点（rj_sup/rj_filtrate，节点值
   恰 `{"kind": "recycle_junction"}` 单键）+17+4 边——回流边四条全部
   **forward（不带 recycle 键）**：nongsuo.sup→rj_sup.in、rj_sup.out→
   污水提升泵房.in、tuoshui.filtrate→rj_filtrate.in、rj_filtrate.out→
   同 dst（v1 前向叠加口径——D0 定调：市政图水线/污泥线不连通，回流
   边为跨子图前向边，全图仍 DAG；环不闭合时回流边禁标 recycle，
   executor 组外拒）。checked_units 承载于 expected（市政先例 §2.2）；
   standard_binding={} 同先例；
2. `expected_summary.json`——92 锚（effluent 六指标×5 工况 30+20 单元
   主尺寸 60+m3 双锚 2），每项标注来源与容差；真源=app 正门一次实跑
   落盘（HEAD `74c30e4`，禁手打）；
3. `notes.md`——回流口径注记（前向叠加/kz=1/SS-only 投影/水量平衡
   守恒/追认点清单）。

> 录入状态：**已录入（AI 起草 2026-08-28，待追认）**——三件套齐
> （GOLDEN3 批，BASE `6b86194` 起草）；期望值真源=主线实跑，追认点与
> 口径注记见 `notes.md` §2/§3。
>
> 录入人：＿＿＿（领域专家）日期：＿＿＿；差异解释逐条附于 notes。
