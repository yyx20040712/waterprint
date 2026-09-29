# 单元库浏览验收探针清单（tools/units_browser_probe.py）

> 批6m（UF-52 验收追认收口）沉淀的手动验收工具——门一 d1-B1 处置：
> 验收证据入库持久化（.workflow 会话件散佚教训——增补六十九先例，
> 本批设计件散佚同构复发防再犯）。先例形态=tools/oda_smoke.md（批6j）。
> **不入 CI**（非 hermetic：依赖活链路），随需手动复跑。

## 一、前置条件（缺一=诚实失败 exit 1）

1. **server**（仓根相对）：`uv run --project server uvicorn waterprint_server.main:app --host 127.0.0.1 --port 8000`
2. **vite dev**：`cd webapp && pnpm dev`（127.0.0.1:5173，/api 代理→8000；
   `pnpm install` 先行——node_modules 缺失时）
3. **python playwright**（chromium 已装）：`python -c "import playwright"` 通过

## 二、执行

```bash
python tools/units_browser_probe.py   # 仓根执行；exit 0=PASS / 1=FAIL
```

产物：`.workflow/b6m-probe-out/b6m-probe-report.json`（断言明细+oracle
推导值）+三截图（Drawer 抽样/搜索/聊天 Drawer 宽度）。

## 三、断言族（P0~P10b——探针 docstring 为单源，此处摘要）

- **P0 oracle**：GET /api/units 实读独立推导期望值（组计数/叶总数/抽样
  单元参数端口行数）——判据不写死探针内（防自证循环，d1-W2）。
- **P1/P2**：组行计数与叶行总数 vs oracle 恰等（四线+内置〔5 组〕）。
- **P3**：foot 计数条口径——左=kind=unit 条数、右=组数**含内置组**
  （C2-lib GL-01 用户裁决 2026-09-10「视觉稿形态保留」在册口径）。
- **P4**：叶行英文码不显示（用户裁定 2026-09-10——git 1fd8b8182+
  webapp/src/app/README.md 行内引文在案；悬浮 title=全 unit_id 唯一
  追溯通道）。
- **P5/P6**：抽样单元 Drawer 参数面五列表〔含 label_zh 物理意义〕/
  端口面四列表，行列数 vs oracle 恰等（抽样制非逐条——渲染走同一
  数据驱动通路，k1-N2 口径）。
- **P7/P7b**：搜索过滤 unit_id 子串+**中文名子串**双面恰命中 oracle
  推导集（k1-W2——显示面与搜索面一致性钉死）。
- **P8**：内置空参单元 Drawer「内置节点无参数面」文案（R 轮 G1-02）。
- **P9**：console 零 error（探针域全页面告警归零——ChatPane Drawer
  弃用 width prop 已随批6m 迁移 styles.wrapper 收口）。
- **P10/P10b**：Drawer 宽度等价性证明（d1-W4）——styles.wrapper 迁移
  后 `.ant-drawer-content-wrapper` 实测宽：单元库 480+聊天 420（width
  prop→styles.wrapper 同节点恒等实证）。

## 四、重录时机

- 目录条目增删（新单元包/内置 kind 变更）→ oracle 自动跟随（探针零
  改动——期望值全部 API 推导）；
- 分组/树/Drawer 渲染逻辑变更 → 重跑本探针核对；
- 断言族语义变更 → 探针 docstring（单源）与本清单同步。
