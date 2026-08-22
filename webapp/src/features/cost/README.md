# cost —— 概算视图

分部分项/措施/间接/预备/税分级表 + 单位造价指标校核展示。

## 文件规划（实装期创建，先登记 file-contracts.md）

| 文件 | 职责 |
|------|------|
| `components/EstimateTable.tsx` | 分级汇总表（可折叠行 + 每笔溯源列：定额键/来源字段） |
| `components/IndicatorsCard.tsx` | 指标对照（带内/偏离状态，语义色） |
| `store/costStore.ts` | 视图 slice |
| `api/` | 生成客户端调用 |

## 规格要点

- 表列按字段 ID 取数（生成类型）；中文列名走 i18n 显示层；
- 每笔金额可点开溯源（定额键 + source_field_ids + 三元组）——
  M4"任一数字可回溯"的前端落点；
- 概算绑定 condition_key（默认 design 档，切换显式）。
