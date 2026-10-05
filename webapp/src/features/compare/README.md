# compare —— 多工况对比与工况校核

多工况对比与工况校核视图（消费 GET /api/calc/compare/{project_id} 响应
——latest done calc 全工况聚合投影）。双页=对比矩阵（指标×工况矩阵+警告
计数）+工况校核（受检单元集合）；溯源=P2 第三批 ADR-018 D1/D3/D4/D5+
工况面 UX 反馈批 2026-09-12 件 1/件 2。

## 文件清单（P2 第三批 ADR-018 实装 2026-09-12）

| 文件 | 职责 | 状态 |
|------|------|------|
| `lib/compareView.ts` | 纯函数层：narrowCompareResponse 窄化门（顶层 9 键+指标/警告条目键域逐项校验，非法抛 CompareViewError）+锁定基准三件 pinOf/isPinStale/filterLivePins（D3 语义）+metricRowKey/metricLabel/rowExtremes/formatMetricValue 矩阵行模型与数值格式化（D1）；零运行期库 import | P2 第三批实装 |
| `lib/compareView.test.ts` | 投影层纯函数 vitest（窄化正负例族+锁定判定+行模型/格式化对照） | P2 第三批实装 |
| `lib/checkedUnits.ts` | 工况校核勾选纯函数层：checkableUnits 可勾全集（design.nodes 键减内置四 kind，字典序）/restoreCheckedKeys 恢复投影（幽灵勾选过滤）/withCheckedUnits PUT 载荷构造（仅替换 design.checked_units——CP2 样板同构） | P2 第三批实装 |
| `lib/checkedUnits.test.ts` | 三函数正负例 vitest（内置排除/幽灵过滤/结构化替换/异形拒） | P2 第三批实装 |
| `api/useCompareQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/calc/compare/${projectId}']+select 窄化收口（projectId=null 禁用不取数——useTrustQuery 同构先例） | P2 第三批实装 |
| `components/CompareMatrix.tsx` | 指标矩阵表+警告计数表：行=单元×out_dims 字段、列=工况（行内 max 加粗/min 下划线差异标注——全等行零标注）；pinned 键 ★ 标+失效键灰显「已移除」；工况列头/单元列中文化（conditionLabel/unitNameIndex） | P2 第三批实装 |
| `components/CompareMatrix.test.tsx` | 矩阵失效列头呈现 vitest（SSR renderToString 零 jsdom——HC25-F4 可达面；灰显令牌断言锚=UF-64 承接批联动面） | P2 第三批实装 |
| `components/CheckedUnitsPanel.tsx` | 工况校核集合面板：标题行「受检 k 单元 → 计算工况 2+k 档」运行代价提示（ADR-007 线性口径）+勾选即 PUT（withCheckedUnits 结构化替换——CP2 持久化样板；onError 回滚+domainGate 码表门控分级 toast） | P2 第三批实装 |
| `components/CheckedUnitsPanel.test.tsx` | 面板 onError toast 码表门控源文断言 vitest（domainGate 双码+锁冲突优先接线——纯读源零渲染） | P2 第三批实装 |

## 规格要点（P2 第三批实况）

- 数据全部来自服务端聚合（server services/compare：latest done calc
  指标×工况矩阵+警告计数+stale+design_hash 回显——FE 侧窄化+呈现，
  聚合零参与）；
- app 层装配=app/comparePane.tsx：Segmented 双页[对比矩阵|工况校核]
  （ParamTabs 制式）；锁定基准 view.compare={pinned,pinned_hash} PUT
  （视图态——不触发重算）；TASK_EVENT 第六处监听 invalidate 查询键；
- 锁定基准（D3）：过期判定=pinned_hash≠报告 design_hash（与表层 stale
  正交——提示性不阻断比对）；失效键不自动删（灰显「已移除」），清理
  经重新锁定；
- 领域码面不透 raw message（R3b→2A4 批 UF-59 domainGate 两态化：
  CompareSourceNotFoundError 固定摘要+引导，网络错/窄化错 raw 兜底）；
- 挂账注记（docs/undefined-features-register.md）：
  - UF-63（开放）：FLOW 维度输出面单位标签错配——CompareMatrix 指标行
    `dimUnit(metric.dim)` 为两消费面之一（q_air 值 m3/s×标签 m³/d）；
  - UF-64（开放）：CompareMatrix 三处 `var(--wp-text-secondary)` 未定义
    失效——承接批修复须同步 CompareMatrix.test.tsx L71 令牌断言。
