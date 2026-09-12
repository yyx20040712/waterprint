# ADR-018：多工况对比与锁定（枚举全工况化 + 对比矩阵 + ViewState 锁定基准）

- 状态：**已接受（已冻结）**（授权链=P2 路线图第三批「多工况对比与锁定」
  ——n+42 批尾用户裁定内容、GOV1~GOV5+V2 顺延后照序；ADR-007 决策 4
  「UI 可并排对比」兑现批 + ConditionSwitcher 头注 UX 挂账清偿批；本 ADR
  为 D1~D6 唯一语义源；2026-09-12 会话 n+48 按用户常设指令默认推荐项
  定稿记档供追认）。
- 背景：
  - ConditionSet 契约（ADR-007/contracts/condition.py）冻结 2+k 工况族
    （baseline 恒 design/avg 两档 + 每受检单元一条 design 档检修敏感性；
    key 字面量族 GR-20），calc 面已全工况（PlantResult.conditions 按
    condition_key 索引、scene/elevation/cost/site 四端点收 condition_key
    查询参），但枚举面（app.py run_enumeration）硬取首档只产单工况行、
    FE 无并排对比面、checked_units 无编辑 UI、锁定语义未定义。
  - 锁面约束：run_enumeration 签名 / PlantResult 顶层 / 271 键测试锁面——
    方案空间以「零签名变更、零总线触碰、锁键只增不改」为界。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **对比形态=方案表多工况行混排 + 独立「工况对比」pane 指标矩阵**（行=指标[各单元 out_dims 声明面+警告数]、列=工况键、差异高亮、失效工况灰显）；ConditionSwitcher 头注「双图并排」挂账以矩阵并排语义清偿，不做同 pane 双图 | 工艺工程师对比的是指标差异而非几何；双图并排成本最高（双数据通道/深链/stale 横幅翻倍）收益最低；混排行是枚举全工况化的自然产物零额外视图成本 |
