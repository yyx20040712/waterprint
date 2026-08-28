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
| check_module_graph.py | 结构图谱：依赖沿层序向下/无环/与 import-linter 双源一致/单元包三方互验/调用链路径存在 | AGENTS §13 / docs/structure-graph.md |
| check_webapp.py | webapp 结构：TS 契约头（/** 职责/输入/输出 */）+ features 互不依赖分层 | §13.5 / file-contracts §5 |
| check_magic_numbers.py | 魔法数字：代码数值字面量仅限 registry/quantity 真源区（白名单值 0/1/2/10） | AGENTS §3 / business-logic §9 |
| run_gates.py | 门禁聚合入口（一键跑全部，CI gates job 同口径） | — |
| lock_tests.py | **仅人类执行**：生成锁定清单并设置只读属性（键集只增不减守卫：漏根挤出既有条目 → 拒写 return 2；`--prune` 显式放行） | AGENTS §7 |
| gate_patterns.py | 特征串集中定义（供上面脚本与 pytest 复用） | — |

> venv 内工具链（ruff/mypy/import-linter/pytest/coverage）在 CI 与
> `uv run` 环境中执行，不在本目录重复实现。

## lock_tests.py 用法（仅人类执行，AGENTS §7）

```bash
python scripts/lock_tests.py                    # 锁定两默认根（core/tests + server/tests）
python scripts/lock_tests.py <额外测试目录>...   # 追加锁定（如 units_lib 包内 tests）
python scripts/lock_tests.py --prune <路径...>   # 显式放行删除既有条目（慎用）
```

- **键集只增不减守卫**（COST2 事故设防）：写出前比对现有
  test-lock.manifest.json 键集——本次结果会删除既有条目（典型：
  裸跑默认两根，挤出 units_lib 包内 tests 条目）且未带 `--prune`
  时**拒绝写出**（return 2，manifest 字节不变），并提示携带覆盖
  旧条目的完整根清单重跑；确属有意删除才加 `--prune` 放行。
- **裸跑防呆警示**：无任何路径参数时打印一行警示（默认两根不含
  units_lib 包内 tests 条目，若既有条目被挤出将由守卫拦截）。
