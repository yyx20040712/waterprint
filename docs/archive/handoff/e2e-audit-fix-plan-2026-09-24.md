# 前端用户模拟测试排查与修复交接文档（e2e-audit-20260924）

> 生成：2026-09-24 调研会话（主控手动直跑——用户直排工单「对当前项目进行用户模拟测试，
> 排查 bug，并制定详细修复计划」；本会话=只调研+规划+本文档，**零仓内源码改动**）。
> 消费者：修复会话（新会话按 §7 开工指引执行 §4 修复计划）。
> 板面声明：`docs/handoff/relay.md` 接力板**未改动**（next_batch 仍=B4-5）；本工单为
> 用户对话内直排，位阶高于板面自动排程——修复会话以本文档为准，收口时按 §7.4 回写板面。

---

## 0. 执行摘要

用户报告「前端测试时几乎没有一步是没有问题的」。本次调研用**无头浏览器完整走查
真实用户旅程**（48 步两轮 + 聚焦复测 20 步 + 4 个定点探针），叠加白盒代码勘察，
结论：**用户体感成立，且根因高度集中——4 个 P0 缺陷的级联足以让主旅程每一步都死**：

| # | 缺陷 | 层 | 一句话 |
|---|---|---|---|
| P0-A | `data_dir` 缺省按 CWD 相对解析 | server | 按 README 口径启动（`cd server && uv run …`）→ 约束库 500、计算必败、AI 接入 400——**服务端全线断** |
| P0-B | 只读态「提交计算」静默 no-op | webapp | 默认（非编辑）态点主按钮**零请求零反馈**——结果面九标签全部拿不到 done calc，全陷空态 |
| P0-C | 聊天桥 worker 把 `data_dir` 当仓库根 | server | `uv run --directory <data>/agent` 必然找不到目录——**聊天功能在任何部署形态下从未跑通过** |
| P0-D | 聊天失败轮后输入框永久锁死 | webapp | `busy=turnStage!==null`，失败轮不清空——一次 failed 即聊天面板报废 |

三件服务端/环境修好后（阶段2实证）：导入建项、编辑态提交计算、方案枚举、图纸导出、
九结果标签出数**全部正常**——前端主体是好的，坏在四个定点缺陷与其级联。

**证据目录**（本会话仓外工作区，修复会话直接复用）：
`.workflow/e2e-audit-2026-09-24/`
- `sim_test.py` / `run2.log` / `report.json` / `console.json` / `network.json` / `screenshots/`（48 步全程）
- `stage2_test.py` / `stage2-report.json` / `screenshots2/`（健康环境复测）
- `probe_*.png`（定点探针：枚举 e2e / 聊天开抽屉 / 聊天发消息）
- 技能盘点件：`.workflow/skills-inventory-e2e-audit-2026-09-24.md`

---

## 1. 测试环境与方法（精确复现口径）

### 1.1 起服务（两种口径——正是 P0-A 的对照组）

```bash
# 口径①（README 快速开始，复现"全线断"）：
cd E:/class/智水蓝图/waterprint/server
PYTHONUTF8=1 uv run python -m waterprint_server.main        # data_dir→server/data ✗

# 口径②（健康基线，阶段2 用）：
cd E:/class/智水蓝图/waterprint/server
PYTHONUTF8=1 WATERPRINT_DATA_DIR="E:/class/智水蓝图/waterprint/data" \
  uv run python -m waterprint_server.main                   # ✓

# 前端（pnpm 不在当前 shell PATH 时直跑 hoisted vite）：
cd E:/class/智水蓝图/waterprint/webapp
node ../node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
```

注意：vite 缺省只绑 `[::1]`（IPv6）——`--host 127.0.0.1` 必加，否则 127.0.0.1 拒连
（本会话实测；也是用户侧潜在「打不开页面」因素）。

### 1.2 无头浏览器资产（全局规范：禁可见浏览器抢前台）

