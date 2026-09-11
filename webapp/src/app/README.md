# app 层 —— 路由与 Provider 组合

**唯一允许组合 features 的层**（§13.5）。规则：features 互相禁止 import，
一切跨 feature 编排发生在本层。

## 文件清单（新文件先登记本清单——file-contracts.md §5 已委托逐层 README 维护）

| 文件 | 职责 | 状态 |
|------|------|------|
| `App.tsx` | 应用布局壳+Tabs 路由状态机+Providers 组合（§19.2 骨架，见文件头规格） | FE9 更新（2026-08-30）：六标签全实装（drawings 挂 DrawingsPane），占位屏组件退役删除；UX1 更新：?tab= 路由态进 URL（初值三级解析+onChange replaceState 写入）；ENG5 更新（2026-08-31）：深链判据扩 ?enum=（无 ?tab= 有 ?task= 或 ?enum=→solutions——枚举轨深链同落方案浏览）；R2-A 批2 更新（2026-09-02）：Header 设置按钮+连接设置 Modal+AUTH_EVENT 自愈回路监听；?token= 首参引导编排放模块顶层（读→写 localStorage+replaceState 剥离）；C1 更新（2026-09-10）：滚动容器重构（根 Layout overflow 收敛+Tabs wp-scroll-tabs 统一滚动域+Sider 自滚——需求①根治）+顶栏品牌区（水滴标+双语名+鎏金收边线）+StatusBar 挂载+Sider 280→232；C2-lib（2026-09-10）：libraryFocusId 受控态双穿线（Sider[Drawer 开闭]+CanvasPane[画布定位光环]——U3 联动） |
| `providers.tsx` | Provider 组合：AntD ConfigProvider（C1 主题骨架全量 token）/ QueryClient | FE3 实装；C1 重制（2026-09-10）：darkAlgorithm+方向 A 全量 seed token（cssVar 显式传参省略——v6 样式面默认开，A2-N-04 勘误）（工程蓝主色/三层底/文字三档/语义三色/13px 工程密度/等宽数值栈）+components 微调（Layout 头底分离/Tabs 鎏金墨条/Table 表头基线）；深色锁定（亮色维持 UX 批挂账） |
| `router.tsx` | 路由表：画布/三维（懒加载）/高程/图纸/概算 | 路由名冻结；机制定 D1=Tabs 状态机（App.tsx 持 activeKey），本文件类型面零消费变化；UX1：view 态持久化挂账行收口（?tab= URL 落地——纯注记） |
| `ErrorBoundary.tsx` | 每 feature 一个边界的封装件+errorReportPayload 导出 | FE3 最小接线：componentDidCatch 结构化上报+重试 fallback（复制诊断挂账 UX 批） |
| `queryClient.ts` | QueryClient 工厂+retry 策略（D3 领域错误口径：WaterprintApiError 不重试/网络族重试 1 次） | FE3 实装（providers 消费） |
| `queryClient.test.ts` | queryClient 策略+errorReportPayload 纯函数 vitest（node 环境） | 6 用例绿（D6-①③） |
| `projectParam.ts` | URL project/task/enum/tab 参数解析/合成纯函数（D5 单一真相+deep-link+UX1 S4 路由态+ENG5 D6 双任务轨） | FE3 实装（viewer3dPane 消费）；UX1 增 tabParam 两函数；ENG5 增 enumParam 三函数（?enum= 枚举任务轨——与 ?task= 计算轨并存互不覆盖，I-4 收口）；R2-A 批2 增 tokenParam 两函数（?token= 首参引导——App.tsx 模块顶层消费，写入面唯一无 with 函数） |
| `projectParam.test.ts` | projectParam 纯函数 vitest（node 环境） | 32 用例绿（FE3 9+FE6 task 组+UX1 tab 组 4+ENG5 enum 组 9[双轨独立往返断言]——以 vitest 实跑为准） |
| `useProjectId.ts` | projectId 跨面板共享 hook（UX1 S3——URL ?project= 单一真相订阅面：PROJECT_EVENT 监听重读同值早退+setter 回写 replaceState 写后派发） | UX1 实装（六 pane 消费：写方 canvas/viewer3d setter、读方四 pane 订阅；薄壳不测裁量见头注） |
| `projectCreate.ts` | 建项纯函数面（P0-1）：normalizeProjectName（strip+1~100 与 core ViewState.name 同口径）/projectOptionLabel（F3「名称 (id8)」无名回退全 id）/parseProjectJson（导入解析判别联合——结构校验归 server 422 面） | P0-1 实装（2026-09-11）——createProjectModal 消费；测试 projectCreate.test.ts |
| `createProjectModal.tsx` | 建项 Modal（P0-1——F1/F4-文案面）：空白新建（名称必填）/导入 JSON（File.text 解析）两态+POST {name, project?}+成功 invalidate 列表+onCreated 切入 | P0-1 实装（2026-09-11）——canvasPane/viewer3dPane 空态 CTA 共用件（「两处内联同构挂账 UX 批」就此收口） |
| `projectCreate.test.ts` | projectCreate 纯函数 vitest（node 环境） | P0-1 实装（名称校验/label 格式/导入解析三组） |
| `enumerateBar.tsx` | 枚举提交条（P0-2 行数预算修自 solutionsPane 抽取——组合层件：ConstraintPicker[params]×unitOptionLabel[solutions] 跨 feature 组合归 app；单元下拉[useUnitCatalog nameById 内聚]+约束勾选+提交钮+两错误行，逻辑零变更纯展示） | P0-2 实装（2026-09-11） |
| `viewer3dPane.tsx` | viewer3d 标签页装配：lazy Scene+ErrorBoundary+projectId 空态 Select+URL 同步 | FE3 实装；UX1：S3 写方换 useProjectId（回写+派发收敛进 hook setter） |
| `canvasPane.tsx` | canvas 标签页装配（C2-thumb 2026-09-11：ThumbnailStage[viewer3d 域]组合穿线——useSceneQuery 同键复用+404/投影拒静默回退象形+切项目清批+unitThumbnails props 注入 CanvasFlow）：design 工艺图 projectFlow 投影→React Flow 只读画布（URL ?project= 单一真相+节点点击选中联动 params）+flex 行满高链（C2-canvas P2） | FE4 实装（FE7 补登）；UX1：S3；C2-canvas 满高；C2-params：侧栏 280 默认+拖拽把手（240~480）+aside flex 列（参数面板 body 内滚+假设清单限高 42%）；C2-lib（2026-09-10）：libraryFocusId prop 透传（App 持态联动穿线） |；P0-3（2026-09-11）：画布区顶部挂 CanvasEditToolbar（编辑会话/校验/保存/常驻提交计算）+画布区 flex 列化 |
| `canvasEditToolbar.tsx` | 画布编辑工具条（P0-3——task-c2-edit-plan §一.4/一.5）：编辑会话开关⑤[beginEdit 快照/dirty Popconfirm 退场]+校验⑦[警告放行 Alert]+保存[markSaved+invalidate+toast]+常驻提交计算⑥[dirty 先存后算——?task= 回写+TASK_EVENT 六标签联动]；保存体=时点最新 raw+草稿四面（红线⑤双守） | P0-3 实装（2026-09-11）——canvasPane 画布区顶部挂载 |
| `unitLibrary.tsx` | 左侧单元库浏览：搜索+四线分组树+Drawer 详情（app 层薄壳——组装面在 unitLibraryTree 纯函数） | M2 实装；C2-lib 重制（2026-09-10）：图标行（titleRender——域色三色组图标+中文名单主列，**英文码不显示**[用户裁定]——悬浮 title=全 unit_id 唯一追溯通道）+组标题域色短条计数右对齐+foot 计数条（左右分列 32 单元/5 组 catalog 驱动——树区自滚钉底）+Drawer 标题图标+focusId 受控 props（App 联动穿线——生命周期=Drawer 开闭）+defaultExpandAll；设计真源 briefs/task-C2-lib-plan.md |；P0-3（2026-09-11）：编辑态双入口（叶行悬浮「＋」+Drawer 主钮「添加到画布」→ canvasStore.addUnit——呈裁② 甲案） |
| `unitLibraryTree.ts` | 单元库树纯函数：目录→Tree 数据（四线分组+内置排末+过滤+叶反查） | M2 实装；C2-lib 增 libraryGlyph（条目→象形字形——画布查表键同口径：builtin 喂 kind 槽） |
| `unitLibraryTree.test.ts` | unitLibraryTree 纯函数 vitest（node 环境） | M2 实装；C2-lib 增 libraryGlyph 4 用例（18 用例绿——以 vitest 实跑为准） |
| `solutionsPane.tsx` | solutions 标签页装配：?project=/?task=/?enum= 三参+单单元枚举提交+TaskPanel（SSE）+方案表/诊断面板+apply 任务轨分立（R1 状态双轨+ENG5 D6 键双轨：表源=enum 键/面板=task 键优先） | FE6 实装（FE6 批记账遗漏，FE7 补登 2026-08-29）；UX1：S3 读方换 useProjectId 订阅；ENG5：枚举提交写 ?enum=（apply 后深链不丢方案表）；R1：表源轨初值 ?enum= 优先、纯 ?task= 旧链兜底（DS-01 修复——FE6 时代分享链表挂载回归）；CP1：ConstraintPicker 挂载（约束勾选→options.constraints 三键载荷——features/params 面组件） |
| `elevationPane.tsx` | elevation 标签页装配：?project= 消费+lazy ProfileChart（echarts 独立 chunk）+ErrorBoundary+空态/404 引导+ConditionSwitcher+PumpStationsPanel+TASK_EVENT 事件桥监听 invalidate | FE7 实装；UX1：S3 读方换 useProjectId 订阅（D7 勘误措辞） |
| `costPane.tsx` | cost 标签页装配：?project= 消费+ErrorBoundary+空态/404 引导+工况 Select（缺省=design 回显）+EstimateTable 分级汇总+IndicatorsCard 指标对照+TASK_EVENT 事件桥监听 invalidate（第四处监听——非 lazy 无大件） | FE8 实装；UX1：S3 读方换 useProjectId 订阅（D7 勘误措辞） |
| `drawingsPane.tsx` | drawings 标签页装配：?project= 消费+ErrorBoundary+空态引导+工况/单元源 404 分级+ExportButton 导出发起（UX1 D3 单元 Select 可投影面过滤——目录 builtin 集判别，catalog 未就绪不过滤）+SheetList 产物目录+DrawingPreview 元数据卡+TASK_EVENT 事件桥监听 invalidate（第五处监听——非 lazy 无大件） | FE9 实装；UX1 更新（S3 订阅+D3 过滤） |
| `global.css` | 全局样式底座（C1 批 2026-09-10 首个 CSS 文件——此前纯 inline style）：body 底色/字体栈/document 滚动根除+WebKit 滚动条+项目色变量轴（--wp-gold/water/sludge/mine/convey——antd 无槽位色轴真源；四色与 unitGlyph 主源等 N 处字面量联动[清单见 global.css 头注]，mine/convey=C2-canvas 四域色板新增）+antd Tabs 内容滚动域结构微调（wp-scroll-tabs）+画布点阵工具类（C2-canvas 消费兑现）+Tabs 满高链（body/content 两层——C2-visual 勘正：v6 现版 tabpane 包装层零命中，死选择器已除）+C2-visual 页签行面板蓝底/下边框/8px 内距+内容 gutter 分策（content 12px/16px 内距+wp-full-bleed 满铺回收[canvas/siteplan]）+wp-lib-hit 定位光环（C2-lib 联动命中节点 wrapper ::after 水蓝外扩环——R-G3 联动清单成员）；check_webapp/file_budgets 均不扫 .css——本清单即登记面 | C1 实装（方向 A 冻结值） |
| `statusBar.tsx` | 状态栏：底部全局信息条（C1 视觉稿新增件，用户裁选一期即做）——projectId 订阅（useProjectId）+就绪态绿点；版本号面减配（server 无现成端点，webapp-only 纪律不新增——二期有端点再上）；薄壳不测裁量（app 层惯例，行为面归无头 DOM 断言） | C1 实装 |
| `tokenSettingsModal.tsx` | 连接设置 Modal：API token 查看/保存/清除（Input.Password 受控+保存=setApiToken/清除=clearApiToken/关闭；零即时校验——错 token→401→AUTH_EVENT→App 重开本 Modal=自愈回路） | R2-A 批2 实装（2026-09-02）：Modal 形态（不动 router.tsx AppRoute 冻结面）；开态同步现读 localStorage 回显 |

## 交互规范基线（§19，实现期遵守）

- 深色主题默认、语义色纪律（绿合格/橙警告/红错误/蓝水线/棕泥线）；
- 键盘优先：F5 计算、Del 删除、Ctrl+L 自动布局、Ctrl+S 保存；
- 反馈三通道：即时（连线拒绝）/ 非阻塞（toast）/ 持久（诊断面板）。
