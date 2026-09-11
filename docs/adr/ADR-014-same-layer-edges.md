# ADR-014：同层边一等公民化（唯一声明面+生成器+双向校验）

- 状态：**Accepted**（授权链=深度审计建议 B3「同层边一等公民」→总控裁决
  《审计裁决与治理优化规划_GLM5.3.md》B-6→GOV2 批设计件呈裁
  （.workflow/gov2-same-layer-design.md）→用户裁定方案 A「声明块+生成器」
  2026-09-12）。
- 背景：
  - 同层边（跨节点、同层 token 的合法依赖边）共 4 条，历史上每条需在
    3 处手工同步：core/pyproject.toml 两契约 ignore_imports（layers 全量
    +L3 independence 子集）+docs/structure-graph.md §1b 后散置注记+
    scripts/check_module_graph.py `_SAME_LAYER_EXEMPTS` 硬编码。
  - 漏同步的反馈面分裂：pyproject 漏=CI import-linter 红（慢反馈）；
    check_module_graph 漏=本地门禁红；structure-graph 漏=图谱与机器面
    漂移（审计熵——深度审计 P0 风险②「治理面熵增」的具体面之一）。
  - 边界：同节点伴生边（B7 services.exports→exports_registry 等，节点
    粒度内拆件）由 check_real_imports 的「同节点忽略」天然豁免，无
    3 处同步问题，不入本机制。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **唯一声明面=structure-graph.md §1c 机器声明块**（toml 围栏块：from/to/note/independence/glob 五字段） | 宪法 §13 已定位「三层关系单一事实源=structure-graph.md」——同层边真源住图谱是既定定位的自然延伸；独立数据文件方案被否（真源外移=新双源） |
| D2 | **check_module_graph 解析块替代硬编码**：`_SAME_LAYER_EXEMPTS` 删除；块缺失/空/非同层边/重复=FAIL（fail-closed） | 真实 import 校验语义不变（同层边仍不入 §1b 边表，「严格向下」规则不放开）；同层性校验防把向下边塞进声明块绕过边表 |
| D3 | **pyproject 标记段=生成物**：`scripts/gen_same_layer_edges.py` 自 §1c 块展开两契约 ignore_imports 的 `SAME-LAYER-EDGES:BEGIN/END` 标记段（条目注释由 note 生成；幂等）；check_module_graph 新增双向对照（layers 应恰含全部边、L3 independence 应恰含 independence=true 边，多/少即 FAIL） | 「机器展开」目标落地：新增边=编辑声明块+跑生成器（3 处手工→1 处声明+1 命令）；忘跑生成器=门禁红（CI 与本地同拦）；标记段内手编由「多出」面拦截 |
| D4 | **glob 字段承载 importer 通配语义**（grimp 精确模块匹配——包子模块为实际 import 现场的边需 `<from>.*`，先例 ifc_export.builder） | 通配与否是 import-linter 工具链行为差异，必须活在声明面而非生成器猜测 |

- 后果：
  - 正面：同层边新增同步点 3→1；漂移面机器拦截（缺失/多出/空块三面
    变异验证全红实录）；§1b 后 4 段散置注记压缩为 1 段机制说明（历史
    原文入 git 历史+note 字段）。
  - 代价：gen_same_layer_edges.py 新件登记（file-contracts §4）；
    check_module_graph 增一面（§1c 完整性+pyproject 双向对照）。
  - 首跑实录：4 条既有边迁入声明块，pyproject 由生成器重写（条目集合
    语义等价，lint-imports 5 kept 不变）；幂等性 md5 双跑恒同实证。
