# constraint_kb —— 约束知识库

迁移来源：旧各 `discretization.json` 的 constraint_hints（51 条，§5）。
迁移时逐条复核出处（规范条文或工程惯例），复核人签字入 manifest。

## 文件规划（迁移期创建）

```
constraint_kb/
├─ manifest.yaml          # data_version + 逐条复核记录
├─ municipal.yaml         # 市政线约束条目
├─ mine_water.yaml        # 矿井水线条目
├─ sludge.yaml            # 污泥线条目
└─ conveyance.yaml        # 集配水线条目
```

## 条目 schema（每条必须齐全）

```yaml
- key: "municipal.aao.min_pool_count"   # 全库唯一（manifest/constraints 引用）
  expression: "n >= 2"                  # 受限 DSL：field_id 与常数比较 + AND
  severity: "hard"                      # hard（过滤）/ warn（警告）
  source: "GB 50014-2021 §x.x.x 或 工程惯例（注明年份/手册）"
  note: "可选说明"
```

## 硬规则

- 表达式 DSL 白名单：`>=` `<=` `>` `<` `==` `in` 与 `and`；
  字段必须是 dimensions 注册的字段 ID——加载时静态校验，失联 = 失败；
- UI 临时覆盖只在会话内；用户勾选的知识库条目进 design 态（存 key
  不存表达式）；
- 条目只增不改语义（key 稳定，进项目文件）。