| D2 | **枚举全工况化=run_enumeration 内逐工况 upstream_context→enumerate_solutions→concat，整帧一次 apply_constraints/rank；签名不变**；逐工况循环抽 app_enumeration.py 伴生件（app.py 500 行预算的宪法正解）；diagnosis 触发口径=全工况无可行解（分工况无解诊断挂账）；空集守卫保留（语义从「取首档」转为「迭代前提」）；**行序记档（实现批实测）**：concat 帧序=工况序×网格序，但 margin_min 全 NaN（AAO 族无 margin_* 字段）时 rank 稳定排序 tie_break=grid 轴升序 → 呈现序=**网格行主序、工况内序交错**（同方案档各工况相邻）——此较工况块序更利于「同参数档跨工况比」，记档为默认语义；margin_* 在场单元则 margin_min 全局排序优先 | execute_graph 已一次算全工况（零额外计算成本）；condition_key 常量列机制现成（enumerate.py）；签名不变=271 键锁面零破；行数 ×(2+k) 线性=ADR-007 决策 2 既有口径 |
| D3 | **锁定=ViewState 持久化**（新增 compare 字段：pinned 工况键集 + pinned_hash 锁定时刻结果件 design_hash；不参与哈希，pydantic 缺省兼容旧项目零迁移）；FE 呈现 pinned_hash 与对比源结果件 repro.design_hash 比对——不一致出「基准已过期」横幅+「重新锁定」刷新（pinned∩现工况集过滤失效键）；锁定/解锁本身不触发 stale | 锁定是视图偏好非设计事实——入哈希会让纯视图动作引爆 stale 信任链（c 否决）；纯会话态断跨会话工作流且与 CP2 勾选持久化样板相悖（a 否决）；ViewState「不参与哈希」语义槽现成（project_schema.py ViewState），与 GR-21 只增字段向后兼容先例同制。**比对面修正记档（实现批实录）**：pinned_hash 比对对象=对比数据源（最近 done calc 结果件）的 repro.design_hash 而非当前项目 digest——改 design→重算→新结果件 hash 不同→过期提示正确触发；stale 仅表层横幅（「先重算」），不阻断比对（hash 不同即过期，与结果集新旧正交） |
| D4 | **checked_units 编辑=工况对比面板内双页「工况校核」集合面板**（Checkbox.Group 全集 + 标题行「受检 k 单元→计算工况 2+k 档」代价提示），保存链路全复刻 CP2 样板（rawQuery 恢复/乐观 set/整项目 PUT/invalidate→既有 stale 机制自动激活/onError 回滚）；恢复投影∩当前单元集过滤幽灵勾选；删除单元级联清理沿 designWriter 既有面。**位置勘正记档（工况面 UX 反馈批 2026-09-12 用户反馈直接翻案）**：原定「画布侧栏」（App Sider 第二区）翻案为「对比面板内双页」——comparePane 顶部 Segmented[对比矩阵\|工况校核]（ParamTabs A5r 制式直复刻——嵌套 antd Tabs 属禁用面 GC-08；双页体 display 切换恒挂载），勾选→PUT→invalidate→矩阵列联动同面板闭环，Sider 减负为副产物；组件与 checkedUnits lib 随迁 features/compare。**资格守卫交互记档（实现批实录）**：装配层资格校验（T3-D4）要求受检单元 manifest.condition_mappings 非空——当前 13 单元全空（UF-36 数据面挂账），持久面 design.checked_units 非空即 calc 400 拒（报文明确「须声明检修降级映射」——FE 错误通道透传）；多工况对比不受此限：run 请求级 conditions 参数独立驱动工况集（build_condition_set 于 payload 面）。面板=状态编辑一等态（intent 记录），数据前提归单元包声明面 | 集合语义需全局呈现运行数代价，散落单元属性内无法呈现 2+k 成本；CP2 样板（solutionsPane 约束勾选族）已验收，零新持久化通道；用户反馈「工况校核应该放在工况对比面板中，位置和工艺画布的参数面板 tab 一样」——校核（勾选受检）与对比（看矩阵列）是同一工作流的两步，同面板切换最短路径 |
| D5 | **fetch_solutions 页内混工况 + 跨工况 margin_min 全局排序**（condition_key 在列集内即自动入排序白名单，enumeration.py 服务端零改动）；**新增 GET /api/calc/compare/{project_id} 聚合端点**（读最近 done calc 任务结果按 condition_key 投影指标矩阵+design_hash+stale 判定；端点集 32→33 三处同步沿 ADR-012 D8 先例）；**rowKey 前缀 condition_key**（多工况行撞键修复，SolutionsTable rowKey 拼接段）；worker 枚举 result 载荷增 condition_keys 清单（与 calc 面同制） | 分工况分页需新过滤参+条件扫描，违背跨工况比裕度诉求（否决）；FE 并行拉四端点拼矩阵=四次窄化+跨域 join 逻辑归错层（否决——聚合归 server 沿 ADR-012 D7）；rowKey 不修即多工况行渲染撞 key bug |
| D6 | **测试面=新件为主 + 既有两件语义翻案**；core 枚举全工况/server compare 与 worker 载荷/FE compareView 与 checkedUnits 纯函数各层新件；**例外记档**：run_enumeration 行为从单工况翻为多工况，既有两件（test_run_enumeration_cass_fifteen_rows 行数 15→30、test_run_enumeration_sort_and_truncation total_feasible 15→30）语义翻案修订入锁面笔呈报——签名不变但行为变，「零触碰」以「不改既有件则不可能收编全工况化」为语义边界，本行即呈报面；其余既有锁定测试零触碰 | ADR-015 D3 锁面草稿器工序：draft_lock_manifest.py 预检漂移直出重锁草稿→[HUMAN-LOCK] 重锁；既有两件翻案非静默 |

