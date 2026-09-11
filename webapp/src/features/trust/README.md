# trust —— 结果可信度视图

结果可信度报告面板（消费 GET /api/calc/trust 响应——P2 次批 ADR-012
D8：回路收敛统计/水量平衡闭合审计/出水达标裕度/校核警告汇总四件套，
全工况聚合）。

## 文件清单（P2 次批实装 2026-09-12）

| 文件 | 职责 | 状态 |
|------|------|------|
| `lib/trustView.ts` | 纯函数层：narrowTrustResponse 窄化门（顶层 13 键+四条目族键域逐项校验，非法抛 TrustViewError）+marginTone/marginText 裕度语义（正绿负红——SolutionsTable 同纪律）+severityTone（PumpStationsPanel 同映射）+formatSci/formatFlow/formatRel 数值格式化+fluidLabel/loopParamLabel 中文标签词典 | P2 次批实装 |
| `lib/trustView.test.ts` | 投影层纯函数 vitest（窄化正负例族+语义色/格式化对照） | P2 次批实装 |
| `api/useTrustQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/calc/trust/${projectId}']+select 窄化收口（useCostQuery 同构先例；全工况聚合无工况参数） | P2 次批实装 |
| `components/TrustReportView.tsx` | 报告主体（纯展示薄壳）：状态条（stale 黄条+降级蓝条+溯源小字）+四区块卡（收敛口径/水量平衡含泥线减量注记/出水裕度 GB 18918 参考面/警告汇总分级 Tag） | P2 次批实装（薄壳不测） |

## 规格要点（P2 次批实况）

- 数据全部来自服务端（GET /api/calc/trust：latest done calc 全工况聚合
  ——诊断件 calc-diag-{task_id}.json[core ADR-012 独立并列 artifact]+
  PlantResult 警告总线聚合）；
- 降级语义（ADR-012 R1）：旧结果无诊断件=diagnostics_available=false
  蓝条提示重算——"已算但无数据"与"未算"显式区分，禁伪造空诊断冒充；
- 警告面恒给（PlantResult 总线自有——旧结果也有）；
- 刷新联动：TASK_EVENT 事件桥（第五处监听）invalidate 键；
- 工艺性注记：泥线浓缩/消化/脱水/干化单元水量变化=工艺减量非数值
  错误（BalanceCard 文案注记）。
