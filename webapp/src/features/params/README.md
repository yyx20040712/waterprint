# params —— 参数与约束面板

选中对象的参数编辑 + 约束选择 + 假设清单查看（左侧面板，§19.2）。

## 文件清单（M0.5 结构接线创建骨架；FE5 批 6b 段三实装参数/假设两面；UX2 批假设编辑化 2026-08-30）

| 文件 | 状态 | 职责 |
|------|------|------|
| `lib/designParams.ts` | FE5 实装+UX2 扩；C2-visual F8 | 纯函数层：design 窄化门+draft 归一+脏比较+目录索引+假设合成行+假设编辑收集/PUT 载荷构造/conditions 透传+trimFloatNoise（F8 浮点噪声归一——12 位有效数字，显示/回填/步进三通道） |
| `lib/designParams.test.ts` | FE5 实装+UX2 扩 | 纯函数 node 测试（golden 内联节选+负例族+UX2 假设编辑 9 用例）；trimFloatNoise 用例=独立件 trimFloatNoise.test.ts（本件行数预算拆分——C2-visual F8） |
| `api/useUnitCatalog.ts` | FE5 实装 | 单元目录/假设清单查询薄封装（静态键） |
| `api/useProjectDesign.ts` | FE5 实装 | 项目 design 参数面查询（select 窄化；read 键 invalidate 面） |
| `components/ParamForm.tsx` | FE5 实装+C2-params 重制 | 参数表单：manifest 参数面+design 覆盖值→草稿→apply 提交重算——**表单化重制 Q1~Q7**（flex 三层骨架[head/body 滚/foot 固定]+单行 field[标签 secondary+field_id 悬浮隐藏]+单位入控件 dimUnit[C2VD V6 迁移 Space.Compact+自样式后缀 span——addonAfter 弃用根除]+grid 档位 chips 点击回填+重置钮；FD 可行域入口零动——glm D④「开发者表单」痛点收口，2026-09-10）；C2-visual F8：trimFloatNoise 五通道消费（显示/onChange/onBlur/步长喂入/回填） |
| `components/AssumptionsPanel.tsx` | FE5 实装+UX2 编辑化+C2-ALIGN A5r 页体化 | 经验取值页体（原设计假设独立 section 升位进 ParamTabs——2026-09-12 用户澄清）：行=左 ▸/▾ 展开钮+中文物理意义标签（assumptionLabel——key 悬浮追溯）+控件列 Space.Compact[122px+dimUnit 后缀]=ParamForm 同貌；展开=「默认 X · 出处」小字+覆盖行恢复默认链接；「提交修改」一次 PUT+自动重算（UX2 D1-D4 链路零变） |
| `components/ParamTabs.tsx` | C2-ALIGN A5r 新件 | 参数面板双分页容器：单元标题（ParamForm Q2 头部升位）+Segmented[约束参数 N\|经验取值 22]+双页体 display 切换恒挂载（草稿跨页保留；嵌套 antd Tabs 属禁用面 GC-08） |
| `lib/assumptionLabels.ts` | C2-ALIGN A5r 新件 | 22 键→中文物理意义字典（registry note 语义提炼；fail-open 回退 key；dimLabels 同款显示层纪律——core label_zh 化挂账；assumptionScope 11+11 分类案随用户澄清取缔[裁量史=brief §六]） |
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

## C2-params 批（2026-09-10）增量面

- 行为通道零变（drafts/apply/?task=/FD 引导全保持）；渲染面重制：
  单行布局/单位 addon（antd v6=.ant-space-addon）/chips/foot 常驻；
- canvasPane 配套：侧栏 280 默认+**拖拽把手**（240~480 clamp——用户
  裁选「边界可拉伸」）+假设清单限高 42% 自滚；
- shared/dimLabels 新导出 dimUnit（单位符号直取——零换算纪律沿袭）；
- 挂账：参数分组（manifest 无分组元数据——server/core 扩面呈裁量）/
  单元库选中联动（单元库子面统筹）。
