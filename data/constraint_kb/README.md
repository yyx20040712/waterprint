# constraint_kb —— 约束知识库

> **状态：1.5.0（全量 29 条——存量 20 条已追认：18 条=Ruling 2026-08-31、
> spacing_check 2 条=Ruling 2026-09-03；boundary_check 1 条=SPC2 批
> 2026-09-05 工程惯例起草待专家确认；geometry_guard 8 条=批3b 2026-09-26
> b3a-research.md §二 B 组+§七追认单直录——D 级 AI 推导值经用户「全部
> 追认」生效）**；批复记录=.workflow/ledger.md 两日 Ruling 条目+
> pending-domain-expert.md §22/§24 销账注+backend-calc-complete/
> b3a-research.md §七。
> 唯一未来项：干化全干化档另立待起草追认。消费方=server `GET /api/constraints`（META1 静态目录端点
> 同构）+webapp ConstraintPicker（方案浏览枚举提交面）+`GET /api/site/spacing`
> （L4b 间距校核——spacing_check 阈值数据面；SPC2 起 boundary_check
> severity 数据面同端点）。

## 与规划期构想（本文件前版）的差异记档

前版（M0 槽位期）规划 YAML 分线四件+hard|warn 二级+「勾选条目进 design
态存 key」。v1.0.0 起草按 2026-08-31 用户裁决①（CP1 全链=枚举
options.constraints 通道）落地为：

- 单文件 `constraints.json`（18 条规模不分线；分线留扩容裁量）；
- severity 沿 **core 冻结面 Severity=ERROR/WARN/INFO**（contracts/
  unit_api.py D3——非 hard|warn 构想词）；本库条目全 WARN（沿 units_lib
  CONSTRAINTS 同级——建议带越出非强条）。〔执法口径注记 2026-09-26 批5
  AUD-W10：**勾选即硬滤全级别**（CP1 用户裁决 2026-08-31「勾选=过滤」
  ——用户显式勾选=自愿升级为强制）；severity=呈现分类元数据，不构成
  执法分级——WARN 软语义（未勾选默认态的越带注记不滤）属产品裁决位
  呈报待裁，见接力板批次日志 Rulings〕；
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
  "kind": "enumeration_filter",          // enumeration_filter | effluent_standard | spacing_check | boundary_check | geometry_guard
  "unit_kinds": ["municipal_vxinglvchi"],// 适用单元（effluent 参考面恒 []；spacing_check []=全对通用/两键=限定对；boundary_check 恒 []=全构筑物；geometry_guard 恒 AAO/CASS 双键）
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
- spacing_check（L4b 1.2.0 增 2 条——间距校核面）：expression 契约固定为
  `min_clearance_m >= <float>`（**server services/site.py 是唯一解析面**——
  core geometry/spacing 收结构化阈值不解析 DSL；形态越界=fail-visible 拒）；
  unit_kinds 空=全对通用（装配面 None 语义）、两键=限定对（对内双方 kind
  均须在键集）；净距口径=OBB 点-边枚举精确距（SPC2 起——webapp
  siteGeometry measureToNearest 同式镜像所见即所得；旋转 0° 恒等旧
  AABB 式回归锚在册）。数值=GB 50016 防火间距族**类比起草态，已追认**
  （Ruling 2026-09-03——pending-domain-expert.md §24 销账注；value_basis
  逐条标注。L4b 笔「§23」引用系悬空——追认节实登 §24）。
- boundary_check（SPC2 1.4.0 增 1 条——用地红线越界校核面）：expression
  契约固定为 `containment == inside`（**server services/site.py 是唯一
  解析面**——产出 severity；core geometry/boundary 判定 OBB 四角内含，
  不解析 DSL；形态越界=fail-visible 拒；条目缺席=不校核零违规）；
  unit_kinds 恒空=全构筑物；无数值阈值。severity=ERROR 系工程惯例
  「总图构筑物不得越用地红线」**类比起草态待专家确认**（数据策略 v2
  ——pending-domain-expert.md 新节登记）。
- geometry_guard（批3b 1.5.0 增 8 条——几何域拒面）：四量（l_pool/
  b_pool/v_pool/n_aerator）各提示/拒收双门，expression=单侧
  `field > <float>`（**真=越门**——与 enumeration_filter 可行带「真=在带」
  极性相反；消费走 solution apply_constraints 行字段布尔过滤同通道，
  severity=WARN 超工程常用提示/ERROR 荒诞域拒收=分层防御元数据）；unit_kinds
  一律 `["municipal_aao","municipal_cass"]`（两包 out_dims 均含四量同名
  行字段，量级同域可用——AAO v_pool=池体构造容积/CASS=单池有效容积）。
  **数值权威=b3a-research.md §二 B 组+§七追认 2026-09-26**（用户「全部
  追认」——D 级 AI 推导值经追认生效；无 coefficients 源键=本库首次
  追认单直录形态，value_basis 逐条溯源——锚=GB 50014-2021 §7.5.10-1
  类比+§7.9.6 方法学+白龙港实践包络推导链，见 b3a §三独立复算）。
- 裕度语义（backend-calc-complete 批2a 2026-09-25——裁决①）：枚举
  margin_min 裕度列=行对**已追认双侧带条目**（`x >= a and x <= b` 形）
  的归一距离 min(v−a, b−v)/(b−a) 行级取最紧（core
  constraints.band_margin_column；与 UI 勾选/过滤同一约束集同源）。
  单侧/∈ 档形态无带宽概念不产出裕度——覆盖面随本库扩条渐进；
  数值零新增（带值即已追认约束值）。
