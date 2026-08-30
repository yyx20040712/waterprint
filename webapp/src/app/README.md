# app 层 —— 路由与 Provider 组合

**唯一允许组合 features 的层**（§13.5）。规则：features 互相禁止 import，
一切跨 feature 编排发生在本层。

## 文件清单（新文件先登记本清单——file-contracts.md §5 已委托逐层 README 维护）

| 文件 | 职责 | 状态 |
|------|------|------|
| `App.tsx` | 应用布局壳+Tabs 路由状态机+Providers 组合（§19.2 骨架，见文件头规格） | FE9 更新（2026-08-30）：六标签全实装（drawings 挂 DrawingsPane），占位屏组件退役删除 |
| `providers.tsx` | Provider 组合：AntD ConfigProvider（深色默认）/ QueryClient | FE3 实装：模块级 QueryClient 单例（组件外创建）+darkAlgorithm |
| `router.tsx` | 路由表：画布/三维（懒加载）/高程/图纸/概算 | 路由名冻结；机制定 D1=Tabs 状态机（App.tsx 持 activeKey），本文件类型面零消费变化 |
| `ErrorBoundary.tsx` | 每 feature 一个边界的封装件+errorReportPayload 导出 | FE3 最小接线：componentDidCatch 结构化上报+重试 fallback（复制诊断挂账 UX 批） |
| `queryClient.ts` | QueryClient 工厂+retry 策略（D3 领域错误口径：WaterprintApiError 不重试/网络族重试 1 次） | FE3 实装（providers 消费） |
| `queryClient.test.ts` | queryClient 策略+errorReportPayload 纯函数 vitest（node 环境） | 6 用例绿（D6-①③） |
| `projectParam.ts` | URL project 参数解析/合成纯函数（D5 单一真相+deep-link） | FE3 实装（viewer3dPane 消费） |
| `projectParam.test.ts` | projectParam 纯函数 vitest（node 环境） | 9 用例绿（D6-②） |
| `viewer3dPane.tsx` | viewer3d 标签页装配：lazy Scene+ErrorBoundary+projectId 空态 Select+URL 同步 | FE3 实装 |
| `canvasPane.tsx` | canvas 标签页装配：design 工艺图 projectFlow 投影→React Flow 只读画布（URL ?project= 单一真相+节点点击选中联动 params） | FE4 实装（FE5/FE6 批记账遗漏，FE7 补登 2026-08-29） |
| `solutionsPane.tsx` | solutions 标签页装配：?project=/?task= 双参+单单元枚举提交+TaskPanel（SSE）+方案表/诊断面板+apply 任务轨分立（R1 双轨） | FE6 实装（FE6 批记账遗漏，FE7 补登 2026-08-29） |
| `elevationPane.tsx` | elevation 标签页装配：?project= 消费+lazy ProfileChart（echarts 独立 chunk）+ErrorBoundary+空态/404 引导+ConditionSwitcher+PumpStationsPanel+"wp:task" 监听 invalidate | FE7 实装 |
| `costPane.tsx` | cost 标签页装配：?project= 消费+ErrorBoundary+空态/404 引导+工况 Select（缺省=design 回显）+EstimateTable 分级汇总+IndicatorsCard 指标对照+"wp:task" 监听 invalidate（第四处内联——非 lazy 无大件） | FE8 实装 |
| `drawingsPane.tsx` | drawings 标签页装配：?project= 消费+ErrorBoundary+空态引导+工况/单元源 404 分级+ExportButton 导出发起+SheetList 产物目录+DrawingPreview 元数据卡+"wp:task" 监听 invalidate（第五处内联——非 lazy 无大件） | FE9 实装 |

## 交互规范基线（§19，实现期遵守）

- 深色主题默认、语义色纪律（绿合格/橙警告/红错误/蓝水线/棕泥线）；
- 键盘优先：F5 计算、Del 删除、Ctrl+L 自动布局、Ctrl+S 保存；
- 反馈三通道：即时（连线拒绝）/ 非阻塞（toast）/ 持久（诊断面板）。