- 引擎：系统 Python 3.14 + playwright（`D:/python3/python314/python.exe`；chromium 已缓存于 `~/AppData/Local/ms-playwright`）。
- 脚本即上表证据目录三件；逐步截图+console/pageerror/网络≥400 采集+按步骤归因，一步失败不中断。
- golden 建项素材：`core/tests/golden/golden_data/municipal_34760/input_project.json`（UI「导入 JSON」通道，19 节点）。

### 1.3 方法论：两阶段隔离

1. **阶段1（口径①坏环境）**：完整复现用户视角——48 步旅程，17 步失败，312 console 错误。
2. **阶段2（口径②健康环境）**：同一批 UI 操作复测——区分「环境断的级联」与「前端真缺陷」。
3. **白盒勘察**（并行 Explore 子代理）：antd v6 迁移面、聊天契约、计算链接线、崩溃候选——
   与黑盒发现互相印证（P0-B 双源确认；P0-D 白盒预言黑盒坐实）。

---

## 2. 用户旅程断点图（为什么"每一步都有问题"）

以「导入 golden 项目 → 计算看结果」主旅程为例，口径① 下用户实际经历：

```
打开页面          ✓ 正常（1 条 antd 弃用警告）
导入建项          ✓ 正常（19 节点上画布）
选中节点/参数面板  ✓ 正常
[可行域]          △ 进水节点无连续参数无入口（正常语义，但无引导说明是"为何没有"）
[经验取值]页签    ✓ Segmented 控件正常（注意：不是 role=tab）
进入编辑/校验/保存 ✓ 正常
退出编辑
点「提交计算」     ✗ P0-B：静默无操作（无请求/无提示/按钮不置灰）
（即使进入编辑态提交）✗ P0-A：任务 failed=DataPackError 系数包缺 manifest
方案浏览          ✗ 枚举提交→服务端 LoaderError（P0-A 级联）；无 done calc 表格恒空
三维视图/高程/概算/对比/可信度/诊断 ✗ 全部 404 空态（P0-A/B 级联——空态文案本身合格）
图纸预览          ✗ 导出按钮 disabled（无 done calc 级联闸门，行为正确但用户死路）
AI 接入           ✗ 400 工作区锚点校验失败（P0-A 级联）
设计对话          ✗ 发消息→99%→「轮结束（failed）」→输入永久锁死（P0-C+P0-D 叠加）
项目管理          △ 重命名/复制/删除本身正常（本会话因抽屉遮挡未走完，属测试脚本问题）
```

**核心洞察**：九个结果面标签的空态文案与闸门逻辑都是诚实且合格的——它们"坏"只是因为
上游 P0-A/P0-B 让 done calc 永远不存在。修好两个上游 P0，下游自动复活（阶段2 已实证）。

---

## 3. Bug 清单（分级·证据·根因·修法）

### P0-A【server】data_dir 缺省 CWD 相对——README 开发口径启动全线断

- **现象**（口径①实测）：
  - `GET /api/constraints` → 500 `RuntimeError: 约束知识库未就绪：data\constraint_kb\constraints.json 不存在`
  - `POST /api/calc/run` → 任务 failed `DataPackError: 系数包缺 manifest.yaml：data\coefficients`
  - `GET /api/ai/connection` → 400 工作区锚点校验失败（repo_root 推导错位）
- **根因**：`server/waterprint_server/settings.py:107` `data_dir: Path = Path("data")`——
  CWD 相对。README「一键命令」教用户 `cd server && uv run …` ⇒ 解析为 `server/data`（不存在）。
  历史会话从仓库根启动（根下 `projects/`、`exports/` 有产物为证）才碰巧正常；打包版
  （B4-4a-pkg）在 `启动.bat` 显式设了 env 才正常——**唯独 README 文档口径是坏的**。
- **波及**：`services/calculation.py:112`、`services/enumeration.py:121`（data_dir 入载荷）、
  `services/constraints.py:104`、`services/ai_connection.py:136`（`.parent` 推导 repo 根）。
