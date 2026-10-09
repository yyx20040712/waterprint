# report_golden —— 说明书管线 golden 产物生成器（B6 起 report 管线居 core）

> 批6k（2026-09-29，增补六十二②「report 一次性产物生成脚本化入库」）：
> 历史上 result.json/diag.json 是系统临时目录一次性脚本产物（会话环境
> 易失——增补六十一 R2 呈报项），测试缺失即 skip。本批起产物入库+
> 生成脚本化+CI 漂移检测三件闭项。

## 一、产物与消费链

| 件 | 位置 | 生成 | 消费 |
|----|------|------|------|
| result.json | `core/tests/report/__snapshots__/` | 本脚本（PlantResult serialize） | `core/tests/report/conftest.py`（默认路径；env 覆盖通道保留） |
| diag.json | 同上 | 本脚本（serialize_diag） | 同上 |
| municipal_34760.sample.md | 同上 | 渲染重录（漂移随 result.json 联动；B6 起含数学块+公式溯源附录） | `test_snapshot.py`（render 与入库样例逐字节比对） |
| formula_printers.latex.txt | 同上 | B6：registry 全量公式双打印机快照（LaTeX 态——451 条） | `test_formula_printers.py`（逐公式快照对账——漂移即红） |
| formula_printers.typst.txt | 同上 | B6：同上（Typst 态） | 同上 |

三件全 CI 钉死：agent job 的 `--check` 步钉 result/diag 两件，
`test_snapshot` 经产物钉 sample md——coefficients/模板/引擎面任何变更
导致的漂移都会红。

## 二、命令（仓根执行）

```
uv run --project core python tools/report_golden.py --check   # 漂移检测（CI 同款）
uv run --project core python tools/report_golden.py --write   # 重录
```

## 三、重录时机（漂移红时的处置清单）

1. `data/coefficients`（或 unit_prices）升版/改值——数值面漂移；
2. core `serialize`/`serialize_diag` 契约变更——序列化面漂移；
3. core 引擎计算面变更致 golden 数值变化（此类通常 core golden 先红，
   随 core 重录批次同批处理本面）；
4. sample md 渲染模板（`render_md.py`）变更——重跑 --write 后跑
   core `tests/report` 套件，`test_snapshot` 红则同步重录 sample md；
5. B6：registry 公式集/表达式变更（单元扩面/改式）或公式双打印机
   （`formula_printers.py`）实现变更——公式快照两件漂移，--write 同批
   重录。

重录后本地核验：`uv run --project core python tools/report_golden.py
--check` 绿 + core `tests/report` 套件 pytest 全绿（B6 起 report 居 core
——路径与 venv 均已迁；agent 侧零 report 资产）。

## 四、纪律注记

- 产物在 `__snapshots__` 目录=check_readonly/lock_tests 双忽略面（锁面
  外快照资产，与 core `__snapshots__` 同口径）——不入 test-lock
  manifest，不触发 [HUMAN-LOCK] 工序；
- 双跑字节恒等断言内建（确定性破坏=脚本自身 FAIL，分诊 GR-04/16/18
  迭代序纪律）；
- conftest 的 skip 通道退役为仓库损坏 belt（产物入库后缺失=仓库缺陷，
  CI agent job 的 skip==0 拦截兜底红显）。
