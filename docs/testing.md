# 测试系统

> 单一事实源：`core/tests/README.md`（本页为导航摘要，详规以该文件为准）。

- 分层：架构门禁测试（active）→ 休眠镜像测试（实现合入自动激活）→
  性质测试（hypothesis）→ golden 端到端 → 性能基准；
- 收集口径：core 的 `python_files = ["test_*.py", "properties_*.py"]`
  （tests/ 与 units_lib 包内**真性质测试** `properties_*.py` 入全量收集——
  默认 test_*.py 模式曾漏收，0ac8c73 起补齐）；包内裸 `properties.py`
  33 份为**结构预留件**（含各单元物理性质清单规格——C1-续批转实内容），
  **不入收集**（R2D 2026-09-02 收口，见 `core/pyproject.toml` 注记；
  GOV1 2026-09-12 勘正：本页原称"含 properties.py"失实）；
- 只读锁定：`core/tests/`、`server/tests/` 与 **units_lib 包内 tests/**
  全部文件由 `test-lock.manifest.json`（sha256）+ 文件只读属性双重锁定
  （实测口径 270 键 = core/tests 139 + server/tests 39 + units_lib 包内
  94——GOV1 勘正：本页原漏 units_lib 面），
  `scripts/check_readonly.py` 与 `tests/arch/test_lock.py` 本地/CI 双验；
- 红绿纪律：每个测试先失败一次再通过；skip 数随里程碑归零（CI `-ra`；
  **skip>0 即 CI FAIL——GOV1 A3 机器化**，ci.yml core/server 两 pytest
  步骤拦截）；
- 快照回归：`tests/snapshots/`（syrupy）锚三导出产物内容哈希
  （xlsx/DXF/HTML——ADR-010）；快照红≠自动更新，先人审定性（预期漂移
  `--snapshot-update` 重录+diff 入批注记；非预期=回归缺陷走修复）；
  `__snapshots__/` 不入锁定清单，更新走显式命令+人审。