- **修复建议**（批1）：
  1. 缺省改**包定位解析**：`Path(__file__).resolve().parents[2] / "data"`
     （server/waterprint_server/settings.py 上溯两级=仓库根；对仓库开发/打包 app 伪根/Docker /app 三种布局全部成立——已逐一核对目录形态；env `WATERPRINT_DATA_DIR` 仍可覆盖）。
  2. **启动 fail-fast**：main.py 启动时校验四个数据包目录（coefficients/constraint_kb/
     templates/unit_prices 的 manifest.yaml 在场），缺任何一个以可执行文案拒绝启动
     （对齐 ADR-012 D6 的 fail-fast 理念：现在的问题不是拒绝，是**晚拒+拒在用户脸上**）。
  3. README「一键命令」与 docs/user-manual.md §2 同步修正（或保持 cd server 口径但依赖①的自愈）。
- **验证**：口径①裸启 → 启动即绿或明确报错；`/api/constraints` 200；golden 项目 UI 提交计算 done。
- **测试落点**：server 侧镜像测试（**注意锁面**：server/tests 只读，走 §7.3 [HUMAN-LOCK] 工序）。

### P0-B【webapp】只读态「提交计算」静默 no-op

- **现象**（黑盒双证）：阶段2 `t01` 点击后 `/api/calc/run` 请求增量=0；server 日志无 POST。
  按钮可点、不置灰、无任何 toast——用户以为点了没反应或软件坏了。
- **根因**：`webapp/src/app/canvasEditToolbar.tsx:98-100`
  ```ts
  const body = draft !== null && rawQuery.data !== undefined ? draftProjectRaw(...) : null;
  const runCalc = async () => {
    if (body === null) { return; }   // ← 只读态 draft===null ⇒ 恒 return
  ```
  只读态（项目加载后的默认态）`draft===null` ⇒ `body===null` ⇒ 静默返回。而同函数
  `:117-122` 的 mutate 载荷明确写了只读 raw 分支——实现与「呈裁⑥ 常驻提交计算（不依赖
  选中/dirty）」的设计意图脱节。
- **引入史**：P0-3 批 `fec0c72baf` 落地；该批无头 E2E（shoot_c2_edit.py T5）在**编辑态**内
  验证通过——只读路径从未被任何测试覆盖，潜伏至今。
- **修复建议**（批2）：`body===null` 守卫只应作用于 dirty-save 分支：
  ```ts
  const runCalc = async () => {
    try {
      if (dirty) {
        if (body === null) { messageApi.error("项目数据未就绪——稍候重试"); return; }
        await save.mutateAsync({ projectId, data: body }); …
      }
      run.mutate({ data: { project_id: projectId, …raw 条件分支照旧… } }, …);
    } catch …
  ```
  另建议：`rawQuery.isLoading` 时按钮 loading（防「未就绪点击」窗口）。
- **回归锚**：webapp vitest 新用例「只读态 runCalc 发出 mutate（不 save）」+
  无头 E2E 新步「导入项目→不进编辑→提交计算→?task= 回写」。
- **验证**：阶段2 脚本 `t01` 复跑 `readonly_calc_requests ≥ 1`。

### P0-C【server】ai_chat worker agent 目录推导错位——聊天轮必失败

- **现象**：聊天发消息 → POST 200 → 轮进度 99% → 「轮结束（failed）」。
  任务记录：`RuntimeError: 对话子进程退出码 2（agent CLI 桥失败——stderr 摘要 error:
  系统找不到指定的文件。 (os error 2)）`。
