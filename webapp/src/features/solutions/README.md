# solutions —— 方案浏览器

枚举结果浏览：单单元枚举提交 → SSE 任务进度 → 分页方案表 → 行级应用
+ 无解诊断（ADR-005 语义的 UI 半；FE6 批 6b 段四实装 2026-08-29）。

## 文件清单（M0.5 骨架；FE6 批 6b 段四实装数据通道与组件）

| 文件 | 状态 | 职责 |
|------|------|------|
| `lib/solutionsView.ts` | FE6 实装 | 纯函数层：SolutionPage 窄化门+动态列模型+apply 载荷+排序选项 |
| `lib/solutionsView.test.ts` | FE6 实装 | 四纯函数族 node 测试（golden aao 内联夹具+负例族带键定位） |
| `lib/taskFeed.ts` | FE6 实装 | 纯函数层：SSE 线格式解析+事件归约 TaskView+TaskStatus 快照归一+终态判定 |
| `lib/taskFeed.test.ts` | FE6 实装 | 事件序列归约/线格式/快照归一 node 测试（畸形 data 拒负例） |
| `api/useTaskFeed.ts` | FE6 实装 | EventSource 自建薄壳（SSE 不走 customInstance——生成 useTaskEvents* 是一次性 JSON 读不可用） |
| `api/useProjectUnits.ts` | FE6 实装 | useReadProject 薄封装 select 窄化 {unitId,kind}[]（read 键三面共享） |
| `components/TaskPanel.tsx` | FE6 实装 | 任务态面板：SSE 进度徽标/进度条/阶段文案/failed 三件回显/取消 |
| `components/SolutionsTable.tsx` | FE6 实装 | 动态列方案表（响应 columns 建列+margin_min 语义色+受控分页+行级应用） |
| `components/RankingControls.tsx` | FE6 实装 | 排序键 Select（响应 columns 白名单；服务端恒降序不提供方向切换） |
| `components/DiagnosisPanel.tsx` | FE6 实装 | 无解诊断三段只读呈现（最小冲突集/失败计数/调参建议） |
| `components/ApplySolutionButton.tsx` | FE6 实装 | 行级应用（grid 字段投影 params——服务端 R5 原子事务非乐观更新） |
| `store/solutionsStore.ts` | 占位维持 | UI 态组件内 useState（分页/排序/任务 id 单面板无跨组件态——FE5 D2 先例；zustand 首例留 canvas 编辑批） |

## 规格要点（FE6 批 6b 段四口径）

- 枚举任务语义永远是"单单元"（ADR-005）；UI 不提供跨单元多选入口；
  提交载荷 unit_ids 恰 1（多值服务层 422 MultiUnitEnumerationError）；
- 任务 id 单一真相=URL `?task=`（与 `?project=` 双参共存）：枚举提交/
  方案应用（recalc_task_id）/params 表单 apply 三写入面全走
  history.replaceState；消费面=app/solutionsPane（TaskPanel+表挂载依据）；
- 弱类型行窄化门在 `lib/solutionsView.ts` 收口（顶层七字段逐类校验+
  行值域 number|string|boolean|null——nan_flag 布尔列服务端原样下发；
  NaN 服务端已转 null）；非法形状 SolutionsViewError 带键定位；
- 数字 tabular-nums 等宽对齐（§19.3）；裕度列语义色（正绿负红 null 灰）；
  nan_flag true→「不可行」标记；列序=响应序（服务端构造序不重排）；
- queryKey 含任务 id+分页/排序全量（§17.2 前端缓存规则：输入变自动失效）；
  排序白名单=响应 columns（服务端 422 拒白名单外，恒降序）；
- 应用后表格数据为已提交任务快照不自动刷新（旧行保留——服务端分页
  只读快照语义）；无解=done+feasible_count=0 合法终态非 failed。

## 挂账面（FE6 批外）

- constraints 编辑面（constraint_kb 空槽——options 传 null 走默认）；
- 工况面 UI（沿 FE5 D6 挂账）；跨标签自动跳转不抢焦点（UX 批）；
- cost 列（概算未注入枚举行——现状无此列不加）；万级行虚拟滚动
  （行数=网格组合数，golden 案例个位数~几十行常规渲染足够）；
- 建议条目点击跳转参数面板（DiagnosisPanel 只读——UX 批）。
