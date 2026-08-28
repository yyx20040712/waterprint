# 文件职责契约（单一事实源）

> 一个文件只干一件事、只通过接口对外负责（§13）。本表是机器强制对象：
> `scripts/check_structure.py` 与 `core/tests/arch/test_structure.py` 双向校验——
> **源码文件未列 = CI 失败；列了不存在 = CI 失败**。新增/改名文件必须先补表。
> 每个文件内部的完整规格见其源码头部"规格说明"节。

## 1. core 计算内核（L0~L4）

| 路径 | 层 | 唯一职责 | 输入 | 输出 |
|------|----|----------|------|------|
| `core/waterprint/contracts/quantity.py` | L0 | 量纲与规范单位定义、pint 边界包装（唯一 pint 接触点；GR-36 类③量纲真源） | 单位字符串/带单位数值 | 规范单位裸值、Quantity、InvalidUnitError、InvalidQuantityError |
| `core/waterprint/contracts/flow.py` | L0 | 水量契约与构造校验（q_design 派生消双轨；GR-36 类①冻结 schema） | q_avg_daily、Kz | WaterFlow、make_flow、InvalidFlowError |
| `core/waterprint/contracts/quality.py` | L0 | 水质契约 + 出水标准库（标准是数据；GR-36 类①冻结 schema） | 六指标 + 标准名 | WaterQuality、EffluentStandard、margin、INDICATORS、InvalidQualityError |
| `core/waterprint/contracts/sludge.py` | L0 | 污泥量契约（DS 守恒载体；GR-36 类①冻结 schema） | Q_wet/DS/含水率 | SludgeFlow、make_sludge、mix、InvalidSludgeError |
| `core/waterprint/contracts/ports.py` | L0 | 端口与边契约（水/泥类型、回流标记、连接合法性唯一裁判；Edge.recycle=边拓扑标记/Port.recycle=端口声明倾向分工 T6 D1；GR-36 类①冻结 schema，含连接校验语义） | 端口声明/连线意图 | Port、PortRef、Edge（含 recycle 边标记）、FluidKind、Direction、validate_edge、InvalidConnection |
| `core/waterprint/contracts/unit_api.py` | L0 | 单元计算协议（UnitContext→UnitResult）+ 警告结构（UF-17：Severity/Warning 三必带；GR-36 类②跨层协议） | 上游量+参数+工况 | UnitContext、UnitResult、Unit、Severity、Warning |
| `core/waterprint/contracts/manifest.py` | L0 | 模组清单 schema 正门（加载即静态校验：R1a~R1e/R4；校验器机器部分 T4 拆至 manifest_validation.py，公开 schema 面不动；GR-36 类①冻结 schema） | 清单数据 | ParamSpec、ConditionMapping、UnitManifest、load_manifest、bind_dimension_lookup、InvalidUnitConfig（后两者为 manifest_validation 再导出） |
| `core/waterprint/contracts/manifest_validation.py` | L0 | manifest 冻结 schema 的静态校验器集 + 装配槽（GR-36 类①；T4 拆分自 manifest.py 纯移动，bind_dimension_lookup 单槽 bind-once） | 清单数据节点 | 守卫器/键集常量/InvalidUnitConfig、bind_dimension_lookup（经 manifest.py 再导出） |
| `core/waterprint/contracts/condition.py` | L0 | 工况契约（ADR-007：2+k 语义、condition_key 稳定键；GR-36 类①冻结 schema） | 工况轴取值 | FlowCase、OperatingCondition、ConditionSet、build_condition_set、InvalidUnitConfig（同层引用：manifest 再导出，定义在 manifest_validation） |
| `core/waterprint/contracts/project_schema.py` | L0 | 项目文件 design/view 双态 schema（pydantic strict+extra=forbid 严格校验；UF-40 零偏移 UTC 收紧 T7a；GR-36 类①冻结 schema） | 项目 JSON | ProjectFile、DesignState、ViewState、Metadata（含 migrated_from——GR-21 只增，v1 恒 None）、parse_project |
| `core/waterprint/contracts/result_schema.py` | L0 | 全厂结果与计算迹 schema（全架构总线；确定性序列化正门 R3/R6；deserialize 内层三键必在 D4；GR-36 类①冻结 schema） | 引擎产出 | PlantResult、UnitResultSnapshot、TraceNode、ReproTriple、serialize、deserialize、InvalidResultError |
| `core/waterprint/contracts/expr.py` | L0 | 共享受限表达式求值器（公式/工况映射 DSL 的唯一解析求值内核；GR-36 类③受限 DSL 内核） | 表达式字符串+允许名集合+数值绑定 | 校验归一后 AST、float/bool 求值值、ExprSyntaxError |
| `core/waterprint/contracts/trace_api.py` | L0 | 计算迹协议（TraceSink/TraceNodeSpec：registry 与迹收集器的唯一耦合面；GR-36 类②跨层协议） | 公式应用事件（id/工况/实参/结果） | 协议与快照数据类定义 |
| `core/waterprint/contracts/run_env.py` | L0 | 执行环境上下文契约 RunEnv（装配一次、执行期只读；GR-36 类②跨层协议——L3 executor/enumerate 与 L4 app 共用，SENS-B 2026-08-23 UF-31；data_version 聚合口径=包名排序后 name@version 以 + 拼接，UF-10 T4 冻结；T7a 实现——L0 不 import L1，系数库经协议耦合） | 引擎/数据版本+假设/系数/单价+迹收集器 | RunEnv（七字段）、CoefficientsView、CoefficientValueView、EngineParam、InvalidRunEnvError |
| `core/waterprint/contracts/drawing_projection.py` | L0 | UF-32 出图取数对照契约聚合正门（Ruling ① 方案②；M3D1 分线拆分正解=app→app_enumeration 伴生件同款：PROJECTION_TABLE=市政/矿井/污泥/输送四分线表聚合，**32 单元[13+8+7+4]三线+市政全覆盖收口**[输送 4 为 M3D3 本批，重写计划 §7 验收行达成]、正门公式不动——聚合无静默覆盖由分线 disjoint 测试守卫（四线）+32/32 收口断言[len==32 且四线 13+8+7+4]；四符号再导出保持消费方 import 路径不变；GR-36 类①冻结 schema） | 分线表 municipal/mine/sludge/conveyance+types 类型面 | UnitProjection、PROJECTION_TABLE、ProfileStation、ElevationProfile |
| `core/waterprint/contracts/drawing_projection_types.py` | L0 | UF-32 类型面（M3D1 D1 拆出：UnitProjection 六字段基型[Mapping 只读快照+drawn_keys]/ProfileStation/ElevationProfile 纵断 L0 类型——elevation 与 drafting 共同消费，L3 互不 import 解法；GR-36 类①冻结 schema） | quantity DimKey+result_schema TraceNode+unit_api Warning | UnitProjection、ProfileStation、ElevationProfile |
| `core/waterprint/contracts/drawing_projection_municipal.py` | L0 | UF-32 市政线取数表（M3D1 D1 迁出：MUNICIPAL_PROJECTIONS 13 条目五类取数+量纲列冻结声明——cugeshan/xigeshan 同构不合并；GR-36 类①冻结 schema） | 市政单元 dims 键全量实跑提取（2026-08-26，249 键） | MUNICIPAL_PROJECTIONS |
| `core/waterprint/contracts/drawing_projection_mine.py` | L0 | UF-32 矿井水线取数表（M3D1 D2 新增：MINE_PROJECTIONS 8 条目五类取数+量纲列冻结声明；GR-36 类①冻结 schema） | 矿井单元 dims 键全量实跑提取（2026-08-27 全链单点图，107 键） | MINE_PROJECTIONS |
| `core/waterprint/contracts/drawing_projection_sludge.py` | L0 | UF-32 污泥线取数表（M3D2 D1 新建分线表③：SLUDGE_PROJECTIONS 7 条目五类取数+量纲列冻结声明——衔接链键六量全线 non_drawn/bengzhan 逐槽镜像市政提升泵房行/tuoshui machine 实例语义；量纲真源=7 包 FormulaSpec output_dim 实读 79 条+非公式键市政同名先例；GR-36 类①冻结 schema） | 污泥单元 dims 键全量实跑提取（2026-08-27 全链单点图，112 键） | SLUDGE_PROJECTIONS |
| `core/waterprint/contracts/drawing_projection_conveyance.py` | L0 | UF-32 输送线取数表（M3D3 D1 新建分线表④——战役收口批：CONVEYANCE_PROJECTIONS 4 条目五类取数+量纲列冻结声明——三井 cylinder(d,h_total) 两槽全[peishuijing 井室为体孔口为口 primitive 取井室径 d_well]/peishuiqu 全线唯一 water_depth 语义键=h_water 且无 plan/primitive 半槽[渠长是参数，ziwai 同裁]/穿流校核量与 instance_counts 全空[n 是分流口数非台数]；量纲真源=4 包 FormulaSpec output_dim 实读 35 条[含 _L/_A/_V/_T/_F/_VEL 真量纲]+非公式键 d/d_well 档取整 _L 先例；GR-36 类①冻结 schema） | 输送单元 dims 键全量实跑提取（2026-08-27 输送链实跑，39 键） | CONVEYANCE_PROJECTIONS |
| `core/waterprint/registry/formulas.py` | L1 | 公式注册表：登记/查询/量纲静态校验/apply | 各单元登记项 | FormulaSpec、InvalidFormulaError、register、by_id、validate_all、apply、norm_ref_of（M1b 新增：collector 反查条文号只读面）、ValidationReport |
| `core/waterprint/registry/dimensions.py` | L1 | 维度字段注册表（字段ID/单位/显示键/分类；dtype_of 已实现 T4 D5+dim 归一 D6，预置 pool_length，R1a 查询钩子经 bind_dimension_lookup 装配 bind-once） | 字段声明 | FieldSpec、register_dimension、dimension_of、dtype_of、InvalidDimensionError |
| `core/waterprint/registry/assumptions.py` | L1 | 设计假设清单唯一真源（默认值+出处；UF-08 loop.* 引擎参数三条 T7a 冻结） | 假设声明+项目覆盖 | Assumption、AssumptionSet、DEFAULT_ASSUMPTIONS（4 条：[0] safety.superheight + loop.tolerance/max_iterations/damping）、assumption、TuningImpact、InvalidAssumptionError |
| `core/waterprint/registry/coefficients.py` | L1 | 去除率/经验系数库加载 | YAML 数据包 | Coefficients、data_version、CoefficientValue、load_coefficients、InvalidCoefficientError、require_keys |
| `core/waterprint/graph/topo.py` | L3 | 拓扑排序 + SCC 划分（纯函数；T6 实现：环两分法——非 recycle 环拒/全边 Tarjan） | 节点/边列表 | topological_layers、strongly_connected_components、split_graph（复用 ports.InvalidConnection 拒绝） |
| `core/waterprint/graph/propagate.py` | L3 | 沿边传播水量水质 + 汇流加权混合（工况加权 R1/Kz=max R2/通道隔离 R4/recycle 忽略 R5；T6 实现） | 上游结果+边+工况 | mix、propagate、InvalidPropagationError（污泥汇流走 contracts.sludge.mix） |
| `core/waterprint/graph/loop.py` | L3 | 回路固定点迭代（阻尼/容差/发散诊断；T7b 实现——D1 四参锁定形态+摊平分桶口径） | 回路组+compute 回调+迭代参数 | solve_loop、LoopConfig、LoopDivergence（收敛解或发散诊断三元组） |
| `core/waterprint/graph/nodes.py` | L3 | 内置图节点三 kind 工厂（市政输入/汇流/水质编辑——executor R6"本包内提供"，非单元包，§14.3 归属表；T7b 新建） | kind + design 节点 params（规范单位裸值） | builtin_unit、InvalidNodeError（Unit 协议实例） |
| `core/waterprint/graph/executor.py` | L3 | 图执行编排（工况×拓扑×传播×回路；层-SCC 调度/DSL 工况映射/UF-42 投影/R5 异常隔离；T7b 实现） | design 图+单元注册表+工况集+RunEnv | execute_graph、UnitRegistry（协议）、InvalidExecutionError、PlantResult（design_hash 空串占位由 app 回填） |
| `core/waterprint/graph/incremental.py` | L3 | 脏传播与缓存（仅优化，字节级等价全量） | hash 变更 | 重算范围、ResultCache |
| `core/waterprint/solution/grid.py` | L3 | 自由参数离散网格（≤4^k 护栏） | manifest 离散配置 | 参数矩阵 |
| `core/waterprint/solution/enumerate.py` | L3 | 批量方案计算 → 结果 DataFrame（M2-SOL R1 现实口径：同一 unit.compute 逐网格行驱动——防双轨实质=唯一计算源；apply 向量化增强挂账 UF-36；行级域拒→dims 全 NaN+nan_flag） | 网格+上游上下文 | 结果 DataFrame（M-8 R1 措辞同步） |
| `core/waterprint/solution/constraints.py` | L3 | 布尔约束过滤（含 UI 覆盖、pass_matrix） | DataFrame+约束 | 可行子集+通过矩阵 |
| `core/waterprint/solution/ranking.py` | L3 | 裕度/成本排序与截断（确定性全序） | 可行 DataFrame | 排序结果 |
| `core/waterprint/solution/diagnose.py` | L3 | 无可行解最小冲突集与调参建议 | pass_matrix | DiagnosisReport |
| `core/waterprint/elevation/losses.py` | L3 | 水头损失公式（沿程/局部/堰/孔口） | 几何+流量 | 损失值（挂公式溯源） |
| `core/waterprint/elevation/profile.py` | L3 | 水面/池底/埋深/超高沿程推算 | 图结果+损失+进厂标高 | ElevationProfile |
| `core/waterprint/elevation/pumps.py` | L3 | 提升判定与扬程（跌水 >阈值提示） | 纵断数据 | PumpingPlan |
| `core/waterprint/cost/takeoff.py` | L3 | 工程量提取（按字段 ID，零中文匹配） | 结果 schema | 工程量清单 |
| `core/waterprint/cost/prices.py` | L3 | 定额单价加载与版本管理 | YAML 数据包 | PriceBook、版本 |
| `core/waterprint/cost/estimate.py` | L3 | 分部分项+措施+间接+预备+税汇总 | 工程量+单价+费率 | EstimateSheet |
| `core/waterprint/cost/indicators.py` | L3 | 单位造价指标合理性校核（警告制） | 概算表+指标带 | IndicatorReport |
| `core/waterprint/drafting/styles.py` | L3 | 图层/线型/文字样式基线（GB/T 50001） | — | StyleTable |
| `core/waterprint/drafting/sheets.py` | L3 | 图框/会签栏参数化块库（A0~A4） | 图幅参数 | 图框实体组 |
| `core/waterprint/drafting/plan_view.py` | L3 | 单体平面图生成（manifest 驱动） | 结果 schema+样式 | DXF 实体组 |
| `core/waterprint/drafting/section_view.py` | L3 | 单体剖面图生成（标高唯一真源=Profile） | 结果+标高+样式 | DXF 实体组 |
| `core/waterprint/drafting/site_plan.py` | L3 | 厂区总平面图（M5，接口先冻结） | 布置+结果 schema | DXF 实体组 |
| `core/waterprint/drafting/profile_drawing.py` | L3 | 高程纵断图（四线+标高标注） | 纵断数据 | DXF 实体组 |
| `core/waterprint/drafting/dxf_writer.py` | L3 | ezdxf 封装与落盘（唯一接触点、路径安全） | 实体组+样式 | .dxf 文件 |
| `core/waterprint/geometry/scene.py` | L3 | 场景图 schema 与装配（<100ms） | 结果 schema+假设 | SceneGraph JSON |
| `core/waterprint/geometry/pools.py` | L3 | 池体/渠道/水面几何图元生成 | 结果字段+假设 | 图元+变换列表 |
| `core/waterprint/geometry/internals.py` | L3 | 内部构件布局（实例数来自计算结果） | 结果字段+假设 | InstanceGroup 组 |
| `core/waterprint/network/manning.py` | L3 | 曼宁水力（充满度分档，公式溯源） | 断面+流量 | 流速/坡度/充满度 |
| `core/waterprint/network/solver.py` | L3 | 管径枚举/并联/跌水井判定 | 管段序列 | 设计管径+衔接 |
| `core/waterprint/network/excel_io.py` | L3 | 管网 Excel 读写（模板驱动、防弹） | .xlsx | 管段模型/结果 sheet |
| `core/waterprint/project/io.py` | L4 | 项目文件确定性序列化读写（原子保存+锁探测+大小/深度/常量防弹面；T7a 实现；T7b M-3 拆出 read_project_text——版本门在上层 migrate） | ProjectFile/DesignState/JSON | dumps、loads、save_project、load_project、read_project_text、dumps_design、InvalidProjectError（字节级稳定 JSON） |
| `core/waterprint/project/migration.py` | L4 | format_version 迁移链（链式纯函数框架就位；T7a 实现——v1 零历史迁移器） | 旧版 JSON | migrate、SUPPORTED_VERSIONS、（当前版直通/未来版拒/未知历史版拒） |
| `core/waterprint/project/content_hash.py` | L4 | 设计态内容哈希（三元组成员；T7a 实现——经 io.dumps_design 含版本头） | DesignState | design_hash（sha256 64hex） |
| `core/waterprint/trace/collector.py` | L4 | 计算迹收集（M1b 实现：TraceSink 协议落地+Spec→Node 就地转换[norm_ref 经 formulas.norm_ref_of 反查]+TraceTree=tuple 平铺+collect 正门；零遗漏、确定性） | 公式应用事件（TraceNodeSpec） | TraceCollector、TraceTree、collect、InvalidTraceError |
| `core/waterprint/trace/audit.py` | L4 | 公式溯源审计报告（自包含 HTML） | 迹树+结果 | 审计报告文件 |
| `core/waterprint/trace/calcbook.py` | L4 | Excel 计算书渲染（M1b 实现：模板禁公式拒+{{trace[i].<field>}}/{{summary.<key>}} 冻结占语法+未知占位符拒+字节确定性保存；TEMPLATE_REGISTRY v1 空） | 迹树+结果+模板 | render_calcbook、TEMPLATE_REGISTRY、InvalidTemplateError、.xlsx |
| `core/waterprint/app.py` | L4 | 用例编排：装配 + run_full_calc/load_project+save_project + run_enumeration（唯一装配点，UF-33 方案 A 已落 M2-SOL；T7a 份额=load/save 薄封装+RunEnv 再导出；T7b 份额=assemble/run_full_calc+AssembledGraph/ResultBundle 两字段子集+design_hash 回填+_engine_params 投影+M-3 migrate 路由已落；M1a 份额=_unit_params 系数投影+_CoefficientsUnit 包装（factor.*/removal.* 并入单元 params，D4 裁决）；M2-SOL 份额=装配 grid 档命中校验[Ruling ④]+run_enumeration 编排+app_enumeration 伴生件再导出） | 项目+工况+环境 | AssembledGraph、ResultBundle、assemble、run_full_calc、run_enumeration、export_artifact、EnumerationOptions/EnumerationOutcome（再导出）、ArtifactKindNotReady、InvalidAssemblyError、load_project（migrate 路由+SERVER D2 双闸收口=委托 io 正门）、save_project、RunEnv（再导出）、Constraint/InvalidProjectError/DEFAULT_ASSUMPTIONS（SERVER 批再导出——server 消费面单入口，__all__ 16 名） |
| `core/waterprint/app_enumeration.py` | L4 | UF-33 用例面伴生件（M2-SOL D2；app.py 500 行预算宪法 §2 拆分正解）：枚举选项/产出类型 + export_artifact 分发薄壳（calcbook 接 M1b trace 正门/未就绪 kind 拒）+ upstream_context 上游快照重建（execute_graph 既有产物 UF-42 反解；零 app 依赖防 import 环，类型面注解消费 solution 三模块+trace 正门——I-4 R1 修正；层序登记=SERVER D1 已落[同层并列+ignore_imports 唯一伴生边豁免]） | app 装配产物+结果 | EnumerationOptions、EnumerationOutcome、UpstreamSource、export_artifact、upstream_context、ArtifactKindNotReady、Constraint（SERVER D1 再导出） |
| `core/waterprint/units_lib/__init__.py` | L2 | 单元库包根：四线物理隔离 + discover_units 发现机制唯一入口（T7b 最小实现：骨架包无导出=空注册表合法；M1 实装后自然填充） | 各单元包 __init__ 白名单导出（manifest+make_unit） | discover_units（Mapping[unit_id → (UnitManifest, Unit 工厂)]） |
| `core/waterprint/cli.py` | L4 | 命令行入口（calc/export/new-unit/validate/selfcheck） | argv | 退出码/产物 |

