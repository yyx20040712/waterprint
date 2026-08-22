# data —— 版本化数据资产

> 一切数据带**版本与出处**；内核零硬编码（公式数值的真相要么在规范条文，
> 要么在这里）。数据包只读：写入走版本化发布流程，不在运行时修改。

| 目录 | 内容 | 消费方 |
|------|------|--------|
| `unit_prices/` | 定额单价（YAML，每条带出处；2019 黑龙江迁移，抽验 10%） | cost/prices.py |
| `constraint_kb/` | 约束知识库（旧 constraint_hints 51 条迁移） | solution/constraints.py |
| `coefficients/` | 去除率/经验系数/指标带（随规范版本演进） | registry/coefficients.py |
| `templates/` | Excel 模板（计算书/管网，禁公式） | trace/calcbook.py、network/excel_io.py |

## 数据包通用规则

1. 每个包目录含 `manifest.yaml`：`data_version`（语义化版本）+ 变更记录；
   `data_version` 进入可复算三元组（§16 A8）。
2. 每条数据必须带 `source`（定额子目号/规范条文/手册页码）；
   无 source 条目加载即失败（代码侧强制）。
3. 迁移旧数据时人工抽验并记录在包 manifest（谁、何时、抽验比例）。
4. 文件 UTF-8；数值单位在字段名或 `unit` 字段显式声明（规范单位）。