- 后果：
  - 正面：ADR-007 决策 4「UI 可并排对比」全链兑现（枚举行+指标矩阵
    双面）；checked_units 从只读透传升级为可编辑一等态；锁定语义落入
    ViewState 既有槽，信任链零污染；core/server 签名全冻结，271 键锁面
    只增不改。
  - 代价：枚举行数 ×(2+k)（线性，ADR-007 决策 2 既有口径；k 软上限
    记档挂账）；端点集 32→33（三处同步工序）；ViewState 增字段（旧
    项目缺省兼容，迁移面零）。
  - 记档：「双图并排」挂账以矩阵并排清偿的解释锁定于 D1；分工况无解
    诊断、k 软上限（建议 ≤8 待魔法数字审批）、纵断/概算双图并排字面
    形态、对比矩阵成本列注入、失效锁定键服务端清理工具、compare 端点
    结果缓存——六项挂账；**批尾追记**：其余 30 单元 out_dims 声明沿
    V2 挂账顺延（本批顺带兑现 CASS 31 条——枚举锚单元；机械扩面与
    本批核心正交）；条件映射数据面（condition_mappings 13 单元全空
    =UF-36 挂账）为受检面完全启用前置——对比矩阵请求级工况不受限。
  - **工况面 UX 反馈批追记（2026-09-12 件 4——量纲三写面对账收口）**：
    out_dims.dim 实测对账（M3D2 实读法一过+AST 门禁常设）查出 7 键
    分叉并归一（AAO q_wet FLOW→VOLUME/t_n/t_o/t_total/theta_c
    TIME→DIMENSIONLESS、CASS q_decant VOLUME→DIMENSIONLESS/theta_c
    TIME→DIMENSIONLESS——③手工推写值改①②镜像）；结构裁定=量纲真源
    单归 FormulaSpec.output_dim，out_dims.dim 降为消费投影+对账断言件
    （门禁 scripts/check_out_dims_consistency.py；①无声明的构造/圆整/
    聚合键以②projection dim_of 兜底基准）；**DimKey 扩成员候选挂账**：
    HRT/泥龄族单位 h/d、滗水流量 m³/h 在现 10 成员枚举无贴切档
    （归一取 DIMENSIONLESS 是「无单位显示」对「错误单位显示」的次害
    选择）——扩 TIME_H/FLOW_M3_PER_H 类新成员需动 CANONICAL_UNITS+
    FE DIM_LABELS 镜像+parse 白名单全链，独立批呈裁；准则成文=
    engineering-conventions GR-42（声明路线分轨）；FE 词典镜像门禁=
    scripts/check_dim_labels_mirror.py（门禁 13→14 与对账门禁 12→13
    同批）。
  - **DimKey 扩成员批追记（2026-09-12——上段挂账收口，用户裁定
    「HRT/泥龄应显示单位」插队）**：core quantity.py 扩 TIME_H（h）/
    TIME_D（d）/FLOW_H（m3/h）三刻度档成员（同量纲异规范刻度——
    CANONICAL_UNITS+UF-20 白名单+规格头注全链，锁定测试补笔
    test_quantity.py 三件）；三写面翻案 8 键归位真刻度——AAO
    t_o/t_n/t_total→TIME_H、theta_c→TIME_D（件 4 归一时的
    DIMENSIONLESS 次害选择终结）+CASS theta_c→TIME_D/q_decant→
    FLOW_H/t_phase_sum TIME→TIME_H（原 TIME 规范 s 对 h 值=错误
    单位显示，批内语义修正——①②③三面一致故对账门禁不拦，系值
    语义病非分叉病）；FE DIM_LABELS 镜像 +3 行（dimLabels 13 成员，
    镜像门禁自动对账）。参数面 h/d 语义字段（t_p/t_cycle 族 ~25 个）
    沿 dimensions 注册表「单位语义随 i18n 键走」既有口径不入本批
    （R1a 登记+四行业横扫=独立挂账）。
- 细化归属：core 枚举全工况（app.py 循环 + app_enumeration 抽件）→
  server compare 端点与 worker 载荷与 ViewState.compare 字段 → webapp
  对比 pane/工况校核面板/锁定横幅/rowKey 修复；测试三层新件 +
  锁面重锁草稿（ADR-015 工序）。
