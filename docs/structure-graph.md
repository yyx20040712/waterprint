# 结构图谱（模块依赖 · 端到端调用链 · 业务单元映射）

> **机器校验对象**：`scripts/check_module_graph.py`（接入 `scripts/run_gates.py`
> 与 CI gates job）。本文件回答三层关系：
> **§1 谁允许依赖谁**（与 core/pyproject.toml 的 import-linter 契约双源一致）、
> **§2 一次业务动作依次经过哪些文件**、**§3 32 个单元包的业务身份**。
>
> 规则（AGENTS.md §13）：改依赖先改本图谱；实现期真实 import 必须是 §1
> 声明边的子集；新单元先登记 §3 与 file-contracts.md §3，再建目录。

## 1. 模块依赖图

### 1a. 节点表

| 节点 | 层 | 对应路径 |
|------|----|----------|
| `webapp` | L6 | `webapp/src` |
| `waterprint_server.main` | L5.main | `server/waterprint_server/main.py` |
| `waterprint_server.routers` | L5.routers | `server/waterprint_server/routers` |
| `waterprint_server.services` | L5.services | `server/waterprint_server/services` |
| `waterprint_server.jobs` | L5.jobs | `server/waterprint_server/jobs` |
| `waterprint_server.settings` | L5.settings | `server/waterprint_server/settings.py` |
| `waterprint.cli` | L4.cli | `core/waterprint/cli.py` |
| `waterprint.app` | L4.app | `core/waterprint/app.py` |
| `waterprint.project` | L4.project-trace | `core/waterprint/project` |
| `waterprint.trace` | L4.project-trace | `core/waterprint/trace` |
| `waterprint.graph` | L3 | `core/waterprint/graph` |
| `waterprint.solution` | L3 | `core/waterprint/solution` |
| `waterprint.elevation` | L3 | `core/waterprint/elevation` |
| `waterprint.cost` | L3 | `core/waterprint/cost` |
| `waterprint.drafting` | L3 | `core/waterprint/drafting` |
| `waterprint.geometry` | L3 | `core/waterprint/geometry` |
| `waterprint.network` | L3 | `core/waterprint/network` |
| `waterprint.units_lib` | L2 | `core/waterprint/units_lib` |
| `waterprint.registry` | L1 | `core/waterprint/registry` |
| `waterprint.contracts` | L0 | `core/waterprint/contracts` |
| `data` | DATA | `data` |
| `api-contracts` | CONTRACT | `api-contracts` |

> 层序（自上而下）：L6 → L5.main → L5.routers → L5.services → L5.jobs →
> L5.settings → L4.cli → L4.app → L4.project-trace → L3 → L2 → L1 → L0 →
> DATA → CONTRACT。依赖边只许沿层序向下（§1b 由门禁强制）。

### 1b. 依赖边表（声明允许的依赖；未声明的 import = 违规）