## 2. server 服务层

| 路径 | 唯一职责 | 输入 | 输出 |
|------|----------|------|------|
| `server/waterprint_server/main.py` | 应用工厂与生命周期（SERVER 已实装：进程池[initializer 进度队列注入]/统一异常映射 22 类基+DOMAIN_ERROR_CODES 名义表/契约自检端点==18/structlog/CORS/请求 ID） | Settings | ASGI app（create_app、app、DOMAIN_ERROR_CODES） |
| `server/waterprint_server/settings.py` | 环境配置（路径基点 safe_child 分量白名单/上限 fail-fast/优先级值域/ENGINE_VERSION） | env | Settings、get_settings、safe_child、ensure_directories、ENGINE_VERSION |
| `server/waterprint_server/dump_openapi.py` | OpenAPI 契约导出（SERVER D5：确定性序列化双跑 diff=0；生成物只经本模块入库） | 模块级 app | api-contracts/openapi.json |
| `server/waterprint_server/routers/projects.py` | 项目 CRUD 五端点（薄协议转换，138 行） | pydantic 请求 | 响应=服务 dataclass |
| `server/waterprint_server/routers/calc.py` | 计算/枚举六端点（幂等/取消/分页，149 行） | 任务请求 | 任务句柄/TaskStatus/SolutionPage |
| `server/waterprint_server/routers/exports.py` | 导出五端点（stale 守门/文件流/批量转任务句柄，127 行） | 导出选项 | 文件流/ExportHandle |
| `server/waterprint_server/routers/events.py` | SSE 两端点（X-Accel 头/事件 JSON 化/断连清理，80 行） | 任务订阅 | text/event-stream |
| `server/waterprint_server/routers/scene.py` | 场景图端点（FE1：GET /api/scene/{project_id} 一端点[condition_key 可选——缺省=排序首键回显]；response_model=SceneGraph 经服务层再导出，51 行） | project_id+condition_key | SceneGraph |
| `server/waterprint_server/services/projects.py` | 项目用例（SERVER 实装：design_digest=content_hash B4 双胞胎[UF-47]/深度闸/锁 409/import_legacy M4 未就绪） | 项目 id/数据 | SaveOutcome/ProjectSummary/ValidationReport |
| `server/waterprint_server/services/calculation.py` | 计算用例（幂等键/快照绑定/消费时 stale/apply 事务回滚；TaskStatus 再导出） | 项目+工况 | TaskHandle/ApplyOutcome |
| `server/waterprint_server/services/enumeration.py` | 枚举用例（多单元 422[ADR-005]/分页白名单/feather 重载/无解 done+诊断[UF-48 随载荷交付]） | 枚举请求 | TaskHandle/SolutionPage/诊断 |
| `server/waterprint_server/services/exports.py` | 导出用例（stale 409+force 标注/确定性命名/单产物上限 1 转任务/元数据边车） | 导出请求 | ExportHandle/ExportMeta |
| `server/waterprint_server/services/scene.py` | 场景图用例（FE1：最近结果集取数[exports 同款模式复制]/假设合成视图[worker._build_env 同款]/core.build_scene 纯投影；无结果 404/工况非法 422/确定性继承，93 行） | 项目 id+工况键 | core.SceneGraph |
| `server/waterprint_server/jobs/manager.py` | 任务注册表与调度（状态机单向/优先级堆同级 FIFO/幂等键/mp.Queue→asyncio 桥[run_coroutine_threadsafe]/文件取消令牌/SSE 背压丢旧保新） | TaskRequest | TaskStatus/Event 流 |
| `server/waterprint_server/jobs/worker.py` | 进程池入口（run_task 三参 pickle 边界唯一面/kind 映射表集中一处经 app[UF-33]/RunEnv 协议适配器[UF-46]/阶段取消轮询[UF-49]/feather+serialize 原子落盘/导入零副作用） | payload+令牌 | 结果+进度 |

