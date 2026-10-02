# 项目文件迁移链 golden 样本（M1 起逐版累积）

> `project/migration.py` 每个迁移器（v(n)→v(n+1)）配一个旧版样本 JSON +
> 迁移后期望（golden）。样本由人类维护（锁定），实现不得自编。

```
migrations/
├─ README.md            # 本文件
├─ v2_0_to_3_0_input.json     # v2 样本（site 全子键、零 boundary——L4a 前盘实态形）
├─ v2_0_to_3_0_expected.json  # 迁移后期望（boundary 补默认空+版本头随链尾推进
│                              #   ——inlet-m3d 批 2026-10-02 起为 4.0 到达态）
├─ v3_0_to_4_0_input.json     # v3 样本（municipal_input inlet m³/s 旧口径+
│                              #   hebing 形单元节点 m³/d 面负锚——inlet-m3d 前盘实态形）
└─ v3_0_to_4_0_expected.json  # 迁移后期望（inlet q ×86400 round6+版本头 4.0+
                               #   来源版记录；hebing/junction/recycle 零触碰）
```

当前状态：v4.0 为当前 format_version（inlet-m3d 批 2026-10-02——进水参数面
m³/s→m³/d 换轴：municipal_input 节点 q_avg_daily ×86400 round(x,6) 定版，
勘察冻结=恰该 kind 携带该参数）。v1→v2（M1 site 键）回归证据由
`tests/project/test_site_migration.py` 内置合成 fixture 承担（M1 简报
§二.4——该步不补样本）；v2→v3 起样本对入链，`tests/project/test_migration.py`
的链式用例已接线（含 v3→v4 舍入口径锚+1.0→4.0 跳级用例）。

样本纪律：content_hash 保留旧版占位（升版后自然失效——io R6 版本头
语义，迁移链不重算哈希）；expected=迁移器产出 model_dump 逐键相等面。
