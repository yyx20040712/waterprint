# WaterPrint 用户手册

面向最终用户的使用说明：安装、快速开始、核心概念、命令与端点参考、常见问题。

> 事实口径声明：本手册只描述**已实现**的行为（CLI 子命令集 v2 与 API 19 端点，
> 2026-08 实现）；尚未实现的能力一律明确标注"规划中"，不虚构。

## 1. 系统简介

WaterPrint（智水蓝图）是污水处理工艺设计计算平台，分三层：**计算内核**
（`core/`，Python——工艺单元、图引擎、公式注册表）、**服务层**
（`server/`，FastAPI——项目/计算/导出/事件 19 个 HTTP 端点）、**前端**
（`webapp/`，React——工作区界面）。内核也可脱离服务经命令行（`wp`）直接使用。

平台的核心理念是**可审计性**：任何一个输出数字都能沿计算迹回溯到
公式 ID、条文出处与输入快照——计算结果永远绑定"可复算三元组"
（design_hash / engine_version / data_version），同输入必得同输出
（确定性序列化，禁当前时钟）。审计报告（HTML）把这条链路逐条打印成
可核查的文档；四套 golden 基准案例（3.47 万 m³/d 市政、4.38 万 m³/d
矿井水、真环、回流）在测试中逐项对照期望值，作为计算正确性的锚。

## 2. 安装

前置条件：Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)（内核与服务）；
Node.js 与 pnpm（前端，经 corepack 启用）。仓库已内置 `.npmrc`
（npmmirror 镜像、node-linker=hoisted）与 uv 镜像索引配置，国内网络
可直接使用。

```bash
# 计算内核（含全部测试）
cd core && uv sync && uv run pytest

# 服务层（默认监听 http://127.0.0.1:8000）
cd server && uv sync && uv run uvicorn waterprint_server.main:app

# 前端（默认 http://127.0.0.1:5173，已配代理转发到 8000）
pnpm install && pnpm -C webapp dev
```

数据包（系数库 `data/coefficients@1.1.0`、Excel 模板 `data/templates`、
单价库 `data/unit_prices`、约束知识库 `data/constraint_kb`）随仓库内置，
无需单独安装。服务层的数据目录（项目/导出/任务产物）默认在工作目录下
`projects/`、`exports/` 创建。

Windows 控制台建议设置 `PYTHONUTF8=1`（中文输出防 GBK 双重编码乱码）。

## 3. 快速开始

五步走通"建项目 → 提交计算 → 看方案 → 三维场景 → 出审计报告"。
示例用 curl（服务跑在 127.0.0.1:8000）；前端就绪后同样操作在界面完成。

### 3.1 建项目

```bash
# 空项目
curl -X POST http://127.0.0.1:8000/api/projects \
  -H "Content-Type: application/json" -d '{}'
# 返回 {"project_id":"…","content_hash":"…","design_changed":true}

# 或导入既有项目 JSON（如 golden 案例项目文件，包一层 project 字段）
curl -X POST http://127.0.0.1:8000/api/projects \
  -H "Content-Type: application/json" \
  -d "{\"project\":$(cat core/tests/golden/golden_data/municipal_34760/input_project.json)}"
```

项目文件由服务层保存在 `projects/<project_id>.wp.json`。校验（零计算）：

```bash
curl -X POST http://127.0.0.1:8000/api/projects/<project_id>/validate
```

### 3.2 提交计算

```bash
curl -X POST http://127.0.0.1:8000/api/calc/run \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project_id>","conditions":[]}'
# 返回 {"task_id":"…"}（幂等：同 design_hash+conditions 重复提交返回原任务）
```

`conditions` 传受检单元 id 列表（空=只算 design/avg 基线两档；传入后
每单元追加一档离线校核工况）。查进度：

```bash
curl http://127.0.0.1:8000/api/calc/tasks/<task_id>     # 轮询状态
curl -N http://127.0.0.1:8000/api/events/tasks/<task_id> # 或 SSE 事件流
```

任务完成后的状态 JSON 里 `result` 块含 `result_file`（结果文件路径，
serialize 产物）与三元组摘要。

### 3.3 看方案（枚举）

对带自由参数网格的单元（如池型选择类单元的档位组合）列出可行参数并应用：