- **根因**：`server/waterprint_server/jobs/ai_chat.py:84-93`
  ```python
  repo_root = Path(str(payload.get("data_dir", ".")))
  … str(repo_root / "agent") …
  ```
  把 `data_dir`（语义=`<仓库根>/data`）直接当仓库根用 ⇒ `uv run --directory <仓库根>/data/agent`
  （不存在）⇒ uv 报 os error 2。**对照三处正确推导**：`services/ai_chat.py:56`
  （readonly 面）、`services/ai_connection.py:136`、均为 `data_dir.resolve().parent`。
  同一 payload 键在 services/jobs 两面语义不一致——**任何部署形态（dev/Docker/打包）
  下聊天轮都必然失败**；B4-4b 收口时桥面无仓内自动化（在册挂账「多行为人工实证」），
  该缺陷逃过双门。
- **修复建议**（批3）：消除双源——payload 显式传 `repo_root`（由 services 侧
  `data_dir.resolve().parent` 单点推导），worker 只消费不再自算；或最小改：
  worker 行改 `.resolve().parent`。**推荐前者**（防第三处再犯）。
- **回归锚**：server 侧「桥命令构造」单测（payload repo_root 透传断言）+ 无头 E2E
  聊天发消息终态 done（阶段2 探针脚本可直接改造为回归）。
- **注**：修好后仍需 LLM 三键或降级路径可用——本机无键时 agent 走规则回退（B4-4b 设计），
  回归验证用降级路径即可（话术用 fallback 能答的简单问句）。

### P0-D【webapp】聊天失败轮后输入框永久锁死 + 失败零反馈

- **现象**（黑盒复证）：failed 轮后抽屉文本恒显「99%｜轮结束（failed）」，输入可打字但
  发送被 `busy` 吞（`onSearch` 首行 `if (!message || busy || send.isPending) return`）；
  关抽屉/切会话不复位（ChatPane 常驻 App.tsx:409 不卸载）。
- **根因**：`webapp/src/features/ai_chat/components/ChatPanel.tsx:98` `busy = turnStage !== null`；
  `ChatPane.tsx`（useTaskEventSource 三态协议）终态把 turnStage 置为「轮结束（failed）」
  文案而非 null——done 轮可能同病（「轮结束（done）」也非 null？——修复时核实两态）。
  叠加：POST onError 无处理（502/422 时草稿被清空且无提示，`ChatPane.tsx:32-42`）。
- **修复建议**（批3，与 P0-C 同批）：终态（done/failed/cancelled）一律清 turnStage=null；
  failed/cancelled 在消息流区渲染错误横幅（含任务 error 摘要）；mutation onError 保留草稿+
  toast。顺手修：会话清单空时 Select 显示「（暂无会话——直接发言即建档）」引导、
  Progress 假 99% 改消费 SSE percent、首读 502 文案区分「中继不可达/会话尚未落盘」。
- **回归锚**：vitest「failed 终态后可再次发送」「onError 草稿保留」两用例。

### P1 群（修完 P0 后的第二优先级）

| ID | 问题 | 位置 | 说明/修法 |
|---|---|---|---|
| P1-1 | 无根级 ErrorBoundary | `main.tsx:19-23` | Header/Sider(UnitLibrary)/StatusBar/ChatPane 在全部面板边界之外——这些区域一次渲染异常=整树白屏。加根级 Boundary（兜底降级 UI，非吞错） |
| P1-2 | 聊天首轮竞态 | `ChatPanel.tsx:115` 区 | POST 200（任务异步）后立即 GET messages，会话文件未落盘时 502→固定文案「会话读取失败（中继不可达）」误导。改：history 查询带退避重试+终态失效 |
| P1-3 | AI 接入状态在锚点失配时不可自诊 | `services/ai_connection.py:141` | 400 文案已含指引（好），但 Modal 内呈现待核（s60 截图）；P0-A 修后自然缓解 |
| P1-4 | SSE 永不成流无终态兜底 | `shared/api/useTaskEventSource.ts:181-189` | 退避达限转 60s probing 后永远不 invalidate——加轮询 TaskStatus 兜底或超时判定 |

### P2 群（卫生批）