| from | to | 关系 |
|------|----|------|
| `webapp` | `api-contracts` | orval 自 OpenAPI 生成 TS 客户端（类型单源，禁手写） |
| `waterprint_server.main` | `waterprint_server.routers` | 应用工厂挂载路由 |
| `waterprint_server.main` | `waterprint_server.services` | 依赖注入装配服务 |
| `waterprint_server.main` | `waterprint_server.jobs` | 生命周期内创建/销毁进程池 |
| `waterprint_server.main` | `waterprint_server.settings` | 读取配置装配应用 |
| `waterprint_server.main` | `api-contracts` | 启动契约自检并导出 OpenAPI（M2 起） |
| `waterprint_server.routers` | `waterprint_server.services` | 薄协议转换，只调服务（禁业务逻辑） |
| `waterprint_server.services` | `waterprint_server.jobs` | 计算用例向任务管理器提交 |
| `waterprint_server.services` | `waterprint_server.settings` | 输出目录与上限等配置 |
| `waterprint_server.services` | `waterprint.app` | 进程内调用内核 L4（非 RPC，零胶水） |
| `waterprint_server.jobs` | `waterprint.app` | worker 进程执行内核用例（序列化边界） |
| `waterprint_server.jobs` | `waterprint_server.settings` | 池大小/队列等配置 |
| `waterprint.cli` | `waterprint.app` | 命令编排调用用例（经唯一装配点） |
| `waterprint.cli` | `waterprint.contracts` | 参数与项目 schema 校验 |
| `waterprint.cli` | `waterprint.drafting` | export 命令出图 |
| `waterprint.cli` | `waterprint.network` | 管网子工具命令 |
| `waterprint.app` | `waterprint.units_lib` | 唯一装配点：单元发现/实例化/注入 |
| `waterprint.app` | `waterprint.graph` | 图执行编排 |
| `waterprint.app` | `waterprint.solution` | 方案枚举用例 |
| `waterprint.app` | `waterprint.elevation` | 高程用例 |
| `waterprint.app` | `waterprint.cost` | 概算用例 |
| `waterprint.app` | `waterprint.drafting` | 出图用例 |
| `waterprint.app` | `waterprint.geometry` | 三维场景用例 |
| `waterprint.app` | `waterprint.project` | 项目装载与确定性序列化 |
| `waterprint.app` | `waterprint.trace` | 计算迹收集与导出 |
| `waterprint.app` | `waterprint.registry` | 假设/公式/系数装载 |
| `waterprint.app` | `waterprint.contracts` | 契约类型 |
| `waterprint.project` | `waterprint.contracts` | 项目 schema 校验 |
| `waterprint.trace` | `waterprint.contracts` | 结果与迹节点 schema |
| `waterprint.trace` | `waterprint.registry` | 公式溯源查询（条文号） |
| `waterprint.trace` | `data` | Excel 计算书模板（templates 数据包） |
| `waterprint.graph` | `waterprint.contracts` | unit_api 协议与量/水质契约 |
| `waterprint.solution` | `waterprint.contracts` | manifest 离散配置与结果契约 |
| `waterprint.elevation` | `waterprint.contracts` | 结果契约（标高唯一真源） |
| `waterprint.cost` | `waterprint.contracts` | 结果契约字段 ID 取数 |
| `waterprint.cost` | `data` | 定额单价（unit_prices 数据包） |
| `waterprint.drafting` | `waterprint.contracts` | 结果契约与端口语义 |
| `waterprint.geometry` | `waterprint.contracts` | 结果 schema 纯投影 |
| `waterprint.network` | `waterprint.contracts` | 仅共享量与单位（独立域） |
| `waterprint.units_lib` | `waterprint.contracts` | 端口/工况/manifest 契约 |
| `waterprint.units_lib` | `waterprint.registry` | 假设默认值与公式注册表 |
| `waterprint.registry` | `waterprint.contracts` | 量纲签名静态校验 |
| `waterprint.registry` | `data` | 去除率/经验系数（coefficients 数据包） |

> L3 七个子系统互不依赖（independence 契约），各自只消费 L0 契约；
> 单元包互相独立；pint 只在 contracts.quantity 出现——三条铁律由
> import-linter 强制，本图谱与之一致（门禁双源对照）。

## 2. 端到端调用链（一次业务动作经过的文件，路径均实际存在）

| 场景 | 链路（自上而下） |
|------|------------------|
| 全流程计算（F5） | `webapp/src/features/canvas` → `server/waterprint_server/routers/calc.py` → `server/waterprint_server/services/calculation.py` → `server/waterprint_server/jobs/manager.py` → `server/waterprint_server/jobs/worker.py` → `core/waterprint/app.py` → `core/waterprint/graph/executor.py` → `core/waterprint/units_lib`（各单元 compute）→ `core/waterprint/contracts/result_schema.py` → `core/waterprint/trace/collector.py`；进度经 `server/waterprint_server/routers/events.py`（SSE）推送 |
| 方案枚举 | `webapp/src/features/solutions` → `server/waterprint_server/routers/calc.py` → `server/waterprint_server/services/enumeration.py` → `core/waterprint/solution/grid.py` → `core/waterprint/solution/enumerate.py` → `core/waterprint/solution/constraints.py` → `core/waterprint/solution/ranking.py`（无可行解走 `core/waterprint/solution/diagnose.py`） |
| 导出计算书 | `webapp/src/features/drawings` → `server/waterprint_server/routers/exports.py` → `server/waterprint_server/services/exports.py` → `core/waterprint/trace/calcbook.py` → `data/templates`（模板驱动，禁 Excel 公式） |
| 图纸导出（DXF） | `server/waterprint_server/routers/exports.py` → `server/waterprint_server/services/exports.py` → `core/waterprint/drafting/plan_view.py` / `core/waterprint/drafting/section_view.py` → `core/waterprint/drafting/dxf_writer.py`（全库唯一 ezdxf 接触点） |
| 项目保存/加载 | `webapp/src/app` → `server/waterprint_server/routers/projects.py` → `server/waterprint_server/services/projects.py` → `core/waterprint/project/io.py` → `core/waterprint/project/content_hash.py`（dirty 判定）→ `core/waterprint/project/migration.py`（旧版本升级链） |
| 管网水力子工具 | `core/waterprint/cli.py`（独立命令）→ `core/waterprint/network/excel_io.py` → `core/waterprint/network/solver.py` → `core/waterprint/network/manning.py`（不共享厂区图引擎） |