```bash
curl -X POST http://127.0.0.1:8000/api/calc/enumerate \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project_id>","unit_ids":["<带网格的单元 id>"]}'
curl "http://127.0.0.1:8000/api/calc/tasks/<task_id>/solutions?page=1"
# 选定后原子应用（失败自动回滚，不半写）
curl -X POST http://127.0.0.1:8000/api/calc/solutions/apply \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project_id>","unit_id":"<单元 id>","params":{…}}'
```

注意（显式失败语义，非缺陷）：目标单元没有自由参数时报
"网格声明为空"；网格组合数超过护栏（每维基准组合上限的 k 次方，
k=维数）时报"网格组合数超护栏"——缩小参数范围或减维后重试。
不在项目装配图内的单元 id 同样显式拒绝。

### 3.4 三维场景

```bash
curl "http://127.0.0.1:8000/api/scene/<project_id>?condition_key=design"
```

返回场景图 JSON（最近完成结果集的纯投影：池体/渠道/地面等几何与语义
色）。webapp 的三维视图（React Three Fiber 渲染器、场景图查询、视角
控制）**组件与数据通道已就位，工作区标签接线属后续前端批——规划中**。

### 3.5 出审计报告（CLI）

审计报告经内核命令行生成（自包含 HTML，可离线打开、可直接打印）：

```bash
cd core
uv run python -m waterprint.cli export audit <project.json> <result.json> [--out 报告.html]
```

`<result.json>` 即 3.2 任务状态里的 `result_file`（或任何 serialize
产物）；`<project.json>` 即 `projects/<project_id>.wp.json`。默认输出在
结果文件同目录生成 `<名>.audit.html`。报告含工况分章的公式逐条表
（表达式/输入值/输出值/条文出处）、汇总指标表与可复算三元组。

> 说明：`POST /api/exports/audit` 端点当前返回 501（服务层导出通道
> 归 M4 后续批），CLI 是审计报告的现行正门。

## 4. 核心概念

**项目-设计-工况-方案**：项目文件是双态结构——`design` 态（工艺图：
单元与连线、参数——参与内容哈希，一变即新版本）与 `view` 态（纯视图
偏好——不参与哈希）。工况采用 2+k 语义：基线两档（design 设计档、
avg 平均档）加每个受检单元一条离线校核档（如 `design_offline_municipal_aao`）。
方案指单单元参数的可行组合枚举（分页浏览、选定原子应用），不是多套
全厂备选（语义见 ADR-005）。

**系数包版本**：去除率、系数、单价等数据打包带版本（当前
`coefficients@1.1.0`），与引擎版本一起进结果三元组的 `data_version`。
升级数据包后旧结果不会冒充新结果——导出与消费按三元组实时比对（见
FAQ 第 2 问）。

**golden 基准**：四套端到端案例（市政 34,760 m³/d 一级 A、矿井水
43,836 m³/d 地表水 III 类、市政真环、市政回流）由领域专家录入期望值，
每次测试逐工况逐项对照（双容差不放宽）——它是"计算结果可信"的锚，
也是回归的第一道防线。

## 5. 命令与端点参考

### 5.1 CLI（`wp` = `python -m waterprint.cli`，子命令集 v2）

| 命令 | 用途 | 退出码 |
|------|------|--------|
| `wp network <pipes.xlsx> [--out r.xlsx] [--roughness plastic\|concrete]` | 管网水力设计（读模板表→设计→写结果 sheet） | 0 成功 / 3 读入校验失败 / 4 有无解段 |
| `wp new-unit <line> <name> [--root <units_lib>]` | 从模板生成单元骨架（重名拒绝） | 0 / 2 用法 / 3 校验 / 4 失败 |
| `wp export audit <project.json> <result.json> [--out a.html]` | 审计报告 HTML（M4a 起可用） | 0 / 2 用法 / 3 读入或路径或审计链校验失败 |

未注册的子命令（calc/validate/selfcheck/export 其余 kind）调用即
用法错误（退出码 2）——实装归后续批。

### 5.2 API（19 个端点 = 17 路径 × 方法，v1 冻结）