| ID | 问题 | 位置 |
|---|---|---|
| P2-1 | antd v6 弃用：Drawer `width`（console 警告实测2处） | `features/ai_chat/components/ChatPane.tsx:65` |
| P2-2 | antd v6 弃用：Alert `message`→`title`（4 处） | `features/aiconnect/components/AiConnectModal.tsx:91,97,105,117` |
| P2-3 | `Modal.confirm` 静态方法（脱离 ConfigProvider 主题） | `features/drawings/components/ExportButton.tsx:123` |
| P2-4 | 概算面板 React duplicate key 告警（阶段2 实测 10+ 条） | `features/cost/components/IndicatorsCard.tsx:51`（`key: reading.indicator_key` 重复——叠加 condition/序号消歧） |
| P2-5 | THREE.Clock 弃用警告、React Flow attribution 警告 | viewer3d / canvas（升级面，低危） |
| P2-6 | 聊天会话 Select 空清单显示裸 hex value、`Progress percent={99}` 假进度、消息 `key={index}` | `ChatPanel.tsx:107-122` |

### 测试资产缺口（用户体感的深层原因——测试绿≠产品通）

1. **只读态主链零覆盖**：全部既有无头 E2E 在编辑态内验证（P0-B 逃逸通道）。
2. **README 口径冒烟缺失**：没有任何测试按文档口径（cd server 裸启）跑过服务端。
3. **聊天真桥零自动化**（B4-4b 在册挂账）——P0-C 逃逸通道；本调研已提供可改造的探针脚本。
4. **antd v6 DOM 断代**：`.ant-select-selector`→`.ant-select-content` 等类名变更——
   任何依赖 v5 类名的测试/样式选择器都会静默失配（本次测试脚本即中招）；建议修复批
   顺手盘点 `global.css` 与组件内 v5 类名引用。

### 环境事项（用户侧复现成本，随批1文档化）

- `pnpm` 需 corepack 启用且不在所有 shell PATH——README 已述但易踩（本会话直跑
  hoisted vite 绕过）。
- vite 缺省绑 `[::1]`：`--host 127.0.0.1` 或 vite.config 固化（建议后者，随批2）。
- server 从不同 CWD 启动会在该 CWD 落 `projects/`/`exports/`（根下与 server/ 下现有
  双份产物为证）——P0-A 修复只动 data_dir；projects/exports 的 CWD 语义是否也要
  收敛属产品决策，修复会话**呈报不擅动**。

### 未决异常（低优先，修复会话顺手追）

- 阶段2 `t10` 截图出现过一次「枚举提交失败：LoaderError: 系数包缺 manifest.yaml」
  toast——当页零枚举 POST、服务端零对应记录、干净复现两轮均不重现。怀疑与 vite
  proxy 对旧连接的瞬时失败或 React Query 缓存边缘态有关。留观；若修复批复现即追。

---

## 4. 修复计划（批次·DoD·依赖）

> 批型全部为**实现批**：按 AGENTS.md 管道走双门（门一异构隔离审+门二实证）；
> 涉 server/tests 或 core/tests 改动=锁面笔（§7.3）。webapp vitest 不在锁面。
> 建议顺序：批1→批2→批3（批2/批3 可并行——不同文件域）；批4 卫生批收尾。

### 批1【server-data】数据包路径自愈 + 启动 fail-fast（P0-A）

- **改动面**：`settings.py`（缺省解析）、`main.py`（启动校验）、`README.md`+`docs/user-manual.md`（口径）、
  `server/tests/` 镜像测试（锁面）。
- **DoD**：
  - [ ] 三种布局（仓库开发/打包伪根/Docker env）缺省或 env 均解析到正确 data 包根（单测断言解析函数）
  - [ ] 缺数据包启动=显式拒绝+可执行文案（非 500 晚拒）
  - [ ] 口径①裸启：`/api/constraints` 200、golden 项目 `/api/calc/run` done
  - [ ] run_gates 全绿；[HUMAN-LOCK] 锁面笔合规
