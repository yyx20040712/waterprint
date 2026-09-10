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

# 服务层（默认只听 http://127.0.0.1:8000——对外绑定须 WATERPRINT_HOST 显式覆盖）
cd server && uv sync && uv run python -m waterprint_server.main

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
护栏基数缺省为每维 7 档（2026-09-09 裁定 4→7，市政 5/7 档单元
开箱即枚举）；项目假设面板可按项目覆盖该基数（键
`solution.grid.base_per_dim`）。
不在项目装配图内的单元 id 同样显式拒绝。

### 3.4 三维场景

```bash
curl "http://127.0.0.1:8000/api/scene/<project_id>?condition_key=design"
```

返回场景图 JSON（最近完成结果集的纯投影：池体/渠道/地面等几何与语义
色）。webapp 的三维视图（React Three Fiber 渲染器、场景图查询、视角
控制）已实装为工作区「三维视图」标签（FE3 批：只读浏览+机位切换+
URL `?project=` 联动）。

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

### 3.6 参数面板「可行域」引导（webapp，FD 批 2026-09-10）

选中单元后，参数面板对**连续区间参数**（声明 min/max 范围且无档位
网格——当前目录 93 个）在参数行提供「可行域」链接入口：

- **1D 区间条**：点击后在该参数行下方展开——绿色段=当前工况与约束
  下计算可行的取值区间，灰色段=不可行；点击区间任意位置把该值回填
  到输入框（点在灰色区自动**吸附**到最近可行段边界，不静默无响应）；
  行尾附可行率（可行点数/总点数）。
- **第二轴 2D 热力图**：展开后在「第二轴」下拉选同单元另一连续参数，
  弹出热力图模态（绿=两参组合可行，灰=不可行；悬停格点显示两参
  取值）；点击格点把两个参数同时回填（不可行格自动吸附最近可行格）。
  模态**不自动关闭**——便于回填后继续微调，手动关闭返回。
- **degraded 标注**：单元没有适用可行性约束时，区间条整条绿色并标注
  「本单元暂无适用可行性约束——绿色区=计算有效域」——诚实呈现降级
  态，绿色不代表约束结论。
- **步长派生口径**：连续参数输入框为数字组件，上下箭头增量恒=
  (max−min)/10（缺省 11 档指引粒度）；键盘可输入任意值不受步长限制
  ——步长只是调参效率指引，不是校验规则（语义校验仍在计算侧）。

接口面：`POST /api/calc/design-map`（同步直返，轴 1~2 个；扫描总点数
上限 2500，超限显式拒绝——项目假设面板可按项目覆盖键
`solution.design_map.max_points`）。

### 3.7 界面主题与滚动行为（webapp，C1 批 2026-09-10）

webapp 全界面采用「**深海工程台**」深色主题（用户裁选——参考 GPS-X/
BioWin 工程软件专业风×原神质感分寸）：

- **配色**：深海军蓝三层底（页面/面板/浮层）+工程蓝主色（按钮/链接/
  焦点）+鎏金点缀（品牌字、选中态描边、标签指示条——仅品牌点缀，
  不与流程语义色混用）；语义色纪律不变（绿合格/橙警告/红错误/蓝水线
  /棕泥线）；
- **布局骨架**：顶栏（水滴标+「智水蓝图 WaterPrint」双语名+当前项目
  徽章+连接设置齿轮）+左侧单元库（232px，四线分组树+搜索）+中央
  七标签工作区+**底部状态栏**（当前项目 id+就绪态；引擎/数据版本
  字段待服务端端点，暂不显示）；
- **滚动行为**：整页（document 级）滚动已根除——内容超高时滚动发生
  在**标签内容区内部**（每标签独立滚动域），顶栏/单元库/状态栏恒在
  视口内；此前「滚轮一滚就跑出窗口、看到窗口外白色背景」的问题已
  根治（C1 批无头断言实证）；
- **数值显示**：参数与数据数值采用等宽字体（Cascadia Code 系）——
  工程数据列对齐易读。

### 3.8 方案浏览表格（webapp，C2 批 2026-09-10）

「方案浏览」标签的方案表按工程数据表惯例重制（六项——无头断言实证）：

- **列宽与固定列**：列宽按列型固定（表头不再竖排/截断）；宽表横向
  滚动时**首列（行身份）与「操作」列固定**，滚动不失锚；
- **表头吸顶**：表格纵向滚动时列头吸附在内容区顶部（单滚动域——
  整页滚动行为不变，见 §3.7）；
- **数值格式化**：整数带千分位（12,480）；非整数统一 3 位小数
  （2129.0928751763995→2,129.093——16 位浮点直出根除）；**鼠标悬浮
  单元格可见全精度原值**（工程师复核通道）；
- **中文列名**：固定列 margin_min/nan_flag/condition_key 显示为
  「最小裕量/可行性/工况条件」（悬浮可见原字段名）；排序下拉同文案；
- **可行性列**：每行「可行」（绿）或「不可行」（红）——标注该组参数
  能否算出完整结果；「最小裕量」列当前在全部单元上为空（内核裕度
  字段供给面挂账建设中），有值后将显示最紧指标的裕度。

