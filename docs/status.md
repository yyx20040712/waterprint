<!-- 本文件由 scripts/gen_status.py 生成——禁手编；改指标集须同批重生成入库件。
     CI 零漂移检查：python scripts/gen_status.py --check（重生成与入库件字节比对）。 -->
# 项目状态计数（生成物——单一生成源）

> 复杂度治理方案四（2026-09-18）：**一切计数以本页生成值为准**，
> README/各文档不再手写数字。用例数与覆盖率以 CI 输出为准（文件派生
> 指标之外不生成——见页脚口径注记）。

| 指标 | 值 | 事实源 |
|---|---|---|
| CI 门禁数 | 18 | `scripts/run_gates.py` GATES 元组 |
| 测试锁面键数 | 372（core/tests 189 + server/tests 65 + units_lib 包内 92 + agent 26） | `test-lock.manifest.json` |
| OpenAPI | 39 路径 / 44 操作 | `api-contracts/openapi.json` |
| ADR 件数 | 26 | `docs/adr/ADR-*.md` |
| 未定义特性登记 | 总 67（已定义闭合 59 / 临置 0 / 待定义开放 2 / 待拍板 0 / 其他表述 6） | `docs/undefined-features-register.md` 表行 |
| 快照锚点 | 5（syrupy `# name:` 标记） | `core/tests/snapshots/__snapshots__/*.ambr` |
| 工艺单元包数 | 32 | `core/waterprint/units_lib/*/*/manifest.py` |
| webapp 测试文件数 | 113 | `webapp/src/**/*.test.*` |
| 数据包版本·assumptions | 1.0.0 | `data/assumptions/manifest.yaml` |
| 数据包版本·coefficients | 1.8.0 | `data/coefficients/manifest.yaml` |
| 数据包版本·constraint_kb | 2.1.0 | `data/constraint_kb/manifest.yaml` |
| 数据包版本·templates | 1.1.0 | `data/templates/manifest.yaml` |
| 数据包版本·unit_prices | 1.2.0 | `data/unit_prices/manifest.yaml` |

## 口径注记

- pytest/vitest **用例数与覆盖率**：以 CI 输出为准（环境派生，本页不生成）；
  本页测试面指标为文件派生口径（锁面键数=锁定文件数、webapp 测试文件数）。
- 系数/单价等**键级计数**：以装载探针（`core` 装载正门测试）为准；
  本页仅记数据包 `data_version`。
- 生成命令：`python scripts/gen_status.py`（纯标准库，仓库根运行）；
  再生成比对：`python scripts/gen_status.py --check`。
