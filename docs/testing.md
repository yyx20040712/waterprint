# 测试系统

> 单一事实源：`core/tests/README.md`（本页为导航摘要，详规以该文件为准）。

- 分层：架构门禁测试（active）→ 休眠镜像测试（实现合入自动激活）→
  性质测试（hypothesis）→ golden 端到端 → 性能基准；
- 收集口径：core 的 `python_files` 含 `properties_*.py` 与 `properties.py`
  （tests/ 与 units_lib 包内性质测试均入全量收集——默认 test_*.py 模式
  曾漏收，0ac8c73 起补齐）；
- 只读锁定：`core/tests/` 与 `server/tests/` 全部文件由
  `test-lock.manifest.json`（sha256）+ 文件只读属性双重锁定，
  `scripts/check_readonly.py` 与 `tests/arch/test_lock.py` 本地/CI 双验；
- 红绿纪律：每个测试先失败一次再通过；skip 数随里程碑归零（CI `-ra`）。
