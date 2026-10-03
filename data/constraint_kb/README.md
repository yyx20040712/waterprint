# constraint_kb —— 约束知识库

> **状态：1.7.0 起草态（全量 41 条=34 追认存量+input_band 7 条 AI 起草
> 待追认〔§1a1 清单——.workflow/1a1-20261003/draft-table.md 起草表〕：
> Kz 总变化系数静态包络带+进水六指标浓度上限带，追认单直录形态）——
> 存量 29 条中 28 条+1.6.0 扩 5 条已追认：18 条=Ruling
> 2026-08-31、spacing_check 2 条=Ruling 2026-09-03；boundary_check 1 条=SPC2 批
> 2026-09-05 工程惯例起草待专家确认；geometry_guard 8 条=批3b 2026-09-26
> b3a-research.md §二 B 组+§七追认单直录——D 级 AI 推导值经用户「全部
> 追认」生效；**enumeration_filter 新增 5 条双侧带=margin-kb-20261001 批
> 2026-10-01 起草→已追认定稿 1.6.1（Ruling 2026-10-01——§32 四裁量
> 全数生效，含 ns_act 语义迁移 R1 成立/缺氧 HRT 子带 R2 维持）**〔数值=
> factors.yaml 已追认键同值投影，C3 门禁恒等〕）；
> 批复记录=.workflow/ledger.md 两日 Ruling 条目+
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
  ——登记锚=UF 登记表 UF-54（批6h 2026-09-27 注记升级：板面日志过程指针→仓内持久锚；勾选即硬滤口径维持；**UF-54 已拍板 2026-09-28=显式不做软语义**〔用户裁决·relay 增补六十三：越带几何量〔如超大单池〕属应滤除设计——工程正解=上调池数而非单池做大；勾选即硬滤全级别为定版口径〕）〕；
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
  `field <= <float>`（**真=门内合规**、越门=假被滤——与
  enumeration_filter 可行带「真=在带」极性统一，勾选=过滤越门行；
  门一回炉轮2 B1 勘正：初版 `>` 越门极性致 feasible 集合语义倒置，
  阈值数值零变；恰等值=门内保留=严格越门语义）；消费走 solution
  apply_constraints 行字段布尔过滤同通道，severity=WARN 超工程常用
  提示/ERROR 荒诞域拒收=分层防御元数据；unit_kinds
  一律 `["municipal_aao","municipal_cass"]`（两包 out_dims 均含四量同名
  行字段，量级同域可用——AAO v_pool=池体构造容积/CASS=单池有效容积）。
  **数值权威=b3a-research.md §二 B 组+§七追认 2026-09-26**（用户「全部
  追认」——D 级 AI 推导值经追认生效；无 coefficients 源键=本库首次
  追认单直录形态，value_basis 逐条溯源——锚=GB 50014-2021 §7.5.10-1
  类比+§7.9.6 方法学+白龙港实践包络推导链，见 b3a §三独立复算）。
- input_band（1A1 批 1.7.0 增 7 条——进水输入合理性带）：横切**全厂进水
  输入面**的合理性带（非单元包、非枚举行字段——unit_kinds 恒空=全适用
  语义，boundary_check 空表先例；README 归属声明表 Kz/水质两行的数据面
  载体）。两形态：`inlet.kz_band` 同字段双侧带 `kz >= 1.3 and
  kz <= 2.7`（Kz 静态包络——GB 50014-2021 总变化系数表端点；流量相关
  精确内插表显式挂账不录=设计计算辅助非输入合理性校核）；六指标上限带
  `inlet.quality_upper.<sym>` 单侧 `field <= max`（字段=契约既有进水面
  命名 BOD5/CODCR/SS/NH3N/TN/TP——contracts 冻结面直用，非新建命名）。
  severity 全 WARN（逐条定级归 1A6 批）；数值=追认单直录起草（无
  coefficients 源键——geometry_guard 先例；手册原册页级复核归追认批，
  起草表=§1a1 清单）。**消费面=零**（core solution 装载器不拒不裁——
  kind 空表数据面门禁归 kb 数据批 R10 口径；kb 执法面 `_maint_face`
  适用判据 `unit_kind in unit_kinds` 对空表恒不选中；枚举面仅消费调用
  方显式勾选——执法面接线归 1A2 校验骨架批）。
- 裕度语义（backend-calc-complete 批2a 2026-09-25——裁决①）：枚举
  margin_min 裕度列=行对**已追认双侧带条目**（`x >= a and x <= b` 形）
  的归一距离 min(v−a, b−v)/(b−a) 行级取最紧（core
  constraints.band_margin_column；与 UI 勾选/过滤同一约束集同源）。
  单侧/∈ 档形态无带宽概念不产出裕度——覆盖面随本库扩条渐进；
  数值零新增（带值即已追认约束值）。
  **覆盖扩展（margin-kb-20261001 批 1.6.0）**：本批前双侧带仅 5 条
  且集中于 4 个辅助单元（vxinglvchi/ganhua/nongsuo/xiaohua）——AAO/
  CASS 两族零带条目→主单元枚举行 margin_min 恒 NaN=「最小裕量」列
  全空根因（est 批档下棒指针；基线实锤=.workflow/margin-kb-20261001/
  baseline_probe.py 面 1）。本批增 5 条双侧带（aao.hrt_anoxic_band/
  aao.sludge_age_band/cass.sludge_age_band/cass.draw_band/
  cass.ns_act_band——字段=两包 out_dims 行字段 t_n/theta_c/h_draw/
  ns_act；数值=units_lib 校核面同键带 factors.yaml 已追认值同值投影，
  「校核面与本库过滤面互补不替代」口径下的过滤面首批接入）——扩条后
  两族 margin_min 全行产出（探针面 2 实录+归一距离逐位对拍 0 失败）。
  已追认定稿（1.6.1——Ruling 2026-10-01 §32 四裁量全数生效：R1 ns_act
  语义迁移成立/R2 缺氧 HRT 维持常用子带 2~4h/R3 起草态可用口径确认/
  R4 过滤面首批接入披露确认）；tuoshui 零收录维持（跨命名映射禁自创
  挂账不动）。
  **口径三注（margin-kb-20261001 门一双审回炉笔）**：①追认粒度=数值级
  ——margin 消费判据是双侧带形态非条目追认标记（「已追认双侧带」的
  批2a 措辞指带值数值溯源，起草态条目勾选后同样产出裕度；追认锁定
  的是收录面定稿标记——1.6.1 起五键已定稿）；②NaN 行字段——行级域拒行不入枚举 rows
  （批5 AUD-W5 前置），过滤面无「NaN 行静默滤除」通路；③负裕度——
  band_margin_column 对全行计算可负，但呈现面=feasible 行（带外行
  勾选即滤不呈现），呈现口径恒带内非负（恰等下界=0）。

