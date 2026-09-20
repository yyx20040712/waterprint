# WaterPrint Agent —— 一句话设计演示（B4-4a）

> 演示版：一句话自然语言 → 全厂水力水质计算 → 设计说明书（.md）+ 计算书（.xlsx）。
> 原理：LLM 只做单步意图解析（可选，失败/断网自动回退规则表），计算全部走
> WaterPrint 计算内核正门（只编排不算数）。

## 一键运行

```bash
# 在仓库根目录（首次先 uv sync 见「环境要求」）
uv run --directory agent python -m waterprint_agent.demo "设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺"
```

断网/无 key 场景加 `--offline`（规则表直跑）：

```bash
uv run --directory agent python -m waterprint_agent.demo "矿井水处理厂，日处理量 1 万吨" --offline
```

`--json` 输出完整机器可读结果；缺省输出人类可读摘要。

## 演示三话术（验收基准）

| # | 话术 | 预期 |
|---|---|---|
| ① | 设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺 | 达标✓；吨水电耗≈0.208 kWh/m³；吨水碳强度≈0.588 kgCO2e/m³；说明书+计算书双落盘 |
| ② | 矿井水处理厂，日处理量 1 万吨 | 计算绿+达标判定诚实呈现（矿井水高 TN/TP，市政标准口径下未达标——明细可解释）；吨水碳强度≈0.70；双报告暂不生成（core 报告面对矿井线两处既有缺口，已记档挂账） |
| ③ | 市政污水厂 5 万吨每天，出水要一级 A | 达标✓（一级 A 判定面全过）；双落盘 |

预期输出样例（话术①）：

```
════ WaterPrint 一句话设计演示 ════
话术：设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺
解析：种子=municipal_34760 规模=30000 m³/d（规则解析：…）
项目：9508c4d3…（design 2bc352604a）
达标判定：✓ 达标（出水指标 12 项）
出水指标（mg/L）：COD 19.19 / BOD5 5.53 / SS 0.24 / NH3-N 2.60 / TN 10.75 / TP 0.45
能耗：总 6239 kWh/d（吨水电耗 0.208 kWh/m³）
碳排：总 17627 kgCO2e/d（吨水碳强度 0.588 kgCO2e/m³）
成本：年运行 2,638,585 元/a
落盘·说明书：<沙箱>/reports/…-report-….md
落盘·计算书：<沙箱>/exports/…-calcbook-….xlsx
```

产物落沙箱区（缺省 `仓库上一级/ai-sandbox/`，环境变量 `WATERPRINT_AI_SANDBOX` 可覆盖）。

## 环境要求

- [uv](https://docs.astral.sh/uv/)（Python ≥3.12 包管理）
- 首次：`uv sync --directory agent`（core/server 本地路径源一并安装）
- 离线演示无需任何外部服务（`--offline`）

## 意图解析配置（可选）

环境变量三元组（任意 OpenAI 兼容对话端点均可；名称/地址/密钥以你所用
服务商的文档为准）：

```bash
export WATERPRINT_DEMO_LLM_BASE_URL="<服务商文档给出的 API 基址>"
export WATERPRINT_DEMO_LLM_API_KEY="<你的密钥>"
export WATERPRINT_DEMO_LLM_MODEL="<模型名>"
```

- 三项齐备才发起调用（10 秒超时）；任一缺失、调用失败或返回不合规
  →自动回退规则表解析，输出中诚实标注解析来源（`规则解析…已回退`）。
- 密钥只走环境变量，禁止写入任何文件。

## 规模改参口径（量纲异构）

| 种子 | 进水节点 | q_avg_daily 单位 |
|---|---|---|
| municipal_34760 / loop / recycle | inlet | m³/s（= m³/d ÷ 86400） |
| mine_43836 | mine_water_input | m³/d（直填） |

## MCP 接入（ZCode 等客户端）

软件页面顶栏「AI 接入」入口：状态四项检查+一键接入（把 waterprint MCP
server 条目写入工作区 `.zcode/config.json`，merge 保留既有条目）——重启
ZCode 会话后 21 个 `wp_*` 工具可用。命令行等价：启动 server 后
`POST /api/ai/connection/setup`。

## 测试

```bash
uv run --directory agent pytest tests/test_demo_rules.py tests/test_demo_llm.py tests/test_demo_pipeline.py
```
