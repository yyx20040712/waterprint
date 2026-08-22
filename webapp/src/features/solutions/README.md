# solutions —— 方案浏览器

枚举结果浏览：虚拟滚动表格 + 排序 + 诊断面板（ADR-005 语义的 UI 半）。

## 文件规划（实装期创建，先登记 file-contracts.md）

| 文件 | 职责 |
|------|------|
| `components/SolutionsTable.tsx` | AntD Table virtual 虚拟滚动（千级行流畅） |
| `components/RankingControls.tsx` | 排序键选择（margin_min/cost/字段白名单） |
| `components/DiagnosisPanel.tsx` | 无解诊断（最小冲突集 + 建议，持久面板） |
| `components/ApplySolutionButton.tsx` | 方案应用（乐观更新 + 失败回滚 §17.2） |
| `store/solutionsStore.ts` | 分页/排序/选中 slice |
| `api/` | 生成客户端调用（分页参数） |

## 规格要点

- 枚举任务语义永远是"单单元"（ADR-005）；UI 不提供跨单元多选入口；
- 数字 tabular-nums 等宽对齐（§19.3）；裕度列语义色（正绿负红）；
- queryKey 含三元组（§17.2 前端缓存规则：输入变自动失效）。
