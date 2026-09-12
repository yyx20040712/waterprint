# ADR-017：structure-graph §1a 节点表生成化（契约展开+渲染比对）

- 状态：**Accepted**（授权链=深度审计建议 B1「§1a 节点表可从 find +
  pyproject 契约半自动生成」→总控裁决《审计裁决与治理优化规划_GLM5.3.md》
  B-4 纳入 P1 路线图→GOV4 批 2026-09-12）。
- 背景：
  - §1a 节点表（25 节点：webapp/服务器五模块/内核 17 模块/data/
    api-contracts）与目录结构一一对应，层归属与 core/pyproject layers
    契约双源一致（check_module_graph a 面双向校验）——**派生数据以
    主数据的姿态手工维护**：新增节点（如 L5c ifc_export）须双处同步，
    漏一处=CI 红（反馈分裂：pyproject 漏=慢反馈，图谱漏=本地红）。
  - 宪法 §13 定位「三层关系单一事实源=structure-graph.md」的实义是
    §1b 边表+§1c 同层声明（真正的架构**决策**住图谱）；§1a 的层归属
    是 import-linter **实际消费面**（pyproject 契约）的人类可读投影。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **§1a 数据行=生成物**：`scripts/gen_structure_nodes.py` 自两 pyproject 的 layers 契约（恰一校验）+固定三叶节点（webapp/data/api-contracts）展开；工序=改契约 → 跑生成器 → 门禁绿 | 层归属真源=import-linter 实际消费的契约面；§1a 转为其投影——新增节点手工面从「图谱+pyproject 双处」降为「契约一处+一条命令」（ADR-014 同型工序） |
| D2 | **标记段禁手编**：STRUCT-NODES:BEGIN/END（HTML 注释）内=生成物；段外（表头说明/层序注记/§1b/§1c）仍手维护；标记缺失=fail-closed 红 | 生成物边界机器可判；HTML 注释不渲染不碍表格解析 |
| D3 | **渲染单源=structure_nodes_lib.py**（共享库）：check_module_graph 新增 h 面比对「标记段内容↔渲染输出」；取数/渲染/LAYER_ORDER/CORE_LAYER_OF_TOKEN 全部单源化迁入库（校验端旧本地常量删除防漂） | 校验端与生成端两套解析必漂（same_layer_lib 设立动机同型）；fail-closed：layers 契约多份/组数超 token 映射（层重构）/幽灵模块=拒并报 |
| D4 | **固定三叶不入任何契约**：webapp（L6）/data（DATA）/api-contracts（CONTRACT）为库内 FIXED_NODES 常量声明 | 三者无 import-linter 契约可派生（非 Python 模块）；路径变更=显式改常量过评审 |

- 后果：
  - 正面：§1a 手工编辑面归零（改层归属只动 pyproject 契约+跑生成器）；
    手编标记段/改契约忘跑生成器=门禁 h 面红（变异实录：改一行路径→
    双面红[路径不存在+渲染不符]→生成器还原→绿）。
  - 代价：structure_nodes_lib.py+gen_structure_nodes.py 两新件登记
    （file-contracts §4）；check_module_graph 增 h 面（门禁数不增——
    挂在既有 check_module_graph 内）。
  - 首跑实录：渲染输出与手维护 25 节点表**逐字节一致**（零内容漂移
    接驳——构造性保证：同层内保持 pyproject 声明序的稳定排序）；幂等
    重跑零 diff。
  - 与 check_pyproject_sync（a 面）关系：h 面自 pyproject 派生，语义上
    蕴含 core 侧 a 面；a 面保留（独立实现互证，冗余=自校验面）。
