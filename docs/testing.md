# 测试系统

> 单一事实源：`core/tests/README.md`（本页为导航摘要，详规以该文件为准）。

- 分层：架构门禁测试（active）→ 休眠镜像测试（实现合入自动激活）→
  性质测试（hypothesis）→ golden 端到端 → 性能基准；
- 收集口径：core 的 `python_files = ["test_*.py", "properties_*.py",
  "properties.py"]`（tests/ 与 units_lib 包内**真性质测试**入全量收集——
  默认 test_*.py 模式曾漏收，0ac8c73 起补齐）；包内裸 `properties.py`
  33 份已 **GOV3 2026-09-12 全量转实**（32 单元包各按规格头性质清单
  断言+模板件可执行蓝本——治深度审计 P0 风险③；R2D 2026-09-02
  "移出收集"注记随批作废——实装后不收集=假覆盖，全量收集数
  1215→1406）；
- 只读锁定：`core/tests/`、`server/tests/` 与 **units_lib 包内 tests/**
  全部文件由 `test-lock.manifest.json`（sha256）+ 文件只读属性双重锁定
  （实测口径 270 键 = core/tests 139 + server/tests 39 + units_lib 包内
  92——GOV1 勘正：本页原漏 units_lib 面；core/tests 139 内含 core/tests/units_lib/ 2 件跨单元测试），
  `scripts/check_readonly.py` 与 `tests/arch/test_lock.py` 本地/CI 双验；
  漂移修复的机器半边=`scripts/draft_lock_manifest.py` 草稿器（差异三类
  清单+全根清单重锁命令，只读投影；CI gates 红面自动输出——ADR-015；
  重锁动作本身仍=人类执行 lock_tests.py+独立 [HUMAN-LOCK] commit）；
- 红绿纪律：每个测试先失败一次再通过；skip 数随里程碑归零（CI `-ra`；
  **平台守卫白名单外的 SKIPPED 即 CI FAIL——GOV1 A3 机器化**，白名单=
  「Windows 本地写屏障」只读属性豁免[CI/Linux 由 manifest 哈希覆盖]）；
- 快照回归：`tests/snapshots/`（syrupy）锚三导出产物内容哈希
  （xlsx/DXF/HTML——ADR-010）；快照红≠自动更新，先人审定性（预期漂移
  `--snapshot-update` 重录+diff 入批注记；非预期=回归缺陷走修复）；
  `__snapshots__/` 不入锁定清单，更新走显式命令+人审。
