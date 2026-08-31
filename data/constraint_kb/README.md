# constraint_kb —— 约束知识库

> **状态：1.0.0 起草态（AI 起草待领域专家追认）**——2026-08-31 夜班 CP1
> 批首批起草 18 条（enumeration_filter 6+effluent_standard 12），全部
> 入 `.workflow/pending-domain-expert.md` 追认清单晨报申报；追认后升
> 1.1.0 定稿。消费方=server `GET /api/constraints`（META1 静态目录端点
> 同构）+webapp ConstraintPicker（方案浏览枚举提交面）。

## 与规划期构想（本文件前版）的差异记档

前版（M0 槽位期）规划 YAML 分线四件+hard|warn 二级+「勾选条目进 design
态存 key」。v1.0.0 起草按 2026-08-31 用户裁决①（CP1 全链=枚举
options.constraints 通道）落地为：

- 单文件 `constraints.json`（18 条规模不分线；分线留扩容裁量）；
- severity 沿 **core 冻结面 Severity=ERROR/WARN/INFO**（contracts/
  unit_api.py D3——非 hard|warn 构想词）；本库条目全 WARN（沿 units_lib
  CONSTRAINTS 同级——建议带越出非强条）；
- 勾选面=**枚举请求 options.constraints[{key,expression,source}]
  通道**（worker→core apply_constraints，按次无状态）；「进 design 态
  存 key 不存表达式」=design 持久面构想**保留挂账**（产品裁决面）；
- DSL 白名单以 **core 实现为准**（<=|>=|<|>|∈ 与 and——README 前版
  `==`/`in` 为构想词，core 无此算符）；字段=枚举行字段命名空间
  （apply 时未知字段即拒——机制守卫）。

**沿用的前版硬规则**：条目 key 全库唯一且稳定（只增不改语义——key
进 API/UI 引用面）；表达式字段与常数禁无出处。

## 条目 schema（每条八键齐全）

```json
{
  "key": "vxinglvchi.v_filter_band",     // 全库唯一（UI/追认清单引用）
  "kind": "enumeration_filter",          // enumeration_filter | effluent_standard
  "unit_kinds": ["municipal_vxinglvchi"],// 适用单元（effluent 参考面恒 []）
  "label": "…（含字段名）",              // UI 显示（限值出处另列）
  "expression": "v_filter_act >= 7.0 and v_filter_act <= 10.0",  // core DSL
  "source": "GB 50013-2018 §9.5；给水排水设计手册（第 5 册 城镇排水）；起草表待追认",
  "severity": "WARN",
  "value_basis": "factor.… @ coefficients 1.1.0——AI 起草待追认"  // 数值溯源
}
```

## 数值与出处纪律（数据策略 v2）

- 过滤条目数值=coefficients `factors.yaml` **同值投影**（value_basis
  逐条注明源键）——数值真源在系数库，本库不另立权威；系数库升版须
  同步复核本库；
- 出处只标国标+给水排水手册两类；「待追认」注记逐条保留。

## 收录边界（v1.0.0——golden 实测）

- 默认栅格可枚举单元恰 5（vxinglvchi/ganhua/nongsuo/tuoshui/xiaohua；
  其余 GridTooLarge/InvalidGridError 不可达）；tuoshui 零收录——
  CONSTRAINTS 字段（dose_pam/p_cake）≠行字段（w_pam/ds_cake），跨命名
  映射禁自创留追认；
- units_lib 33 包 129 条 CONSTRAINTS 为**结果校核面**（factor.* 引用），
  与本库过滤面互补不替代——全量校核面接入另批；
- effluent_standard（GB 18918-2002 一级A/B×六项）：参考面——出水水质
  非枚举行字段（枚举行=设计变体量），过滤机制不可行故不供选；表达式
  字段（BOD5_out 等）为占位命名待校核面裁定。
