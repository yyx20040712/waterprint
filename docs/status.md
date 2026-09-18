<!-- 本文件由 scripts/gen_status.py 生成——禁手编；改指标集须同批重生成入库件。
     CI 零漂移检查：python scripts/gen_status.py --check（重生成与入库件字节比对）。 -->
# 项目状态计数（生成物——单一生成源）

> 复杂度治理方案四（2026-09-18）：**一切计数以本页生成值为准**，
> README/各文档不再手写数字。用例数与覆盖率以 CI 输出为准（文件派生
> 指标之外不生成——见页脚口径注记）。

| 指标 | 值 | 事实源 |
|---|---|---|
| CI 门禁数 | 15 | `scripts/run_gates.py` GATES 元组 |
| 测试锁面键数 | 296（core/tests 142 + server/tests 43 + units_lib 包内 92 + agent 19） | `test-lock.manifest.json` |
| OpenAPI | 32 路径 / 35 操作 | `api-contracts/openapi.json` |
| ADR 件数 | 22 | `docs/adr/ADR-*.md` |
| 未定义特性登记 | 总 52（已定义闭合 30 / 临置 0 / 待定义开放 11 / 待拍板 2 / 其他表述 9） | `docs/undefined-features-register.md` 表行 |
| 快照锚点 | 4（syrupy `# name:` 标记） | `core/tests/snapshots/__snapshots__/*.ambr` |
| 工艺单元包数 | 32 | `core/waterprint/units_lib/*/*/manifest.py` |
| webapp 测试文件数 | 65 | `webapp/src/**/*.test.*` |
| 数据包版本·coefficients | 1.2.0 | `data/coefficients/manifest.yaml` |
| 数据包版本·constraint_kb | 1.4.0 | `data/constraint_kb/manifest.yaml` |
| 数据包版本·templates | 1.1.0 | `data/templates/manifest.yaml` |
| 数据包版本·unit_prices | 1.0.0 | `data/unit_prices/manifest.yaml` |

## 口径注记

- pytest/vitest **用例数与覆盖率**：以 CI 输出为准（环境派生，本页不生成）；
  本页测试面指标为文件派生口径（锁面键数=锁定文件数、webapp 测试文件数）。
- 系数/单价等**键级计数**：以装载探针（`core` 装载正门测试）为准；
  本页仅记数据包 `data_version`。
- 生成命令：`python scripts/gen_status.py`（纯标准库，仓库根运行）；
  再生成比对：`python scripts/gen_status.py --check`。