| 分组 | 端点 |
|------|------|
| projects（3） | `GET/POST /api/projects`、`GET/PUT /api/projects/{id}`、`POST /api/projects/{id}/validate` |
| calc（6） | `POST /api/calc/run`、`POST /api/calc/enumerate`、`GET /api/calc/tasks/{id}`、`POST /api/calc/tasks/{id}/cancel`、`GET /api/calc/tasks/{id}/solutions`、`POST /api/calc/solutions/apply` |
| exports（5） | `GET /api/exports`、`POST /api/exports/calcbook`、`POST /api/exports/audit`、`POST /api/exports/dxf`、`POST /api/exports/estimate` |
| events（2） | `GET /api/events/tasks/{id}`、`GET /api/events/projects/{id}`（SSE） |
| scene（1） | `GET /api/scene/{project_id}` |

### 5.3 导出产物四种 kind 的现行状态

| kind | 状态 | 说明 |
|------|------|------|
| calcbook | API 可用 | Excel 计算书（模板已录入 `data/templates`） |
| audit | CLI 可用；API 501 | HTML 审计报告——`wp export audit` 正门；API 通道归 M4 后续批 |
| dxf | 501 | CAD 图纸（M2 出图批实现，服务模板未录入） |
| estimate | 501 | 概算书（概算核心已实现；导出模板通道未录入——诚实 501） |

导出统一守门：结果集三元组与当前项目不一致且未 `?force=1` 时返回
409；`force=1` 导出的产物文件名与元数据显式标注旧三元组（产物永不
冒充）。产物命名确定性（项目 id+kind+工况+三元组摘要，无时间戳）。

## 6. FAQ（十问）

1. **计算提交后怎么知道完成了？** 轮询 `GET /api/calc/tasks/{id}`，
   或订阅 SSE `GET /api/events/tasks/{id}`（进度百分比+阶段消息）。
   完成态载荷含 `result_file` 与三元组。
2. **导出报 409 stale 是什么？** 最近结果集基于旧 design，当前项目已
   改动。先重新计算；或确实要旧结果时加 `?force=1`（产物会带旧三元组
   标注）。CLI 侧不拒——`wp export audit` 只在 stderr 打警告（审计
   对象就是那份历史计算，报告头部三元组自证版本）。
3. **CLI 退出码什么含义？中文输出乱码？** 0 成功 / 2 用法错误 /
   3 读入或校验失败 / 4 计算失败（诊断信息在 stderr）。乱码请设
   `PYTHONUTF8=1`（Windows GBK 控制台）。
4. **导出产物是什么格式、放在哪？** 服务层产物在 `exports/` 目录：
   calcbook 为 `.xlsx`（同名 `.meta.json` 边车记元数据）；CLI 审计报告
   为自包含 `.html`（内联样式零外链，默认落在结果文件旁）。
5. **审计报告里为什么没有日期，只有三元组？** 确定性理念：同一份结果
   渲染两次字节相同（可 diff、可归档比对）。时间面由
   design_hash/engine_version/data_version 三元组承担，不用当前时钟。
6. **CLI 警告"项目 design hash 与结果三元组不一致"？** 传入的项目
   文件不是产出该结果的版本。报告仍会生成（头部三元组标明实际版本）；
   要对齐当前项目请先重算。
7. **项目文件旁出现 `.lock` 文件？** 并发编辑防护（单用户最低成本
   方案）：该文件存在时，服务层拒绝读取/保存该项目（409，消息带锁
   文件路径即持有者信息）。锁的创建与清理由编辑会话负责；确认没有
   会话占用后可删除。
8. **引擎或数据包升级后，旧项目文件还能用吗？** 项目带 `format_version`
   （当前 1.0）。同版直通；未来版本经迁移链处理；无法识别的版本会被
   拒绝（诚实失败，不猜测语义）。旧**结果**不受影响——三元组自证。
9. **三维场景在哪看？** API 已就绪（`GET /api/scene/{id}`）；webapp
   三维视图的工作区接线属后续前端批——规划中。
10. **怎么自检安装是否成功？** `cd core && uv run pytest` 全量绿；
    或用 golden 案例实跑审计链路：拿 3.2 的 result_file 与项目文件跑
    `wp export audit`，能生成含公式逐条表的 HTML 即通。
