# app 层 —— 路由与 Provider 组合

**唯一允许组合 features 的层**（§13.5）。规则：features 互相禁止 import，
一切跨 feature 编排发生在本层。

## 文件清单（新文件先登记本清单——file-contracts.md §5 已委托逐层 README 维护）

| 文件 | 职责 | 状态 |
|------|------|------|
| `App.tsx` | 应用布局壳+Tabs 路由状态机+Providers 组合（§19.2 骨架，见文件头规格） | FE9 更新（2026-08-30）：六标签全实装（drawings 挂 DrawingsPane），占位屏组件退役删除；UX1 更新：?tab= 路由态进 URL（初值三级解析+onChange replaceState 写入）；ENG5 更新（2026-08-31）：深链判据扩 ?enum=（无 ?tab= 有 ?task= 或 ?enum=→solutions——枚举轨深链同落方案浏览）；R2-A 批2 更新（2026-09-02）：Header 设置按钮+连接设置 Modal+AUTH_EVENT 自愈回路监听；?token= 首参引导编排放模块顶层（读→写 localStorage+replaceState 剥离） |
| `providers.tsx` | Provider 组合：AntD ConfigProvider（深色默认）/ QueryClient | FE3 实装：模块级 QueryClient 单例（组件外创建）+darkAlgorithm |
| `router.tsx` | 路由表：画布/三维（懒加载）/高程/图纸/概算 | 路由名冻结；机制定 D1=Tabs 状态机（App.tsx 持 activeKey），本文件类型面零消费变化；UX1：view 态持久化挂账行收口（?tab= URL 落地——纯注记） |
| `ErrorBoundary.tsx` | 每 feature 一个边界的封装件+errorReportPayload 导出 | FE3 最小接线：componentDidCatch 结构化上报+重试 fallback（复制诊断挂账 UX 批） |
| `queryClient.ts` | QueryClient 工厂+retry 策略（D3 领域错误口径：WaterprintApiError 不重试/网络族重试 1 次） | FE3 实装（providers 消费） |
| `queryClient.test.ts` | queryClient 策略+errorReportPayload 纯函数 vitest（node 环境） | 6 用例绿（D6-①③） |
| `projectParam.ts` | URL project/task/enum/tab 参数解析/合成纯函数（D5 单一真相+deep-link+UX1 S4 路由态+ENG5 D6 双任务轨） | FE3 实装（viewer3dPane 消费）；UX1 增 tabParam 两函数；ENG5 增 enumParam 三函数（?enum= 枚举任务轨——与 ?task= 计算轨并存互不覆盖，I-4 收口）；R2-A 批2 增 tokenParam 两函数（?token= 首参引导——App.tsx 模块顶层消费，写入面唯一无 with 函数） |
| `projectParam.test.ts` | projectParam 纯函数 vitest（node 环境） | 32 用例绿（FE3 9+FE6 task 组+UX1 tab 组 4+ENG5 enum 组 9[双轨独立往返断言]——以 vitest 实跑为准） |
| `useProjectId.ts` | projectId 跨面板共享 hook（UX1 S3——URL ?project= 单一真相订阅面：PROJECT_EVENT 监听重读同值早退+setter 回写 replaceState 写后派发） | UX1 实装（六 pane 消费：写方 canvas/viewer3d setter、读方四 pane 订阅；薄壳不测裁量见头注） |
| `viewer3dPane.tsx` | viewer3d 标签页装配：lazy Scene+ErrorBoundary+projectId 空态 Select+URL 同步 | FE3 实装；UX1：S3 写方换 useProjectId（回写+派发收敛进 hook setter） |
| `canvasPane.tsx` | canvas 标签页装配：design 工艺图 projectFlow 投影→React Flow 只读画布（URL ?project= 单一真相+节点点击选中联动 params） | FE4 实装（FE5/FE6 批记账遗漏，FE7 补登 2026-08-29）；UX1：S3 写方换 useProjectId |
| `solutionsPane.tsx` | solutions 标签页装配：?project=/?task=/?enum= 三参+单单元枚举提交+TaskPanel（SSE）+方案表/诊断面板+apply 任务轨分立（R1 状态双轨+ENG5 D6 键双轨：表源=enum 键/面板=task 键优先） | FE6 实装（FE6 批记账遗漏，FE7 补登 2026-08-29）；UX1：S3 读方换 useProjectId 订阅；ENG5：枚举提交写 ?enum=（apply 后深链不丢方案表）；R1：表源轨初值 ?enum= 优先、纯 ?task= 旧链兜底（DS-01 修复——FE6 时代分享链表挂载回归）；CP1：ConstraintPicker 挂载（约束勾选→options.constraints 三键载荷——features/params 面组件） |
| `elevationPane.tsx` | elevation 标签页装配：?project= 消费+lazy ProfileChart（echarts 独立 chunk）+ErrorBoundary+空态/404 引导+ConditionSwitcher+PumpStationsPanel+TASK_EVENT 事件桥监听 invalidate | FE7 实装；UX1：S3 读方换 useProjectId 订阅（D7 勘误措辞） |
| `costPane.tsx` | cost 标签页装配：?project= 消费+ErrorBoundary+空态/404 引导+工况 Select（缺省=design 回显）+EstimateTable 分级汇总+IndicatorsCard 指标对照+TASK_EVENT 事件桥监听 invalidate（第四处监听——非 lazy 无大件） | FE8 实装；UX1：S3 读方换 useProjectId 订阅（D7 勘误措辞） |
| `drawingsPane.tsx` | drawings 标签页装配：?project= 消费+ErrorBoundary+空态引导+工况/单元源 404 分级+ExportButton 导出发起（UX1 D3 单元 Select 可投影面过滤——目录 builtin 集判别，catalog 未就绪不过滤）+SheetList 产物目录+DrawingPreview 元数据卡+TASK_EVENT 事件桥监听 invalidate（第五处监听——非 lazy 无大件） | FE9 实装；UX1 更新（S3 订阅+D3 过滤） |
| `tokenSettingsModal.tsx` | 连接设置 Modal：API token 查看/保存/清除（Input.Password 受控+保存=setApiToken/清除=clearApiToken/关闭；零即时校验——错 token→401→AUTH_EVENT→App 重开本 Modal=自愈回路） | R2-A 批2 实装（2026-09-02）：Modal 形态（不动 router.tsx AppRoute 冻结面）；开态同步现读 localStorage 回显 |

## 交互规范基线（§19，实现期遵守）

- 深色主题默认、语义色纪律（绿合格/橙警告/红错误/蓝水线/棕泥线）；
- 键盘优先：F5 计算、Del 删除、Ctrl+L 自动布局、Ctrl+S 保存；
- 反馈三通道：即时（连线拒绝）/ 非阻塞（toast）/ 持久（诊断面板）。