## 输入合理性带归属声明（UF-24 定版——批6k 2026-09-29）

> 模式定版（flow.py R3 的 Kz 口径推广全量化）：**契约只守数学不变量**
> （正性/有限性/派生一致性——拒 NaN/负值/越界构造）；**行业合理性带=
> 数据面**（constraint_kb 条目或 units_lib manifest range，出处纪律+
> 追认制——数据策略 v2，禁无出处数值）。各量归属逐行声明：

| 量 | 带内容 | 载体（唯一归属） | 执法面 | 状态 |
|----|--------|------------------|--------|------|
| Kz（总变化系数） | 行业上下限 | constraint_kb `input_band`（inlet.kz_band——1A1 批 1.7.0 录入，静态包络带；流量相关精确内插表挂账不录） | 待执法面接线（1A2 校验骨架——kb 执法面按 unit_kinds 选中，空表恒不选中） | 已录入起草态待追认（§1a1 清单——手册原册页级复核归追认批） |
| q_avg_daily（厂界流量） | A-1~A-3：≤0 或 >60 m³/s 拒收；(0,10 m³/d) 与 >100 万 m³/d 提示不阻塞 | `flows/params_guard.py` builtin 常量（builtin kind 无 manifest——锚=b3a-research §二 A 组+§七追认 2026-09-26） | server 422 整批拒+core ParamVerdict | 已落地（批3b） |
| 单元参数（30 包 94 条） | 手册表出处 range（闭区间 GR-06） | units_lib manifest `params.range` | `params_guard` face④ 闭区间执法 | 已落地（批3b） |
| 几何四量（l_pool/b_pool/v_pool/n_aerator） | 提示/拒收双门 | constraint_kb `geometry_guard` 8 条（1.5.0） | `apply_constraints` 勾选过滤 | 已落地（批3b） |
| 枚举可行带 | 存量 6 条+1.6.0 扩 5 条（AAO/CASS 双侧带） | constraint_kb `enumeration_filter` | `apply_constraints` 勾选过滤 | 已追认（存量 Ruling 2026-08-31；扩 5 条 Ruling 2026-10-01） |
| 水质浓度（六指标） | 负浓度/非有限=数学不变量；行业上限带 | 契约面=`contracts/quality.py`（构造拒绝）；上限带=constraint_kb `input_band`（inlet.quality_upper.* 6 条——1A1 批 1.7.0 录入） | 契约在册；kb 上限带待执法面接线（1A2——同 Kz 行口径） | 契约面已定义；上限带已录入起草态待追认（§1a1 清单——手册原册页级复核归追认批） |

> 新增量的归属判断规则：数学不变量（符号/有限性/量纲）一律契约面；
> 行业带（上下限/常用档）一律数据面（本库或 manifest range）——两不
> 混载（契约带=硬编译、数据带=可追认可演进）。

## 起草清单（1.7.0 input_band 七条——AI 起草待追认）

> 起草表全文（八键逐字+数值起草依据+挂账注记）=
> `.workflow/1a1-20261003/draft-table.md`（仓外批档——呈用户追认的
> 唯一材料）；本节为库内索引面。追认后升 1.7.1 回写标记（RATIFY-CP1
> 先例形态）。

| key | expression | severity | 数值权威 |
|---|---|---|---|
| `inlet.kz_band` | `kz >= 1.3 and kz <= 2.7` | WARN | GB 50014-2021 §3.1 总变化系数表端点（大流量厂下限 1.3/小流量端上限 2.7）——追认单直录起草，手册原册页级复核归追认批 |
| `inlet.quality_upper.cod` | `CODCR <= 1000.0` | WARN | 手册第 5 册设计水质节城镇污水浓度分档高档上沿——同上 |
| `inlet.quality_upper.bod5` | `BOD5 <= 400.0` | WARN | 同上 |
| `inlet.quality_upper.ss` | `SS <= 400.0` | WARN | 同上 |
| `inlet.quality_upper.nh3n` | `NH3N <= 50.0` | WARN | 同上 |
| `inlet.quality_upper.tn` | `TN <= 60.0` | WARN | 同上 |
| `inlet.quality_upper.tp` | `TP <= 10.0` | WARN | 同上 |

- 挂账：①流量相关 Kz 精确内插表不录（设计计算辅助）；②手册原册页级
  复核与逐条定级（severity 细化）归追认批/1A6 批；③执法面（进水输入
  校验接线）归 1A2 校验骨架批。
