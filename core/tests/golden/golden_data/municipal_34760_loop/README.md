# municipal_34760_loop —— 市政真环 golden 案例（34,760 m³/d+产泥真边+真回流 SCC）

四件套（录入要求见 `docs/golden-cases.md`；GOLDEN4b D1~D5 起草 2026-08-28）：

1. `input_project.json`——主线 19 节点（=municipal_34760 基例：水线 12+
   污泥链 7）+2 `recycle_junction` 转换节点+17+7 边（24 边）：**3 产泥
   真边 forward**（chuchenchi/aao/gaomidu 的 sludge_out→hebing 三 IN 口
   [in_primary/in_bio/in_chem]——GOLDEN4a 双模的入流直值模式激活，hebing
   节点值收缩为产率链六键：q_avg_daily/s0_bod/se_bod/v_bio/x_vss/
   t_design，ds/p 六键撤出由真边供）+**回流链 2+2**（nongsuo.sup→
   rj_sup.in、tuoshui.filtrate→rj_filtrate.in 两边 **recycle=true**；
   rj_sup.out/rj_filtrate.out→污水提升泵房.in 两边 forward——D1 原四边
   全 recycle 触 executor 冻结覆盖式语义[recycle 股按 dst 覆盖不参与
   propagate 合并]使 inlet 前向入流被清零，记档 notes §2.1）。全图成
   **16 节点大 SCC**（水线提升泵房→…→gaomidu+泥线 hebing→…→tuoshui+
   rj×2），solve_loop 阻尼迭代收敛（16 步/工况）。checked_units 承载于
   expected（市政先例 §2.2）；standard_binding={} 同先例；
2. `expected_summary.json`——92 锚（effluent 六指标×5 工况 30+20 单元
   主尺寸 60+m3 双锚 2），每项标注来源与容差；真源=app 正门一次实跑
   落盘（HEAD `a2c51bb`，禁手打；生成脚本经 stdin 实跑零落盘）；
3. `notes.md`——真环口径注记（2+2 校正/墙 A~C 记档/收敛实录/迁移对照
   /summary 空映射/追认点清单）。

> 录入状态：**已录入（AI 起草 2026-08-28，待追认）**——四件套齐
> （GOLDEN4b 批，BASE `8f87de6` 起草+R1 修复笔序 25735ac/a2c51bb）；
> 期望值真源=主线实跑，追认点与口径注记见 `notes.md` §2/§3。
>
> 录入人：＿＿＿（领域专家）日期：＿＿＿；差异解释逐条附于 notes。
