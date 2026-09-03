# 项目文件迁移链 golden 样本（M1 起逐版累积）

> `project/migration.py` 每个迁移器（v(n)→v(n+1)）配一个旧版样本 JSON +
> 迁移后期望（golden）。样本由人类维护（锁定），实现不得自编。

```
migrations/
├─ README.md            # 本文件
├─ v2_0_to_3_0_input.json     # v2 样本（site 全子键、零 boundary——L4a 前盘实态形）
└─ v2_0_to_3_0_expected.json  # 迁移后期望（boundary 补默认空+版本头 3.0+来源版记录）
```

当前状态：v3.0 为当前 format_version（L4a boundary 红线键，GR-21 只增）。
v1→v2（M1 site 键）回归证据由 `tests/project/test_site_migration.py`
内置合成 fixture 承担（M1 简报 §二.4——该步不补样本）；v2→v3 起样本
对入链，`tests/project/test_migration.py` 的链式用例已接线。

样本纪律：content_hash 保留旧版占位（升版后自然失效——io R6 版本头
语义，迁移链不重算哈希）；expected=迁移器产出 model_dump 逐键相等面。
