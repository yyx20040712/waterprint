# params —— 参数与约束面板

选中对象的参数编辑 + 约束选择 + 假设清单查看（左侧面板，§19.2）。

## 文件清单（M0.5 结构接线创建骨架；FE5 批 6b 段三实装参数/假设两面；UX2 批假设编辑化 2026-08-30）

| 文件 | 状态 | 职责 |
|------|------|------|
| `lib/designParams.ts` | FE5 实装+UX2 扩 | 纯函数层：design 窄化门+draft 归一+脏比较+目录索引+假设合成行+假设编辑收集/PUT 载荷构造/conditions 透传 |
| `lib/designParams.test.ts` | FE5 实装+UX2 扩 | 纯函数 node 测试（golden 内联节选+负例族+UX2 假设编辑 9 用例） |
| `api/useUnitCatalog.ts` | FE5 实装 | 单元目录/假设清单查询薄封装（静态键） |
| `api/useProjectDesign.ts` | FE5 实装 | 项目 design 参数面查询（select 窄化；read 键 invalidate 面） |
| `components/ParamForm.tsx` | FE5 实装 | 参数表单：manifest 参数面+design 覆盖值→草稿→apply 提交重算 |
| `components/AssumptionsPanel.tsx` | FE5 实装+UX2 编辑化 | 设计假设清单+行内编辑：InputNumber/恢复默认→面板级「提交修改」一次 PUT+自动重算（FE5「编辑挂账」收口） |
| `components/ConstraintPicker.tsx` | 占位维持 | 约束勾选——数据通道待 constraint_kb 迁移批（D3：空槽+无读取端点） |
| `store/paramsStore.ts` | 占位维持 | 编辑态 slice——草稿态组件内 useState（单面板无跨组件态；zustand 首例留 canvas 编辑批） |

## 规格要点（FE5 批 6b 段三口径）

- 参数编辑走"草稿→提交"：draft 归一（string→number|null，null=禁提交态）
  与脏比较（design 覆盖 ?? manifest 默认为基准，等值不产空写）在
  `lib/designParams.ts` 纯函数收口；**前端零校验规则复制**（range/grid
  纯展示——range 无执行点，语义校验经 calc 任务 failed 回流挂账 solutions 批）；
- 提交通道=POST /api/calc/solutions/apply（服务端原子样板借用：merged.update
  →save→自动重算→失败回滚）；成功后 invalidate read 键
  （['/api/projects/&lt;id&gt;']——canvas/params/假设三面同步刷新）；
  params 专属端点归 server 批裁量挂账；
  **FE6 联动收口（挂账③）**：apply onSuccess 回写 URL `?task=`
  recalc_task_id（withTaskParam 逻辑内联——分层禁 import app），
  「方案浏览」标签任务态面板经参数呈现重算进度与失败回显
  （消息文案「已提交重算（任务 …）——方案页可看进度与失败回显」）；
- 错误消息统一 WaterprintApiError.message 透出（422/404/409 归一面）；
- 假设面板是"默认值显性化"的 UI 落点（§3 保证 7）——21 条 registry 声明
  序清单+覆盖标记；**UX2 批（2026-08-30）编辑面收口**（FE5 挂账解除）：
  行内 InputNumber 草稿+「恢复默认」（=overrides 删键回落 DEFAULTS；目录外
  键=删行）→面板级「提交修改」**一次 PUT /api/projects/{id}**（body=GET
  未窄化原始体——同键 query 不带 select 缓存共享，仅结构化替换
  `design.assumption_overrides`，`withAssumptionOverrides` 纯函数收口禁散拼）；
  409 锁冲突（ProjectLockedError——services save 前置探测 {id}.wp.lock）
  保守提示「项目已被他处修改，请刷新后重试」不 force 不重试；PUT 成功→
  invalidate read 键→自动 POST /api/calc/run（conditions=GET 原始
  `design.checked_units` 数组原样透传，缺省不传；run 失败仅提示不回滚保存
  ——两步非原子诚实呈现）+`?task=` 回写（ParamForm D3-③ 同构：
  replaceState+TASK_EVENT 派发）；数值校验 Number.isFinite（NaN/Infinity/
  null 拒提交+行内 error 提示，`collectAssumptionEdits` 纯函数）；
  覆盖窄化=**读侧有限数值面**（JS 无 int/float 之分——整数值宽容；
  server 写侧 strict float 拒 int 属 Python 语义，读取链不复制——R 轮 M2 注记）；
- 工况面（checked_units/conditions/condition_mappings）无数据源出批挂账。
