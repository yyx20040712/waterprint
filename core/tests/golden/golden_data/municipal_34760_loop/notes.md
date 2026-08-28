# municipal_34760_loop · notes（真环口径注记与追认清单）

> 录入形态：AI 起草 + 领域专家追认制 v2（宪法 §14 数据策略 v2 /
> pending-domain-expert.md §7）。起草：2026-08-28（GOLDEN4b 批，
> BASE `8f87de6`；R1 修复笔序 HEAD `25735ac`→`a2c51bb`）。

## 1. 来源说明

- 本案例=municipal_34760_recycle 基础上真环化：+3 产泥真边（forward）
  接通 hebing 三 IN 口+回流链 2+2（sup/filtrate 两边 recycle=true+rj
  两出边 forward），hebing 节点值收缩为产率链六键（ds/p 撤出——三股
  由真边供，GOLDEN4a 入流直值模式）；输入经 `app.load_project` 装载
  基例→改 design→`design_hash` 重算→`save_project` 确定性落盘；
  期望值=该文件经 `load_project → build_condition_set → run_full_calc`
  一次实跑落盘（生成脚本经 stdin 实跑零落盘，实录见实现报告；
  禁手打数值纪律）。
- metadata 实录：`engine_version="waterprint-server 0.1.0"`、
  `data_version="coefficients@1.1.0+unit_prices@1.0.0"`、content_hash=
  `46fab80ce6028dea50dc7fb6004371bdaebfacd8c94c0fe98defd91f0f730a4f`
  （design_hash 正门回填，与运行 repro 逐字同）。
- **真环收敛实录（D2 预判兑现）**：16 节点 SCC 组逐工况 solve_loop
  **16 步收敛**（阻尼 0.8/容差 1e-10/上限 200；计数探针实录
  [16,16,16,16,16]——<20 步预判成立、<100 步停手线远未触及）；
  收敛元数据机器锚=serialize trace 面逐工况 NS-F9 迹节点数 17
  （16 迭代+1 收敛解终跑——e2e ④ 断言）。

## 2. 口径注记

1. **回流链 2+2 校正（D1 偏离记档——呈报总控）**：D1 预裁四条回流边
   全 recycle=true；实证全 recycle 形态触 executor 冻结语义**墙 C**：
   `_inflows` 回流股按 dst **覆盖式赋值不参与 propagate 合并**（图机制
   冻结报告 §B 在册）——提升泵房 in 口同时收 inlet 前向股与两条 rj
   recycle 股，后者覆盖前者，inlet 流量被清零→首迭代 TS-F2 除零拒
   （InvalidFormulaError 实录）。本案例取 **sup/filtrate 两边
   recycle=true**（真环迭代面：SCC/solve_loop/状态变量[SLUDGE 三量×2
   =6 变量]全保）+**rj 两出边 forward**（合并面：inlet+rj_sup.out+
   rj_filtrate.out 三股经 propagate 正确合并 q=Σ/kz=max/负荷加权——
   与 v1 合并语义全同）。21 节点 24 边拓扑与 D1 全同，仅 recycle
   标记语义校正；D2 预判的"4 边流股展开 10 变量"相应收窄为 6 变量
   （rj 出边 forward 不入状态——dst 口 WATER 两量×2 由前向传播承载）。
2. **机制修复前提（GOLDEN4b R1 裁决，commit `25735ac`）**：本案例真环
   依赖 executor 两修复——SCC 组调度占最浅成员层（原最深成员层使水线
   尾 vxinglvchi 在组求解前消费 gaomidu 读空池 KeyError——墙 A）+
   SLUDGE 回路初值 q_wet=1e-6（原零值触 rj GR-14 域守卫首迭代即拒
   ——墙 B）；tests/graph 两墙锁定用例随笔序 ⑥ 入锁。DAG 路径逐字节
   不变（三案例 serialize/锚零扰动实证）。
3. **锚迁移实况（D3 预告的机器实证+预告差呈报）**：hebing 入流直值
   模式下三股干基=产泥口实跑值且回流 SS 真进水线逐级传播——收敛解
   ds_total=**5769.677599093755**（vs v1 前向叠加 5306.515，
   **+8.728188%**）、q_total=**427.3594991344455**（+4.402958%）、
   终水 SS design=**0.252524315**/avg=**0.257884314**（v1：
   0.251417/0.256064——回流增益方向）。**预告差**：4a-final N-1 预告
   +3.862%/+1.972% 系**单程真边**口径（CC-F10 实跑 3417.846 替代注入
   3240.12 一次传播）；真环为迭代收敛固定点，回流 SS 逐级放大二阶
   效应使迁移量高于单程预告（ds 比值 1.0873>预告下界 1.03862——
   e2e ③ 方向断言机证）。本批锚全照实跑录（简报 §5 已裁）。
