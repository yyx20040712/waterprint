# cost —— 概算视图

分部分项/措施/间接/预备/税分级表 + 单位造价指标校核展示（消费 /api/cost
响应——core cost 四模块服务端装配投影）。

## 文件清单（FE8 批 6b 段六实装 2026-08-29）

| 文件 | 职责 | 状态 |
|------|------|------|
| `lib/estimateView.ts` | 纯函数层：narrowCostResponse 窄化门（顶层七字段+sheet 小计族六数值+明细九字段[含 name_zh]+四费桶六字段+三元组+指标五键逐项校验，非法抛 CostViewError 带键定位）+buildTableRows 分级行模型（行序=服务端装配序，小计族+grand 高亮 kind，detail 行挂 trace 溯源）+reproString 三元组串 | FE8 实装 |
| `lib/estimateView.test.ts` | 投影层纯函数 vitest（node 环境——golden 真值同构内联夹具+负例族 16 用例） | FE8 实装（16 绿） |
| `api/useCostQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/cost/${projectId}', params?]（conditionKey 全量进键）+select 窄化收口 | FE8 实装 |
| `components/EstimateTable.tsx` | 分级汇总表（antd Table——明细行可展开溯源：定额键+source_field_ids+单价+repro 串；小计/总投资高亮；金额 tabular-nums 右对齐） | FE8 实装（薄壳不测） |
| `components/IndicatorsCard.tsx` | 指标对照卡（OK 绿合格/WARN 橙警告/checked=false 灰「未校核」——§19.3 语义色纪律） | FE8 实装（薄壳不测） |
| `store/costStore.ts` | 视图态占位维持（工况态组件内 useState——FE5/6/7 先例） | 占位（激活挂账 UX 批） |

## 规格要点（FE8 后实况）

- 概算数据全部来自服务端（GET /api/cost latest done calc 四模块装配：
  load_prices→load_fee_rules→takeoff_quantities→build_estimate→
  check_indicators——计算在 Python 单点 §11 R12，前端零算价）；
- 每笔金额可点开溯源（定额键+source_field_ids+三元组 repro 串——M4
  "任一数字可回溯"的前端落点；深链 calcbook 挂账 M4④）；
- 表列中文列名=name_zh 服务端下发单一真源直投（PriceBook.name——
  骨架「中文列名走 i18n 显示层」措辞随 FE8 D4 裁决收口：不建前端
  i18n 体系；fee 行 label=fee_key 字段 ID 原样透传）；
- 概算绑定 condition_key（缺省=design 基线档 D2——服务端回显；
  切换显式=查询键切换按需触发 §17.1）；
- WARN 是诚实读数（偏离经验带非阻塞——如实橙警不美化成绿）；
  estimate 文件导出（501）与 estimate_unit.xlsx 模板归 M3 沿册——
  面板不放导出按钮。
