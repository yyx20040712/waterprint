# 项目文件迁移链 golden 样本（M1 起逐版累积）

> `project/migration.py` 每个迁移器（v(n)→v(n+1)）配一个旧版样本 JSON +
> 迁移后期望（golden）。样本由人类维护（锁定），实现不得自编。

```
migrations/
├─ README.md            # 本文件
├─ v0_9_to_1_0_input.json     # 旧版样本（v0.9 为示例名，实际首个历史版由 M1 定）
└─ v0_9_to_1_0_expected.json  # 迁移后期望
```

当前状态：v1.0 是首个 format_version，尚无历史版需要迁移——
首个真实的向下兼容破坏（v1.1+）出现时，本目录开始累积样本，
`tests/project/test_migration.py` 的链式用例随之接线。
