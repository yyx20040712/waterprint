# scripts —— CI 门禁脚本（纯标准库，系统 Python 直接可跑）

零第三方依赖：不装任何环境即可本地执行，与 CI 完全同口径。

```bash
python scripts/run_gates.py     # 一键跑全部门禁
```

| 脚本 | 门禁内容 | 规则出处 |
|------|----------|----------|
| check_file_budgets.py | 文件 ≤500 行；units_lib compute.py ≤400 | AGENTS 硬约束 |
| check_contract_headers.py | 每个 .py 契约头含 职责/输入/输出 | AGENTS 启动约束 / 硬约束 |
| check_grep_gates.py | grep 门禁：占位/裸 except/乱码 = 0；UTF-8 合法；compose 端口守卫（8000 不出容器网桥）。AUDIT-#20（b30）agent/ 全量纳管；宽族 except 精确豁免=gate_patterns.WIDE_EXCEPT_WAIVERS（键=文件+函数限定名+异常族，reason 非空强制，行号不作键；未消费豁免=腐烂报警；第四处宽族不在表必红，无整文件/整目录排除形态） | AGENTS 硬约束 |
| check_structure.py | 源码树 ↔ docs/file-contracts.md 双向同步；单元包固定结构（包计数 33 含 _template 模板登记行——实单元 32 口径见 check_module_graph.EXPECTED_UNIT_COUNT，AUDIT-#21 b30） | AGENTS 硬约束 |
| check_readonly.py | 测试只读（manifest 哈希 + 只读属性 + 无未登记文件） | AGENTS 硬约束（测试只读） |
| check_trust_root.py | 信任根守卫：三信任根（manifest/lock_tests/check_readonly）变更必带 [HUMAN-LOCK]（CI 查 push range；本地查工作树+HEAD） | AGENTS 硬约束（测试只读；外审整改#3 H1） |
| check_module_graph.py | 结构图谱：依赖沿层序向下/无环/与 import-linter 双源一致/单元包三方互验/调用链路径存在 | AGENTS 硬约束（分层依赖）/ docs/structure-graph.md |
| check_webapp.py | webapp 结构：TS 契约头（/** 职责/输入/输出 */）+ features 互不依赖分层 | file-contracts §5 |
| check_magic_numbers.py | 魔法数字：代码数值字面量仅限 registry/quantity 真源区（白名单值 0/1/2/10） | AGENTS 硬约束 / business-logic §9 |
| check_constraint_sync.py | 约束键同步：constraint_kb 键集与单元消费面一致 | file-contracts §4 |
| check_deprecation_gate.py | 弃用闸：被替代符号/路径的过渡期执法 | ADR |
| check_dim_labels_mirror.py | 出图表 dims 标签镜像：出图取数表与 registry 显示键镜像一致 | UF-32 |
| check_family_parity.py | 同族双胞胎结构恒等（aao/cass energy 族等；family_parity_lib 共享） | ADR-024 |
| check_lint_imports.py | import-linter 包装器（两 pyproject 契约实跑） | AGENTS 硬约束（分层依赖） |
| check_model_names.py | 仓内 markdown 禁 AI 模型代号 | AGENTS 硬约束 |
| check_mypy.py | mypy strict 包装器（venv 工具链） | — |
| check_out_dims_consistency.py | 单元 manifest out_dims 声明与实际输出键一致 | file-contracts §3 |
| check_ruff.py | ruff 包装器（venv 工具链） | — |
| run_gates.py | 门禁聚合入口（一键跑全部，CI gates job 同口径） | — |
| lock_tests.py | **仅人类执行**：生成锁定清单并设置只读属性（键集只增不减守卫：漏根挤出既有条目 → 拒写 return 2；`--prune` 显式放行） | AGENTS 硬约束（测试只读） |
| draft_lock_manifest.py | 锁面草稿器（只读，AI 可跑）：工作树实测 vs manifest 三类差异+全根清单重锁命令；CI gates 红面时自动输出 | ADR-015 |
| gen_contract_lines.py | file-contracts「N 行」注记数字刷新（幂等；在场/缺席人审定夺） | ADR-016 |
| gen_structure_nodes.py | §1a 节点表标记段展开（两 pyproject layers 契约+固定三叶；忘跑检测器=check_module_graph） | ADR-017 |
| structure_nodes_lib.py | §1a 取数/渲染/标记段共享库（校验端+生成端单源） | ADR-017 |
| gen_same_layer_edges.py | §1c 同层边声明块生成（same_layer_lib 共享） | ADR-014 |
| same_layer_lib.py | 同层边取数/渲染共享库 | ADR-014 |
| family_parity_lib.py | 同族结构恒等共享库（check_family_parity 消费） | ADR-024 |
| gen_status.py | docs/status.md 计数再生成为（门禁/锁面/OpenAPI/ADR/单元包/测试计数单源） | ADR-023 |
| gate_patterns.py | 特征串集中定义（供上面脚本与 pytest 复用）+ 宽族 except 豁免登记面 WIDE_EXCEPT_WAIVERS（AUDIT-#20，b30） | — |

> venv 内工具链（ruff/mypy/import-linter/pytest/coverage）在 CI 与
> `uv run` 环境中执行，不在本目录重复实现。

## lock_tests.py 用法（仅人类执行，AGENTS 硬约束·测试只读）

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
  units_lib 包内 tests 条目——尾句随旗标条件化：未带 `--prune` 时
  "若既有条目被挤出将由守卫拦截"；带 `--prune` 时"--prune 已放行：
  本次可能直接删除既有条目"）。