- **风险**：打包版 `启动.bat` 显式 env 不受影响；Docker env 不受影响——回归面小。

### 批2【webapp-calc】只读态提交计算复活（P0-B + 顺手 P1-4/P2 环境）

- **改动面**：`canvasEditToolbar.tsx`（runCalc 重构）、vitest 新用例、无头 E2E 补只读步、
  `vite.config.ts`（--host 固化，可选）。
- **DoD**：
  - [ ] 只读态点击→POST 发出（ vitest mock 断言 mutate 调用）
  - [ ] 编辑态 dirty 先存后算行为不回归（既有 T5 场景）
  - [ ] rawQuery 加载期按钮 loading
  - [ ] 阶段2 脚本 t01 复跑 `readonly_calc_requests ≥ 1`、t03-t05 复绿
  - [ ] check_webapp 契约头门禁绿（新文件须登记 file-contracts.md）

### 批3【chat】双端修通（P0-C + P0-D + P1-2/P2-6 顺手）

- **改动面**：`services/ai_chat.py`（payload 显式 repo_root）、`jobs/ai_chat.py`（消费不自算）、
  `ChatPane.tsx`/`ChatPanel.tsx`（终态清 busy、错误横幅、onError 保草稿、空会话引导）、
  server 侧桥命令单测（锁面）、webapp vitest 用例。
- **DoD**：
  - [ ] 无头 E2E：发消息→终态 done→回复气泡可见（无 LLM 键环境走降级路径验证）
  - [ ] failed 轮后可再次发送（黑盒复证脚本改回归）
  - [ ] onError 草稿保留+toast；空会话下拉有引导文案
  - [ ] payload 契约单测：repo_root 单点推导、worker 零自算
- **依赖**：无硬依赖（可与批2 并行）；验证需要批1 的健康服务端（或 env 口径②）。

### 批4【hygiene】卫生批（P1-1 + P2 群）

- 根级 ErrorBoundary、antd v6 弃用清理（Drawer/Alert/Modal.confirm）、cost duplicate key、
  antd v5 类名引用盘点（global.css+组件）。
- **DoD**：console 警告清零目标（antd/three/ReactFlow 三族——three/attribution 可呈报豁免）、
  既有全量 vitest+tsc 零红。

### 总验收（修复会话收口必跑）

1. 口径①裸启服务端+前端（§1.1 命令原样）。
2. 复跑 `.workflow/e2e-audit-2026-09-24/sim_test.py`（修选择器：`.ant-select-selector`
   →role=combobox / `.ant-select-content`；Segmented 页签用 `.ant-segmented-item` 文案定位；
   s30 断言翻转为「请求发出」）——**48 步目标全绿**（已证可行的部分：s01-s26/s40/
   s50-s57/s60-s61 及健康环境下 t03-t20 全绿）。
3. `run_gates` 全绿 + core/server/agent/webapp 四套件基线对齐（批前批后失败签名零新增）。
4. 用户亲测剧本：§5。

---

## 5. 用户验收剧本（修复后 10 分钟人工走查）

1. 按 README 一键命令起服务+前端（不设任何 env）。
2. 新建项目（导入 golden JSON）→ 不进编辑 → 点「提交计算」→ 状态栏/方案浏览出现任务进度 → done。
3. 依次点开九个结果标签——三维有模型、高程有图、概算有表、可信度有指标、对比有矩阵。
4. 图纸预览 → 导出全厂总图（DXF）→ 产物列表出现。
5. 设计对话 → 发「你好」→ 得到回复（或降级说明）；再发第二条（验锁死已修）。
6. 项目管理 → 重命名/复制/删除一遍。
7. F12 console：无 error（antd 弃用警告应为零或已立项豁免）。

---

## 6. 调研过程数据（供审计回溯）