4. **水量真闭合锚（逐工况）**：bashi 出流 q=inlet(0.4023229167)+该工况
   q_sup/86400+q_filtrate/86400（design 档闭合差 1.79e-13——阻尼迭代
   有限精度下 v1 位级口径放松至 <2e-13 容差带，e2e ② rel=1e-12/
   abs=1e-11 断言；各工况回流量不同[design 297.542+112.435 m³/d，
   avg 工况更大]——断言用**该工况** nongsuo/tuoshui dims，v1 跨工况
   共用 design 值的口径在真环下不成立）。
5. **hebing 双模入流直值面**：formula_ids=F4~F13 收窄集（F1~F3 不重算
   ——入流即真值；GOLDEN4a 审计口径）；dims 13 键两模式同名同义，
   三股 q 直值回显（q_primary=91.092/q_bio=328.525/q_chem=7.743——
   产泥口实跑值，ds 面 CC-F10/AO-F6/GM-F12 链）。
6. **summary 空映射注记**：真环调度（组占最浅成员层）下泥线汇点
   ganhua（非组成员，层 15）后于水线 bashi（层 11）完成——app
   `_summary_of` terminal 启发式（快照序末位无出边单元）取 ganhua，
   无水质键→**空映射**（契约原文"污泥线终端无水质键→空映射合法"；
   v1 因 rj 前向边使水线被推深层、bashi 恰居末——真环形态下启发式
   如实取泥线汇点，非缺陷非回归；终水六指标面由 effluent 锚承载，
   e2e 断言空映射+注记）。
7. **serialize 面（真环迹实录）**：5,717,264 bytes、sha256 头
   `8190d567dfb5c92d`（双跑字节同）——迹面 16,820 节点=逐工况全迭代
   的公式应用全录（16 迭代×~16 单元×~10 式+终跑+DAG 段），较 v1
   504,396 膨胀约 11 倍（迭代迹入 serialize——收敛元数据可观测的
   机制基础，见 §1 收敛实录）；e2e ⑥ 字节长+sha 双锚。
8. **checked_units 勾选**：复用市政三单元（初沉/AAO/二沉——5 工况面
   与基例同；真环下 offline 工况收敛解与 design 全同——offline 映射
   面在环路内的固定点不变，实录）。
9. **m3 双锚**：estimate_total=**12,086,496.936647924** 元（21 节点
   design 档 cost 三正门直调——真环使水线工程量随回流量微增重算）；
   total_sludge=**5769.677599093755** kg/d（hebing ds_total 真边实跑
   口径——与 v1 5306.515 的差=锚迁移 §3）。
10. **容差口径**：rel=1e-12/abs=1e-12 双容差（市政先例红线同款；
    水量真闭合锚单独 rel=1e-12/abs=1e-11——阻尼迭代有限精度注记 §4）。

## 3. 追认点清单（待领域专家批量追认）

1. **期望值整体**（92 项数值）——真源=主线实跑 2026-08-28
   HEAD=`a2c51bb`，AI 起草待追认。
2. **回流链 2+2 校正口径**（§2.1——D1 全 recycle 偏离；机制语义
   记档在案，图形态裁量待追认）。
3. **真环锚迁移实况**（§2.3——预告差+8.73% vs +3.86%，二阶效应
   口径待追认）。
4. **summary 空映射**（§2.6——terminal 启发式在真环形态下的取值）。
5. **kz=1 工程裁量/SS-only 投影/moisture 干基近似**（承 GOLDEN3
   v1 追认点 3/4/5 同面）。
6. **主控项选取裁量**（承 v1 §2.8——18 主线沿用+rj 两键+hebing 三键
   实跑新值）。
7. **概算基数变化**（§2.9——21 节点真环 vs v1 21 节点前向叠加金数
   各自成立）。

## 4. 差异记档位（未来回归差异逐条附此）

| 日期 | 批次/commit | 差异项 | 原因与处置 |
|------|-------------|--------|------------|
| 2026-08-28 | GOLDEN4b（真环案例起草） | ds_total 5769.678 ≠ v1 5306.515（+8.728%） | 真边三股实跑值替代手算表注入值（+3.86% 单程）+回流 SS 逐级传播迭代收敛二阶效应（+4.87%）——固定点口径（§2.3 预告差呈报） |
| 2026-08-28 | GOLDEN4b（真环案例起草） | 终水 SS 0.252524 ≠ v1 0.251417 mg/L（design 档） | 回流 SS 增益方向（真环迭代固定点）；BOD5/CODCR/NH3N/TN/TP 与 v1 量级同链（真边不改去除率族——回流股仍只带 SS） |
| 2026-08-28 | GOLDEN4b（真环案例起草） | D1 四回流边全 recycle=true → 2+2 | 墙 C：recycle 股覆盖式赋值语义使 inlet 被清零（TS-F2 除零实录）——真环迭代面全保（§2.1） |
| （待续） | | | |

## 5. 录入人签字栏

- 起草（AI）：＿＿＿（GOLDEN4b 批实现者，2026-08-28）
- 追认（领域专家）：＿＿＿ 日期：＿＿＿