## 3. units_lib 单元包登记（按包，非逐文件）

单元包内部结构固定（§13.6：manifest/compute/constraints/README/tests×2），
**每新增一个单元包在此表加一行**（路径写包目录，带斜杠）；包内结构由
check_structure 按 §13.6 校验，不逐文件登记。

| 包路径 | 业务线 | 里程碑 |
|--------|--------|--------|
| `core/waterprint/units_lib/_template/` | 模板（不注册） | M0 |
| `core/waterprint/units_lib/municipal/cugeshan/` | 市政污水 | M1 先行示范（M1a 已实装：CG-F1~F14 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/xigeshan/` | 市政污水 | M1 先行示范（M1a 已实装：XG-F1~F14 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/chenshachi/` | 市政污水 | M1 先行示范（M1a 已实装：CS-F1~F18 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/chuchenchi/` | 市政污水 | M2a2 已实装（CC-F1~F18 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/tiaojiechi/` | 市政污水 | M2b2 已实装（TJ-F1~F13 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/aao/` | 市政污水 | M2a2 已实装（AO-F1~F14 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/cass/` | 市政污水 | M2c 已实装（CA-F1~F27 公式注册+manifest[池数/周期 grid 档 Ruling④]/compute[时段和=周期域拒+滗水 1/3 池深双控]/包内 golden 测试 15 例）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/gaomidu/` | 市政污水 | M2b2 已实装（GM-F1~F20 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/vxinglvchi/` | 市政污水 | M2b2 已实装（XL-F1~F19 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/ziwai/` | 市政污水 | M2b2 已实装（ZW-F1~F13 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/erchunchi/` | 市政污水 | M2a2 已实装（EC-F1~F15 公式注册+manifest/compute/包内 golden 测试）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/bashi_jiliangcao/` | 市政污水 | M2c 已实装（BL-F1~F9 公式注册+B7 七档 C/n 档表消费+包内 golden 测试 12 例——七档流量式各一断言）/ M2 正式验收 |
| `core/waterprint/units_lib/municipal/wushui_tisheng/` | 市政污水 | M2c 已实装（TS-F1~F14 公式注册+泵扬程三分量[M2b1 追认点 14 承接]+比阻 DN 档表命中+包内 golden 测试 12 例）/ M2 正式验收 |
| `core/waterprint/units_lib/mine_water/input/` | 矿井水 | M3a2 已实装（KI-F1~F7 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/tiaojiechi/` | 矿井水 | M3a2 已实装（KT-F1~F12 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/chenshachi/` | 矿井水 | M3a2 已实装（KC-F1~F10 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/ningjiao/` | 矿井水 | M3a2 已实装（KN-F1~F15 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/cifenli/` | 矿井水 | M3a3 已实装（KS-F1~F8 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/gaomidu/` | 矿井水 | M3a3 已实装（KG-F1~F10 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/vxinglvchi/` | 矿井水 | M3a3 已实装（KV-F1~F11 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/mine_water/ziwai/` | 矿井水 | M3a3 已实装（KZ-F1~F11 公式注册+manifest/compute/包内 golden 测试）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/hebing/` | 污泥 | M3b2 已实装（HB-F1~F13 公式注册+图源参数注入+包内 golden 测试 11 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/shusong/` | 污泥 | M3b2 已实装（ST-F1~F9 公式注册+DN25 档收口+包内 golden 测试 13 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/bengzhan/` | 污泥 | M3b2 已实装（BZ-F1~F18 公式注册+泵族先例形态+包内 golden 测试 12 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/nongsuo/` | 污泥 | M3b2 已实装（NS-F1~F12 公式注册+双主线取大+sup 回流口声明先行+包内 golden 测试 12 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/xiaohua/` | 污泥 | M3b2 已实装（XH-F1~F11 公式注册+t_digest_temp 参数承载+包内 golden 测试 12 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/tuoshui/` | 污泥 | M3b2 已实装（TU-F1~F8 公式注册+双机档 grid+filtrate 回流口声明先行+包内 golden 测试 12 例）/ M3 正式验收 |
| `core/waterprint/units_lib/sludge/ganhua/` | 污泥 | M3b2 已实装（GH-F1~F8 公式注册+热量衡算主线+包内 golden 测试 12 例）/ M3 正式验收 |
| `core/waterprint/units_lib/conveyance/jishuijing/` | 集配水 | M3c 已实装（JS-F1~F7 公式注册+汇流单口穿流+包内 golden 测试 10 例）/ M3 正式验收 |
| `core/waterprint/units_lib/conveyance/peishuijing/` | 集配水 | M3c 已实装（PJ-F1~F12 公式注册+动态多口分流[表内冻结口径]+包内 golden 测试 11 例）/ M3 正式验收 |
| `core/waterprint/units_lib/conveyance/jipeishuijing/` | 集配水 | M3c 已实装（JP-F1~F9 公式注册+汇流/分流合一动态多口+包内 golden 测试 11 例）/ M3 正式验收 |
| `core/waterprint/units_lib/conveyance/peishuiqu/` | 集配水 | M3c 已实装（PQ-F1~F7 公式注册+明渠侧堰动态多口+包内 golden 测试 11 例）/ M3 正式验收 |

