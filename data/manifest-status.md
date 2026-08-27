# data 版本清单（各数据包 manifest 槽位说明）

> 四个数据包的 `manifest.yaml` 槽位状态：**coefficients 0.1.0 已按 ADR-009
> 拍板口径落库并经 2026-08-23 领域专家签字生效**；templates 1.0.0 正式
> 模板已录入（DRAFT 批 2026-08-26）；其余两包仍为 0.0.0 槽位，
> 真实条目随 M0 §9.5 迁移与后续里程碑录入，录入时同步升版
> ——data_version 进入可复算三元组（§16 A8）。

| 包 | 当前状态 | 首个真实版本归属 |
|----|----------|------------------|
| unit_prices | 0.0.0（空，待迁移 2019 黑龙江定额并抽验 10%） | M0 数据迁移 |
| constraint_kb | 0.0.0（空，待迁移 51 条 constraint_hints 并逐条复核出处；条目可挂"失败时建议"字段，见 business-logic §4） | M0/M1 |
| coefficients | 0.5.0（M3a1 矿井水线八单元批：factor.mine_<短名>.* 共 109 条[平流沉砂/四分区磁混凝/磁分离/无回流高密/低滤速精滤/灯管实算紫外——与市政同名键 mine_ 限定物理隔离] + removal 13 条[SS/COD 双指标面，BOD5 全线不建——B/C=0.025 无生化性；零去除显式 0.0 照 M2b1/M2c 先例]，AI 起草 2026-08-27 数据策略 v2，**领域专家批量追认待补**；0.4.0 及以前 299 键不扰动[逐键零扰动探针实录]） | M1（0.1.0 签字）/M2（0.2.0~0.4.0 追认）/M3（0.5.0 追认） |
| templates | 1.0.0（DRAFT 批 2026-08-26：calcbook_unit.xlsx 单单元[trace 五字段占位行×5]+calcbook_plant.xlsx 全厂[{{summary.design.*}} 终水六指标族]，M1b 冻结语法、openpyxl 生成零公式；TEMPLATE_REGISTRY 扩两键；summary 面真值依赖 plant.summary——executor 现状空注入，D10 落地批接真实汇总） | M2 出图批（UF-16 收口） |