### 3.9 工艺画布（webapp，C2-canvas 批 2026-09-10）

「工艺画布」标签按工程软件画布惯例重制（无头断言 11/11 实证）：

- **节点卡片**：每个构筑物显示行业象形图标（格栅/泵站/沉淀池/生物池
  等聚类字形）+中文名+等宽单元代码+**左侧域色条**（蓝=市政污水线、
  棕=污泥线、青绿=矿井水、灰蓝=输配水）；点击节点=选中（**鎏金描边**
  高亮），右侧参数面板随之切换到该构筑物；
- **连线着色**：水流方向连线为蓝色带箭头、污泥去向为棕色（任一端
  属污泥线即按泥色）；回流连线为虚线；
- **图例**（画布左上）：线型三项+当前图出现的域色点，一目了然；
- **小地图**（画布左下）：全图缩略+当前视口框，可拖动/缩放定位；
- **缩放工具条**（画布右下）：放大/缩小/全图适配三钮；
- **画布底面**：深蓝工程底+点阵网格（对齐全站主题）；画布区随窗口
  满高（不再固定 560px）；
- **自动折行布局**：项目未保存布局时，兜底布局按波次自动折行成
  近方形网格（19 节点双链图不再缩成两条细带）。

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

### 5.2 API（28 操作，openapi 锁定断言恒）

| 分组 | 端点 |
|------|------|
| projects（5） | `GET/POST /api/projects`、`GET/PUT /api/projects/{id}`、`POST /api/projects/{id}/validate` |
| calc（7） | `POST /api/calc/run`、`POST /api/calc/enumerate`、`POST /api/calc/design-map`（可行域引导，同步直返——FD 批）、`GET /api/calc/tasks/{id}`、`POST /api/calc/tasks/{id}/cancel`、`GET /api/calc/tasks/{id}/solutions`、`POST /api/calc/solutions/apply` |
| exports（7） | `GET /api/exports`、`GET /api/exports/{file_name}`（下载）、`POST /api/exports/calcbook`、`POST /api/exports/audit`、`POST /api/exports/dxf`、`POST /api/exports/estimate`、`POST /api/exports/ifc` |
| events（2） | `GET /api/events/tasks/{id}`、`GET /api/events/projects/{id}`（SSE） |
| 图纸与数据（7） | `GET /api/scene/{project_id}`（三维场景）、`GET /api/elevation/{project_id}`（高程纵断数据）、`GET /api/cost/{project_id}`（概算）、`GET /api/site/spacing`（布置间距校核）、`GET /api/units`、`GET /api/assumptions`、`GET /api/constraints` |

> 批量导出（M5 起）：`POST /api/exports/{kind}` 载荷 `items` 数组 >1 项
> 即转低优先级批量任务（服务端幂等键防重复提交；进度走 SSE 订阅；
> 在途可点「取消批量」协作取消[已产清单如实计数]；刷新/切页重挂后经
> 本地会话存储自动恢复在途跟踪[SVRB2]）；
> 单产物即时生成上限 1 项。鉴权 token 与 SSE 限流为可配置开关
> （环境变量，默认本地免鉴权）。

### 5.3 导出产物五种 kind 的现行状态

| kind | 状态 | 说明 |
|------|------|------|
| calcbook | API 可用 | Excel 计算书（模板已录入 `data/templates`） |
| audit | CLI 可用；API 501 | HTML 审计报告——`wp export audit` 正门（内联样式自包含）；API 通道未接线（诚实 501） |
| dxf | API 可用 | CAD 图纸：全厂总图（`site_design` 载荷）或单单元图（`unit_id`）或**高程纵断面图**（`sheet: "profile"`——横纵比例可定制 `h_scale`/`v_scale`，如 `"h_scale":"2000"`；批量面 items 逐项 sheet/unit 混装支持）；DXF 落盘后可选子进程转 DWG（`dwg_converter_path` 开关，转换器不随产品分发） |
| estimate | 501 | 概算书（概算核心已实现——`GET /api/cost/{id}` 数据面可用；导出渲染分支未接线，诚实 501） |
| ifc | API 可用 | 全厂 IFC 模型（BIM 交换格式；单产物端点语义，批量项 unit 须一致） |

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
   （当前 3.0——v1→v2 增厂区总平面、v2→v3 增边界红线，历史文件经
   迁移链自动升级）。同版直通；未来版本拒绝（不降级打开，防静默丢
   数据）；无法识别的版本会被拒绝（诚实失败，不猜测语义）。旧**结果**
   不受影响——三元组自证。
9. **三维场景在哪看？** webapp 工作区已接线（画布+三维视图，M4 起
   交付）；数据面 `GET /api/scene/{id}`。布置编辑器支持边界红线与
   间距校核（黄/红标示，`GET /api/site/spacing`）。
10. **怎么自检安装是否成功？** `cd core && uv run pytest` 全量绿；
    或用 golden 案例实跑审计链路：拿 3.2 的 result_file 与项目文件跑
    `wp export audit`，能生成含公式逐条表的 HTML 即通。