> 32 个单元包于 M0.5 结构接线期按 _template 模式批量落地为骨架
> （包内仅契约头 + 单元规格，公式与数值随里程碑交付冻结）；
> 单元业务身份总表见 `docs/structure-graph.md` §3（三方互验：
> 本表 ↔ units_lib 目录 ↔ 结构图谱）。

## 4. scripts 门禁脚本（纯标准库）

| 路径 | 唯一职责 |
|------|----------|
| `scripts/gate_patterns.py` | 占位符/裸异常/乱码特征串的集中定义（拼接构造避免自匹配） |
| `scripts/check_file_budgets.py` | 文件行数 ≤500（compute.py ≤400）门禁 |
| `scripts/check_contract_headers.py` | 模块契约头（职责/输入/输出三段）存在性门禁 |
| `scripts/check_grep_gates.py` | grep 门禁：占位/裸 except/乱码计数 = 0 |
| `scripts/check_structure.py` | 目录结构与本表双向同步门禁 |
| `scripts/check_module_graph.py` | 结构图谱门禁（层序/无环/双源一致/单元三方互验/调用链路径） |
| `scripts/check_webapp.py` | webapp 结构门禁（TS 契约头 + features 互不依赖分层） |
| `scripts/check_magic_numbers.py` | 魔法数字门禁（代码数值字面量仅限 registry/quantity/units_lib manifest 真源区 + drafting styles/sheets 声明面——DRAFT 批总控问询放行 2026-08-26） |
| `scripts/check_readonly.py` | 测试只读 manifest 与属性校验 |
| `scripts/check_ruff.py` | ruff 门禁：core venv 解释器跑 CI 同款 ruff check（透传） |
| `scripts/lock_tests.py` | 生成/刷新只读 manifest 并设置只读属性（仅人类执行） |
| `scripts/run_gates.py` | 门禁聚合入口（一键跑全部） |

## 5. webapp（M0.5 起机器检查：scripts/check_webapp.py）

- **契约头**：`webapp/src` 下每个 .ts/.tsx 首块 `/** … */` 必含 职责/输入/输出
  （`shared/api/generated/` 生成物与 `vite-env.d.ts` 豁免）；
- **分层（§13.5）**：features 互不 import、features 不向上 import app、
  shared 不 import features/app、入口 main.tsx 只 import app/**；
- 逐文件职责见 `webapp/src/app/README.md` 与各 feature/shared README 的
  文件清单（M0.5 已全部落地为规格骨架）；硬规则（≤500 行、类型单源）
  另由行数门禁与 CI 构建强制。
