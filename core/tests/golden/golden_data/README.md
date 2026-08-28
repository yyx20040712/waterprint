# golden_data —— 端到端期望值数据（只读，与测试同锁）

> 期望值唯一合法来源：docs/norms 手算对照表 + 旧系统结果（差异逐条
> 解释）。由领域专家录入并签字；实现者不得自编数字。
> 数据未就位的目录只有本说明文件——对应端到端测试自动跳过。

```
golden_data/
├─ README.md                          # 本文件
├─ municipal_34760/                   # 市政案例（M2 验收）
│  ├─ README.md                       # 数据整理要求（三件套见 docs/golden-cases.md）
│  ├─ input_project.json              # 待领域专家整理（进水/标准/工艺图/参数/工况）
│  ├─ expected_summary.json           # 待整理（每项标注来源与容差）
│  └─ notes.md                        # 原始设计资料口径注记
├─ mine_43836/                        # 矿井水案例（M3 验收），结构同上
├─ municipal_34760_recycle/           # 市政回流案例（GOLDEN3——前向叠加口径），结构同上
├─ municipal_34760_loop/              # 市政真环案例（GOLDEN4b——产泥真边+真回流 SCC/solve_loop 收敛）
├─ migrations/                        # 项目文件迁移链 golden 样本（M1 起逐版累积）
└─ m3_incremental_seed.json           # 增量==全量 性质测试种子（M1/M3）
```

录入完成后运行 `python scripts/lock_tests.py` 刷新锁定清单（人类操作）。