## 3. 业务单元总表（32 包；与 file-contracts.md §3、units_lib 目录三方互验）

| 包路径 | 业务线 | 中文名 | 旧 mod | 里程碑 | golden 绑定 | 典型上下游 |
|--------|--------|--------|--------|--------|-------------|------------|
| `core/waterprint/units_lib/municipal/cugeshan/` | 市政污水 | 粗格栅 | `cugeshan` | M2 | municipal_34760 | 市政输入节点或 wushui_tisheng 提升泵房 → xigeshan 细格栅 |
| `core/waterprint/units_lib/municipal/xigeshan/` | 市政污水 | 细格栅 | `xigeshan` | M2 | municipal_34760 | cugeshan 粗格栅 → chenshachi 旋流沉砂池 |
| `core/waterprint/units_lib/municipal/chenshachi/` | 市政污水 | 旋流沉砂池 | `chenshachi` | M2 | municipal_34760 | xigeshan 细格栅 → chuchenchi 初沉池或 tiaojiechi 调节池（按工艺配置） |
| `core/waterprint/units_lib/municipal/chuchenchi/` | 市政污水 | 辐流初沉池 | `chuchenchi` | M2 | municipal_34760 | chenshachi 旋流沉砂池 → aao 生物池或 cass 生物池 |
| `core/waterprint/units_lib/municipal/tiaojiechi/` | 市政污水 | 调节池 | `tiaojiechi` | M2 | municipal_34760 | chenshachi 旋流沉砂池 → aao 生物池或 cass 生物池 |
| `core/waterprint/units_lib/municipal/aao/` | 市政污水 | AAO 生物池 | `aao` | M2 | municipal_34760 | chuchenchi 初沉池或 tiaojiechi 调节池 → erchunchi 辐流二沉池 |
| `core/waterprint/units_lib/municipal/cass/` | 市政污水 | CASS 生物池 | `cass` | M2 | municipal_34760 | chuchenchi 初沉池或 tiaojiechi 调节池 → erchunchi 辐流二沉池 |
| `core/waterprint/units_lib/municipal/gaomidu/` | 市政污水 | 高密沉淀池 | `gaomidu` | M2 | municipal_34760 | erchunchi 二沉池或生物池出水 → vxinglvchi V型滤池 |
| `core/waterprint/units_lib/municipal/vxinglvchi/` | 市政污水 | V型滤池 | `vxinglvchi` | M2 | municipal_34760 | gaomidu 高密沉淀池 → ziwai 紫外消毒 |
| `core/waterprint/units_lib/municipal/ziwai/` | 市政污水 | 紫外消毒 | `ziwai` | M2 | municipal_34760 | vxinglvchi V型滤池 → bashi_jiliangcao 巴歇尔计量槽 |
| `core/waterprint/units_lib/municipal/erchunchi/` | 市政污水 | 辐流二沉池 | `erchunchi`（社区） | M2 | municipal_34760 | aao 或 cass 生物池 → gaomidu 高密沉淀池或排放 |
| `core/waterprint/units_lib/municipal/bashi_jiliangcao/` | 市政污水 | 巴歇尔计量槽 | `bashi_jiliangcao`（社区） | M2 | municipal_34760 | ziwai 紫外消毒 → 排放口 |
| `core/waterprint/units_lib/municipal/wushui_tisheng/` | 市政污水 | 污水提升泵房 | `wushui_tisheng`（社区） | M2 | municipal_34760 | 市政输入节点 → cugeshan 粗格栅 |
| `core/waterprint/units_lib/mine_water/input/` | 矿井水 | 矿井水输入 | `kw_input` | M3 | mine_43836 | 线起点（内置输入节点） → tiaojiechi 调节池 |
| `core/waterprint/units_lib/mine_water/tiaojiechi/` | 矿井水 | 调节池 | `kw_tiaojiechi` | M3 | mine_43836 | input 矿井水输入 → chenshachi 平流沉砂池 |
| `core/waterprint/units_lib/mine_water/chenshachi/` | 矿井水 | 平流沉砂池 | `kw_chenshachi` | M3 | mine_43836 | tiaojiechi 调节池 → ningjiao 混凝反应 |
| `core/waterprint/units_lib/mine_water/ningjiao/` | 矿井水 | 混凝反应 | `kw_ningjiao` | M3 | mine_43836 | chenshachi 平流沉砂池 → cifenli 磁分离或 gaomidu 高密沉淀 |
| `core/waterprint/units_lib/mine_water/cifenli/` | 矿井水 | 磁分离 | `kw_cifenli` | M3 | mine_43836 | ningjiao 混凝反应 → gaomidu 高密沉淀 |
| `core/waterprint/units_lib/mine_water/gaomidu/` | 矿井水 | 高密沉淀 | `kw_gaomidu` | M3 | mine_43836 | cifenli 磁分离或 ningjiao 混凝反应 → vxinglvchi V型滤池 |
| `core/waterprint/units_lib/mine_water/vxinglvchi/` | 矿井水 | V型滤池 | `kw_vxinglvchi` | M3 | mine_43836 | gaomidu 高密沉淀 → ziwai 紫外消毒 |
| `core/waterprint/units_lib/mine_water/ziwai/` | 矿井水 | 紫外消毒 | `kw_ziwai` | M3 | mine_43836 | vxinglvchi V型滤池 → 回用或排放 |
| `core/waterprint/units_lib/sludge/hebing/` | 污泥 | 污泥合并 | `wuni_hebing` | M3 | 污泥链全流程 | 各线单元排泥口 → shusong 污泥输送 |
| `core/waterprint/units_lib/sludge/shusong/` | 污泥 | 污泥输送 | `wuni_shusong` | M3 | 污泥链全流程 | hebing 污泥合并 → bengzhan 污泥泵站 |
| `core/waterprint/units_lib/sludge/bengzhan/` | 污泥 | 污泥泵站 | `wuni_bengzhan` | M3 | 污泥链全流程 | shusong 污泥输送 → nongsuo 污泥浓缩 |
| `core/waterprint/units_lib/sludge/nongsuo/` | 污泥 | 污泥浓缩 | `wuni_nongsuo` | M3 | 污泥链全流程 | bengzhan 污泥泵站 → xiaohua 污泥消化或 tuoshui 污泥脱水 |
| `core/waterprint/units_lib/sludge/xiaohua/` | 污泥 | 污泥消化 | `wuni_xiaohua` | M3 | 污泥链全流程 | nongsuo 污泥浓缩 → tuoshui 污泥脱水 |
| `core/waterprint/units_lib/sludge/tuoshui/` | 污泥 | 污泥脱水 | `wuni_tuoshui` | M3 | 污泥链全流程 | xiaohua 污泥消化或 nongsuo 污泥浓缩 → ganhua 污泥干化或外运 |
| `core/waterprint/units_lib/sludge/ganhua/` | 污泥 | 污泥干化 | `wuni_ganhua` | M3 | 污泥链全流程 | tuoshui 污泥脱水 → 外运处置 |
| `core/waterprint/units_lib/conveyance/jishuijing/` | 集配水 | 集水井 | `jishuijing` | M3 | 随各线 golden 覆盖 | 各线来水 → 处理单元或配水设施 |
| `core/waterprint/units_lib/conveyance/peishuijing/` | 集配水 | 配水井 | `peishuijing` | M3 | 随各线 golden 覆盖 | 集水设施或上游处理单元 → 并联处理系列 |
| `core/waterprint/units_lib/conveyance/jipeishuijing/` | 集配水 | 集配水井 | `jipeishuijing` | M3 | 随各线 golden 覆盖 | 各线来水 → 并联处理系列 |
| `core/waterprint/units_lib/conveyance/peishuiqu/` | 集配水 | 配水渠 | `peishuiqu` | M3 | 随各线 golden 覆盖 | 配水井或上游处理单元 → 并联处理系列 |

> 折叠为配置（非单元包）：旧 `jcws_smbg`（进厂水面标高）、`gdys_stss`
> （管道水头损失）→ elevation 子系统输入配置；内置图节点（市政输入/
> 汇流/水质编辑）→ graph 引擎内置类型（§14.3 归属表）。
