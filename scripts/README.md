# scripts —— CI 门禁脚本（纯标准库，系统 Python 直接可跑）

零第三方依赖：不装任何环境即可本地执行，与 CI 完全同口径。

```bash
python scripts/run_gates.py     # 一键跑全部门禁
```

| 脚本 | 门禁内容 | 规则出处 |
|------|----------|----------|
| check_file_budgets.py | 文件 ≤500 行；units_lib compute.py ≤400 | AGENTS §2 / §13.7 |
| check_contract_headers.py | 每个 .py 契约头含 职责/输入/输出 | §13.2 / §13.7 |
| check_grep_gates.py | grep 门禁：占位/裸 except/乱码 = 0；UTF-8 合法 | AGENTS §3 / §6.7 |
| check_structure.py | 源码树 ↔ docs/file-contracts.md 双向同步；单元包固定结构 | §13.7 / §13.6 |
| check_readonly.py | 测试只读（manifest 哈希 + 只读属性 + 无未登记文件） | AGENTS §7 |
| lock_tests.py | **仅人类执行**：生成锁定清单并设置只读属性 | AGENTS §7 |
| gate_patterns.py | 特征串集中定义（供上面脚本与 pytest 复用） | — |

> venv 内工具链（ruff/mypy/import-linter/pytest/coverage）在 CI 与
> `uv run` 环境中执行，不在本目录重复实现。
