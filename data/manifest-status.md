# data 版本清单（各数据包 manifest 槽位说明）

> 四个数据包的 `manifest.yaml` 槽位状态（**doc-health 批 2026-09-13
> 追加制回写**——0.8.0~1.2.0 间各包升版曾漏更本表，历史行原样保留，
> 现行版本以各行「→现」注记+包内 manifest.yaml 变更注释段为准——
> **单一真相源=各包 manifest.yaml**，本表=索引快照）：
> coefficients **1.2.0**/constraint_kb **1.4.0**/templates **1.1.0**/
> unit_prices **1.1.0**（批6d unit_scales 金额倍率契约+aao 曝气系统条目）。

| 包 | 当前状态 | 首个真实版本归属 |
|----|----------|------------------|
| unit_prices | 0.0.0（空，待迁移 2019 黑龙江定额并抽验 10%）→1.0.0（COST1 三 YAML 81 条迁移+RATIFY3 批准放行 2026-08-28——数据策略 v2 全程；结构修正 data_version→price_data_version 不升版注记）→**现 1.1.0**（批6d 2026-09-26：unit_scales 金额倍率契约新增〔万元族消费面×10⁴ 折元〕+installations 增 aao.microporous_aerator_piping〔82 条〕——既有条目面值零变更；详见包内 manifest 变更注释） | M0 数据迁移 |
| constraint_kb | **1.1.0 已追认定稿（Ruling 2026-08-31 全部追认——18 条+边界三裁批复生效，标记回写 RATIFY2 先例）**→**现 1.4.0**（1.2.0 L4b spacing_check 2 条 2026-09-03→1.3.0 追认定稿 Ruling 同日→1.4.0 SPC2 boundary_check 红线越界 1 条 2026-09-05；详见包内 manifest 变更注释）[前史 1.0.0 起草态：18 条=enumeration_filter 6[默认栅格可枚举 5 单元中 4 个的行字段精确匹配条目——值=coefficients 1.1.0 同值投影 value_basis 逐条溯源；tuoshui 零收录（dose_pam↔w_pam 跨命名映射禁自创留追认）]+effluent_standard 12[GB 18918-2002 一级A/B×六项参考面——出水水质非枚举行字段 unit_kinds 恒空不供选]；消费面=GET /api/constraints+ConstraintPicker（枚举 options 通道）；schema 与 M0 规划构想差异记档 README] | CP1 起草（2026-08-31）/Ruling 追认（2026-08-31） |
| coefficients | 0.7.0（M3c 输送线四单元批——三线齐备收尾[32/32 单元包数据面齐]：factor.<裸短名>.* 共 48 条[集水井=汇流容积法+停留校核+圆形井构造/配水井=均匀分流+孔口 μ 反解水头+k_uneven 余量+井室构造[多出流口 n 参数化——动态多口口径表内冻结]/集配水井=汇流+分流合一单节点/配水渠=明渠输配+侧堰配水+渠末防淤校验]——**裸短名形态**[conveyance_ 前缀剥离 M3a1 期已预置，本批零代码改造]；**removal_rates.yaml 零新增**[穿流单元零水质去除——水量/水质全透传不建 removal 键，照 0.6.0 口径注记在册]；出处仅 GB 50014-2021[§6.1 集水池参照+§6 超高+§7.1 并联系列+§4 渠道流速/超高]+给水排水手册两类，AI 起草 2026-08-27 数据策略 v2，**三线 0.5.0~0.7.0 已追认（RATIFY2 2026-08-28——19 表签字栏+removal 头部回写在册；条号章级标注挂账延续）**；0.6.0 及以前 497 键不扰动[四面逐键比对探针实录]）→**现 1.2.0**（0.8.0 NP1 N/P 建模数据批→0.9.0 I3 出处白名单 CJJ 131→1.0.0 NET1 管网曼宁 21 条[RATIFY4 2026-08-28]→1.1.0 GOLDEN3 std.gb3838_iii 五键→1.2.0 曝气头 service_area 2 键 2026-09-13[579 键]；详见包内 manifest 变更注释） | M1（0.1.0 签字）/M2（0.2.0~0.4.0 追认）/M3（0.5.0~0.7.0 已追认 RATIFY2） |
| templates | 1.0.0（DRAFT 批 2026-08-26：calcbook_unit.xlsx 单单元[trace 五字段占位行×5]+calcbook_plant.xlsx 全厂[{{summary.design.*}} 终水六指标族]，M1b 冻结语法、openpyxl 生成零公式；TEMPLATE_REGISTRY 扩两键；**summary 真值已接通（D10 批 2026-08-28：app 层 `_summary_of` 注入+e2e replace 移除+平键集复核完成——design 六键与占位符恰合零变更，不升版）**）→**现 1.1.0**（NET1 管网管段输入模板 network_pipes.xlsx 录入 2026-08-28——列位映射即模板本体；详见包内 manifest 变更注释） | M2 出图批（UF-16 收口——全链闭合） |