- run2（口径①）48 步：17 fail；console 312（其中 297=测试脚本对 null 任务轮询噪声，
  真实信号=2×Drawer 警告+1×Alert 警告+资源 404/500 若干）；API 错误 324（同噪声占比高）。
- 阶段2（口径②）20 步：3 fail（全部=测试选择器 antd v6 类名失配，已定位非产品缺陷）；
  关键取证 `readonly_calc_requests=0`。
- 白盒勘察（Explore）输出全文：见本会话账本（要点已并入 §3）。
- 测试脚本已知误报清单（修复会话勿重复追查）：s21/s22（进水节点无连续参数——正常）、
  s23（Segmented 非 tab）、s41/t10（`.ant-select-selector` v6 失配）、s70-s82（聊天抽屉
  未关遮挡+级联）、s53（导出按钮禁用=级联正确闸门）、s62（消息输入框 `[type=text]`
  选择器失配——antd Input 不写 type 属性，应用 `[data-testid=wp-chat-input]`）。

---

## 7. 新会话开工指引（宪法合规路径）

### 7.1 开工前置（顺序不可倒置）

1. Skill 加载 `ai-dev-org`（实际调用非纸面引用）。
2. `org-config resolve`（模型路由；门一主源额度事实以板面/用户最新告知为准）。
3. 读本文档 + `AGENTS.md`（宪法）+ `docs/file-contracts.md`（要动的文件职责）。
4. 技能盘点件落 `.workflow/skills-inventory-<任务ID>.md`（本会话先例：
   `skills-inventory-e2e-audit-2026-09-24.md`）。
5. 建议把本工单登记为独立修复战役（如 `e2e-fix`），在 relay 板批次日志追加一行用户直排
   记录（不改 next_batch 语义，收口时同步）。

### 7.2 批型与烤验

- 批1/批2/批3=实现批（双门并集：门一异构隔离审+门二实证）；批4 可按「小批」分级烤验
  裁量（纯文档/注释且 ≤3 文件才是小批——批4 涉代码，仍全走）。
- 门一审包自包含（ORG-12：≤8k tokens，golden/契约不内联）。
- 实现纪律：TDD 先红后绿；`git diff --stat` 自查范围蔓延；每文件 ≤500 行+契约头+
  file-contracts 登记；禁占位词/裸 except/魔法数字（详见宪法 §2/§3）。

### 7.3 锁面红线（触碰测试=人类批准事件）

- `server/tests/**`、`core/tests/**` 只读——新增/修改测试须：解锁→改→`python
  scripts/lock_tests.py`→[HUMAN-LOCK] 标签 commit（逐文件动机）。AI 只能起草呈批。
- webapp vitest（`webapp/src/**/*.test.*`）**不在锁面**，可正常 TDD。
- 修复批预计锁面笔：批1（server 镜像测试）、批3（server 桥命令单测）——各一笔。

### 7.4 收口

- run_gates 全绿 + `gen_status.py --check` 零漂移 + health-scan RED=0。
- relay.md：批次日志追加+板头计数/last_handover 刷新（修板不是新批不加 batch_count）；
  next_batch 回 B4-5 原排序（本战役为插队修复，不动第四波清单语义）。
- 向用户呈报：修复清单对账表（本文档 §3 逐条 勾）+ §5 验收剧本结果。

### 7.5 关键提醒（本战役特有）

- 不要「顺手」重构聊天协议或 SSE 架构——P0-C/D 用最小改修通，架构面留给后续批。
- 阶段2 的 LoaderError 一次性 toast（§3 未决异常）若不复现即记档关闭，勿无限追。
- 三处 repo_root 推导（services/ai_chat、ai_connection、jobs/ai_chat）在批3 收敛后，
  在 file-contracts 或 README 注明单一推导点，防第四处再犯。

---

（完——生成者：2026-09-24 调研会话主控；证据与脚本全套在
`.workflow/e2e-audit-2026-09-24/`，新会话按 §4 批次开工即可。）
