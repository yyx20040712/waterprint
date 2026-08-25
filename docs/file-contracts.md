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
| `core/waterprint/registry/formulas.py` | L1 | 公式注册表：登记/查询/量纲静态校验/apply | 各单元登记项 | FormulaSpec、InvalidFormulaError、register、by_id、validate_all、apply、ValidationReport |
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
| `core/waterprint/solution/enumerate.py` | L3 | 向量化批量计算 → 结果 DataFrame | 网格+上游上下文 | 结果 DataFrame |
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
| `core/waterprint/trace/collector.py` | L4 | 计算迹收集（零遗漏、确定性） | 公式应用上下文 | TraceTree |
| `core/waterprint/trace/audit.py` | L4 | 公式溯源审计报告（自包含 HTML） | 迹树+结果 | 审计报告文件 |
| `core/waterprint/trace/calcbook.py` | L4 | Excel 计算书渲染（模板驱动、禁公式） | 迹树+结果+模板 | .xlsx |
| `core/waterprint/app.py` | L4 | 用例编排：装配 + run_full_calc/load_project+save_project（唯一装配点，UF-33 口径；T7a 份额=load/save 薄封装+RunEnv 再导出；T7b 份额=assemble/run_full_calc+AssembledGraph/ResultBundle 两字段子集+design_hash 回填+_engine_params 投影+M-3 migrate 路由已落；run_enumeration/export_artifact 归 M1/M3） | 项目+工况+环境 | AssembledGraph、ResultBundle、assemble、run_full_calc、InvalidAssemblyError、load_project（migrate 路由）、save_project、RunEnv（再导出） |
| `core/waterprint/units_lib/__init__.py` | L2 | 单元库包根：四线物理隔离 + discover_units 发现机制唯一入口（T7b 最小实现：骨架包无导出=空注册表合法；M1 实装后自然填充） | 各单元包 __init__ 白名单导出（manifest+make_unit） | discover_units（Mapping[unit_id → (UnitManifest, Unit 工厂)]） |
| `core/waterprint/cli.py` | L4 | 命令行入口（calc/export/new-unit/validate/selfcheck） | argv | 退出码/产物 |

## 2. server 服务层

| 路径 | 唯一职责 | 输入 | 输出 |
|------|----------|------|------|
| `server/waterprint_server/main.py` | 应用工厂与生命周期（进程池/异常映射/契约自检） | Settings | ASGI app |
| `server/waterprint_server/settings.py` | 环境配置（路径基点/上限/池大小） | env | Settings |
| `server/waterprint_server/routers/projects.py` | 项目 CRUD 端点（薄协议转换） | pydantic 请求 | pydantic 响应 |
| `server/waterprint_server/routers/calc.py` | 计算/枚举任务端点（幂等/取消/分页） | 任务请求 | 任务句柄/状态 |
| `server/waterprint_server/routers/exports.py` | 导出端点（stale 守门/文件流） | 导出选项 | 文件流 |
| `server/waterprint_server/routers/events.py` | SSE 进度端点（背压/清理） | 任务订阅 | 事件流 |
| `server/waterprint_server/services/projects.py` | 项目用例编排（保存语义/导入） | 项目 id/数据 | 领域结果 |
| `server/waterprint_server/services/calculation.py` | 计算用例（幂等/快照绑定/方案应用原子） | 项目+工况 | 任务句柄/ApplyOutcome |
| `server/waterprint_server/services/enumeration.py` | 枚举用例（单单元守护/分页/arrow） | 枚举请求 | SolutionPage |
| `server/waterprint_server/services/exports.py` | 导出用例（stale 守门/确定性命名） | 导出请求 | ExportHandle |
| `server/waterprint_server/jobs/manager.py` | 任务注册表与进程池调度（优先级队列） | TaskRequest | 状态/事件流 |
| `server/waterprint_server/jobs/worker.py` | 进程池入口（序列化边界/取消协作） | payload+令牌 | 结果+进度 |

## 3. units_lib 单元包登记（按包，非逐文件）

单元包内部结构固定（§13.6：manifest/compute/constraints/README/tests×2），
**每新增一个单元包在此表加一行**（路径写包目录，带斜杠）；包内结构由
check_structure 按 §13.6 校验，不逐文件登记。

| 包路径 | 业务线 | 里程碑 |
|--------|--------|--------|
| `core/waterprint/units_lib/_template/` | 模板（不注册） | M0 |
| `core/waterprint/units_lib/municipal/cugeshan/` | 市政污水 | M1 先行示范 / M2 正式验收 |
| `core/waterprint/units_lib/municipal/xigeshan/` | 市政污水 | M1 先行示范 / M2 正式验收 |
| `core/waterprint/units_lib/municipal/chenshachi/` | 市政污水 | M1 先行示范 / M2 正式验收 |
| `core/waterprint/units_lib/municipal/chuchenchi/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/tiaojiechi/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/aao/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/cass/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/gaomidu/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/vxinglvchi/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/ziwai/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/erchunchi/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/bashi_jiliangcao/` | 市政污水 | M2 |
| `core/waterprint/units_lib/municipal/wushui_tisheng/` | 市政污水 | M2 |
| `core/waterprint/units_lib/mine_water/input/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/tiaojiechi/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/chenshachi/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/ningjiao/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/cifenli/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/gaomidu/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/vxinglvchi/` | 矿井水 | M3 |
| `core/waterprint/units_lib/mine_water/ziwai/` | 矿井水 | M3 |
| `core/waterprint/units_lib/sludge/hebing/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/shusong/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/bengzhan/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/nongsuo/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/xiaohua/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/tuoshui/` | 污泥 | M3 |
| `core/waterprint/units_lib/sludge/ganhua/` | 污泥 | M3 |
| `core/waterprint/units_lib/conveyance/jishuijing/` | 集配水 | M3 |
| `core/waterprint/units_lib/conveyance/peishuijing/` | 集配水 | M3 |
| `core/waterprint/units_lib/conveyance/jipeishuijing/` | 集配水 | M3 |
| `core/waterprint/units_lib/conveyance/peishuiqu/` | 集配水 | M3 |

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
| `scripts/check_magic_numbers.py` | 魔法数字门禁（代码数值字面量仅限 registry/quantity 真源区） |
| `scripts/check_readonly.py` | 测试只读 manifest 与属性校验 |
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
