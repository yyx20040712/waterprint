# municipal_34760_recycle · notes（回流口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-28（GOLDEN3 批，
> BASE `6b86194`，HEAD `74c30e4`）。

## 1. 来源说明

- 本案例=municipal_34760 基例（19 节点）+回流扩展（2 转换节点+4 边），
  输入经 `app.load_project` 装载基例→改 design→`design_hash` 重算→
  `save_project` 确定性落盘（往返字节同自证）；期望值=该文件经
  `load_project → build_condition_set → run_full_calc` 一次实跑落盘
  （生成脚本实录见实现报告；脚本用后已删，禁手打数值纪律）。
- 首跑探针零异常（D3b 前瞻解除）：21 节点 Kahn 分层跨子图回流边无
  异常，执行序 bashi 仍居末位（terminal 口径不变），summary 六指标
  全录。
- metadata 实录：`engine_version="waterprint-server 0.1.0"`、
  `data_version="coefficients@1.1.0+unit_prices@1.0.0"`（生成日库
  实拍——std.gb3838_iii 五键批后）、content_hash=`5d80cf03…6e971`
  （design_hash 正门回填，与运行 repro 逐字同）。

## 2. 口径注记

1. **回流拓扑（D0 定调——v1 前向叠加口径）**：市政图水线/污泥线
   不连通（hebing 图源参数注入、水线单元无 SLUDGE 排泥口），回流
   边 sup/filtrate→转换→污水提升泵房为**跨子图 forward 边**（全图
   仍 DAG，无 solve_loop 迭代，一次传播）；边不带 recycle 键
   （executor 373-377：不闭合回路的 recycle 标记=装配异常拒）。
   真环迭代（hebing 实体化+水线产泥口+solve_loop）挂账 GOLDEN4。
2. **转换节点（D1）**：rj_sup/rj_filtrate 为 builtin
   recycle_junction（in SLUDGE/out WATER 单入转换）：出流
   WaterFlow(q_avg_daily=q_wet, kz=1.0)——回流为连续均匀流无峰化
   （工程裁量 I2 追认）；出水质只投 SS=ds/q_wet×1000 mg/L（其余
   指标由 propagate 部分缺项语义=进水原值——回流股无 BOD5/CODCR/
   NH3N/TN/TP 键，mix 在场股加权自然缺项）；dims 两键 q_recycle
   （m³/d 工程口径回显）/ss_recycle（mg/L）。
3. **水量平衡守恒（business-logic §3）**：bashi 出流
   q_avg_daily == inlet(0.4023229167) + q_sup/86400 + q_filtrate/
   86400（0.4068755652828162 m³/s——逐工况断言，实跑位级相等）；
   汇流在污水提升泵房 in 口由 propagate 多股合并（q_avg=Σ、
   kz=max[1.4 vs 1.0→1.4]）。
4. **回流对水质的影响面（实跑实录）**：design 档终水 SS
   0.239667→0.251417 mg/L（回流 SS 负荷 1830.21/1633.77 mg/L 两股
   加权）；BOD5/CODCR/NH3N/TN/TP 与基例逐值同（SS-only 投影——
   回流股只带 SS，其余指标缺项=inlet 原值，下游去除链入流浓度
   不变）。
5. **checked_units 勾选**：复用市政三单元（初沉/AAO/二沉——5 工况
   面与基例同）；承载位置=expected_summary 顶层（design 留空——
   市政先例 §2.2 负向实录口径）。
6. **m3 双锚**：estimate_total=11,966,361.336578732 元（21 节点
   design 档 cost 三正门直调——水线 dims 微变[泵房 q_in 增]使
   概算重算，与基例 11,908,574.595 差 +57,786.74 元记 §4）；
   total_sludge=5306.514999999999 kg/d（hebing ds_total——污泥
   主线参数不变复核与基例逐位同）。
7. **容差口径**：rel=1e-12/abs=1e-12 双容差（市政先例红线同款）；
   serialize 双跑字节同，入 generated 块——e2e ⑥ 机器锚定。印记链：
   GOLDEN3 起草 502281 bytes/212f3621990b5414 → **GOLDEN4a 复录
   （2026-08-28，HEAD=`fe4e1a7`）**：三单元 sludge_out 产股三键×5
   工况入快照——504396 bytes/ba1691c1dc97dd6a（92 锚零扰动）→
   **GOLDEN4b 复核（2026-08-28，HEAD=`25735ac`）**：MS-F1~F3 登记
   落矿井产泥包（本案例不涉）+executor 真环两机制修复（DAG 零扰动）
   ——504396/ba1691c1dc97dd6a 持平复核（真环姊妹案例
   municipal_34760_loop 见 GOLDEN4b ⑧ 批）。
8. **主控项选取**：18 主线单元沿用 municipal_34760 同字段主控项
   （值随回流微变重录）；rj 两节点=q_recycle/ss_recycle 各 2 键。

## 3. 追认点清单（待领域专家批量追认）

1. **期望值整体**（92 项数值）——真源=主线实跑 2026-08-28
   HEAD=74c30e4，AI 起草待追认。
2. **回流 v1 前向叠加口径**（§2.1——真环迭代挂账 GOLDEN4；市政先例
   notes §3.7.d 同面追认）。
3. **kz=1 工程裁量**（§2.2——回流连续均匀流无峰化）。
4. **SS-only 投影**（§2.2/§2.4——其余指标=进水原值的部分缺项语义）。
5. **moisture 干基近似**（sup/filtrate 股含水率反解——市政先例
   notes §3.7.a 同面追认）。
6. **主控项选取裁量**（§2.8——rj 两键+18 主线沿用）。
7. **概算基数变化**（§2.6/§4——21 节点 vs 19 节点金数各自成立）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-08-28 | GOLDEN3（回流案例起草） | estimate_total=11966361.336578732 ≠ 基例 11908574.59503396 | 概算基数 19→21 节点：回流使污水提升泵房 q_in 增 0.004553 m³/s，水线相关工程量微变重算（+57,786.74 元）；两金数各自成立（图不同非回归） |
| 2026-08-28 | GOLDEN3（回流案例起草） | 终水 SS 0.251417 ≠ 基例 0.239667 mg/L | 回流 SS 负荷入汇流（设计意图——回流 SS 投影生效的实证锚）；其余五指标逐值同基例（SS-only 投影） |
| （待续） | | | |

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN3 批实现者，2026-08-28）
- 追认（领域专家）：＿＿＿ 日期：＿＿＿
