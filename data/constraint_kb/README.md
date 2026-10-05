# constraint_kb —— 约束知识库

> **状态：2.1.0（全量 155 条九键已追认——param_band 113 条〔param.<field>.
> positive 单元参数正性域带族——31 单元 _PARAMS_POSITIVE 机扫单源投影，
> 1A4 批起草 109+P10 批补录 4（收录面缺角三单元——Ruling 2026-10-05
> 随批追认）〕+mass_balance 1 条〔sludge.
> primary_load_band 泥量量级互校带——已追认（Ruling 2026-10-05 P10 批，
> 含宽放 0.5 专家背书消化+ratio 末位勘正）〕+前 41 条：1A1 七条
> 数值+1A6 第九键 enforcement
> 逐条定级**已追认（用户裁决 2026-10-04 R2 全量追认，1.8.1 回写标记
> ——含 effluent 四行取严格档裁量一并追认；1A3 批兑现 entry 级标记
> 回写：constraints.json 全库 17 处「AI 起草待追认」回写已追认——
> 挂账清偿②闭口）**〔§1a6 清单——.workflow/
> 1a6-20261003/draft-table.md 起草表=呈用户追认的唯一材料；与 1A1
> 七条数值合并呈报〕；裁决记录=.workflow/adjudication-batch-20261004.md
> 裁决记录节。定级分布：flag 137+block 18——P1 裁决选项 3「kb 逐条
> severity 声明式定级」落地（1A4 批 +param_band 109+P10 批补录 4 全 flag——仪表灯），
> 两维正交见 schema 节；1.7.0 叠加
> input_band 7 条〔§1a1 清单——.workflow/1a1-20261003/draft-table.md
> 起草表〕：Kz 总变化系数静态包络带+进水六指标浓度上限带，追认单直录
> 形态——存量 29 条中 28 条+1.6.0 扩 5 条已追认：18 条=Ruling
> 2026-08-31、spacing_check 2 条=Ruling 2026-09-03；boundary_check 1 条=SPC2 批
> 2026-09-05 工程惯例起草待专家确认；geometry_guard 8 条=批3b 2026-09-26
> b3a-research.md §二 B 组+§七追认单直录——D 级 AI 推导值经用户「全部
> 追认」生效；**enumeration_filter 新增 5 条双侧带=margin-kb-20261001 批
> 2026-10-01 起草→已追认定稿 1.6.1（Ruling 2026-10-01——§32 四裁量
> 全数生效，含 ns_act 语义迁移 R1 成立/缺氧 HRT 子带 R2 维持）**〔数值=
> factors.yaml 已追认键同值投影，C3 门禁恒等〕**）；
> 批复记录=.workflow/ledger.md 两日 Ruling 条目+
> pending-domain-expert.md §22/§24 销账注+backend-calc-complete/
> b3a-research.md §七。
> 未追认未来项（2.1.0 勘正——余干化全干化档一项独留）：干化全干化档
> 另立待起草追认；mass_balance 1 条与 param_band 113 条（109 存量+P10
> 批补录 4）已随 Ruling 2026-10-05 P10 批全量追认（标记回写 RATIFY-CP1
> 先例形态+宽放 0.5 专家背书消化——1A3/1A4 批 P10 归口附条件全闭口）。消费方=server `GET /api/constraints`（META1 静态目录端点
> 同构）+webapp ConstraintPicker（方案浏览枚举提交面）+`GET /api/site/spacing`
> （L4b 间距校核——spacing_check 阈值数据面；SPC2 起 boundary_check
> severity 数据面同端点）。enforcement（1.8.0）=纯声明元数据**零运行时
> 消费**（core KbConstraint 不装载/apply_constraints 不读/run_full_calc
> 零感知——运行时阻断消费接线与工况分级豁免=显式挂账归 P1 后续批）。

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

## 条目 schema（每条九键齐全——1.8.0 起增第九键 enforcement）

```json
{
  "key": "vxinglvchi.v_filter_band",     // 全库唯一（UI/追认清单引用）
  "kind": "enumeration_filter",          // enumeration_filter | effluent_standard | spacing_check | boundary_check | geometry_guard | input_band | mass_balance | param_band
  "unit_kinds": ["municipal_vxinglvchi"],// 适用单元（effluent 参考面恒 []；spacing_check []=全对通用/两键=限定对；boundary_check 恒 []=全构筑物；geometry_guard 恒 AAO/CASS 双键；input_band/mass_balance 恒 []=kind 直判选条〔非全适用——1A2/1A3 接线红线同款口径，回炉 W4 统一〕；param_band 非空=节点 ID∈unit_kinds 选条〔单元 ID 升序——1A4 批，geometry_guard 非空先例形态〕）
  "label": "…（含字段名）",              // UI 显示（限值出处另列）
  "expression": "v_filter_act >= 7.0 and v_filter_act <= 10.0",  // core DSL
  "source": "GB 50013-2018 §9.5；给水排水设计手册（第 5 册 城镇排水）；起草表待追认",
  "severity": "WARN",
  "enforcement": "flag",                 // flag=仪表灯（违规呈现不阻断）| block=断路器（违规即失败终态）——1.8.0 第九键（P1 选项 3）
  "value_basis": "factor.… @ coefficients 1.1.0——AI 起草待追认"  // 数值溯源
}
```

### 两维关系（severity × enforcement——正交，互不替代）

| 维度 | 回答的问题 | 值域 | 语义 |
|---|---|---|---|
| severity | 呈现多醒目（黄/红标示分层） | ERROR / WARN / INFO（core contracts Severity 冻结面） | 呈现分类元数据——勾选即硬滤全级别（UF-54 定版口径不因第九键改变） |
| enforcement | 违规算不算失败（1.8.0） | flag / block | 执法定性元数据——flag=仪表灯（违规呈现不阻断）/block=断路器（违规即失败终态）；**本批零执法**（纯声明，运行时阻断消费归 P1 后续批） |

- 两维独立取值——155 条在库实际组合矩阵（§1a6 起草清单机器清点+1A3 批
  增 mass_balance 1 条+1A4 批增 param_band 109 条+P10 批补录 4 条）：
  severity=WARN+enforcement=flag 137 条（可行带过滤 11+通用间距 1+
  几何提示门 4+进水合理性带 7+泥量互校带 1+单元参数正性域带 113
  ——提示带仪表灯）；severity=WARN+
  enforcement=block 12 条（出水标准：呈现黄标/违规定性失败）；severity=
  ERROR+enforcement=block 6 条（沼气间距 1+用地红线 1+几何拒收门 4：
  呈现红标/违规定性失败）——组合由条目 kind 语义逐条定级。ERROR+flag
  属声明性合法组合（值域正交两维的自然格）但本库暂无实例。
- 值域守卫：server 装载校验 enforcement 越界=fail-visible 拒（同
  kind/severity 面值域守卫族）；core solution 装载器宽容面忽略本键。

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
  输入面**的合理性带（非单元包、非枚举行字段——unit_kinds 恒空=通用勾选
  判据恒不命中（执法面接线归 1A2——接线红线：禁按 boundary_check 空表=
  全构筑物的 kind 专属语义实现 input_band 空表为全适用）；README 归属
  声明表 Kz/水质两行的数据面载体）。两形态：`inlet.kz_band` 同字段双侧带 `kz >= 1.3 and
  kz <= 2.7`（Kz 静态包络——GB 50014-2021 总变化系数表端点；流量相关
  精确内插表显式挂账不录=设计计算辅助非输入合理性校核）；六指标上限带
  `inlet.quality_upper.<sym>` 单侧 `field <= max`（字段=契约既有进水面
  命名 BOD5/CODCR/SS/NH3N/TN/TP——contracts 冻结面直用，非新建命名）。
  severity 全 WARN（1A6 批定级=enforcement 全 flag——WARN 提示不拒收
  语义承接）；数值=追认单直录——已追认（用户裁决 2026-10-04，1.8.1
  回写）（无
  coefficients 源键——geometry_guard 先例；手册原册页级复核归追认批，
  起草表=§1a1 清单）。**消费面（1.8.1 时点）**：core solution 装载器
  不拒不裁——kind 空表数据面门禁归 kb 数据批 R10 口径；`_maint_face`
  适用判据 `unit_kind in unit_kinds` 对空表恒不选中（其余 kind 的
  观测键面）；枚举面仅消费调用方显式勾选；**input_band 七条已由 1A2
  批接线消费**（2026-10-04——plant 级进水面 kind 直判选条
  `app_validation`，unit_kinds 不参与〔接线红线〕；违规产警告码
  不阻断=enforcement flag 语义）。
- mass_balance（1A3 批 1.9.0 增 1 条——plant 级质量规模互校面）：跨节点
  **质量规模一致性校核**（「进出泥量失衡」诊断面——route 1A3 锚）：对子
  =sludge_hebing 参数注入模式声明的 `ds_primary`（初沉股干泥 kg/d）vs
  全厂进水 SS 负荷（进水声明 SS mg/L×q_avg_daily m³/d 换算 kg/d）——
  **仅此一对**（ds_bio/ds_chem 不入互校：高溶解性 BOD5 废水场景 ds_bio
  可合法远超 SS 负荷，无守恒上界必误伤）；unit_kinds 恒空=**选条判据
  kind 直判**（接线红线同款：禁按空表=全适用实现——执法面=core
  app_validation mass_balance 分支〔1A3 批接线〕）；表达式落
  `primary_ss_ratio` 派生比值列双侧带 `primary_ss_ratio >= 0.2 and
  primary_ss_ratio <= 1.0`（**DSL 右值不支持字段算术**——字段×字段算式
  不可解析，起草算术式的最小面落地形态；比值列由消费面注入
  =ds_primary÷全厂 SS 负荷〔mg/L·m³/d→kg/d 换算因子经 pint 单源——
  contracts.quantity R2 禁手写换算系数，core/server 源码零数值字面量〕；
  阈值 0.2/1.0=预裁决带原文）；severity=WARN/enforcement=flag（仪表灯
  ——block 断路器归 P1 后续批挂账）；跳检语义=缺任一面或零基准不警
  （①无 municipal_input 声明节点〔矿井线〕②进水缺 SS 或 q_avg_daily
  〔或非数值〕③无 ds_primary 数值键〔入流直值模式=D2 双模另一态，
  泥量系上游计算派生非手输声明〕④零基准 ss_load≤0——比值无定义=
  量级判断失效面归跳检族语义〔回炉 B1；SS=0 进水荒谬声明归未来
  input_band 下带扩展挂账，q_avg_daily≤0 拒收面 flows/params_guard
  在册〕）。**本族表达式字段仅准引用 {ds_primary, primary_ss_ratio}**
  ——消费面字段门为泛化 DSL 门，族语义边界以此注记为准（代码面收窄
  归族扩张批——回炉 W2）。多泥量声明节点图形态仅校插入序首个
  （_inlet_values 同款口径）——多 hebing 图逐节点互校归后续批挂账
  （回炉 W1 登记）。「输入合理性带归属声明」表是否增 mass_balance 行
  归后续追认批裁定（表语义=零消费族归置 vs 全 kind 需裁决——本批不
  扩面，回炉 N6 登记）。数值=追认单直录起草（无 coefficients 源键
  ——geometry_guard/input_band 先例形态；上界 1.0=GB 50014-2021 §6.5
  去除率 η<1 守恒包络/下界 0.2=η 下端 0.4×上游格栅/沉砂 SS 削减系数
  宽放 0.5（专家背书=Ruling 2026-10-05 P10 批）——34760 案例实测削减系数 0.746）。**已追认（Ruling 2026-10-05 P10 批）**。
- param_band（1A4 批 2.0.0 增 109 条+P10 批 2.1.0 补录 4 条=113——单元
  参数正性域带族，已追认 Ruling 2026-10-05）：四要点——
  ①**收录面=_PARAMS_POSITIVE 机扫单源投影**：31 单元正性守卫参数面全量
  （200 参数次/113 唯一键——逐字段一条、同字段跨单元聚合；实扫单源=
  .workflow/1a4-20261004/scan_params_positive.py+P10 批补录件
  .workflow/p10-20261005/scan_params_positive_p10.py〔cugeshan/xigeshan
  常量化+bashi b_throat——1A4 d1-N1 缺角闭合〕；含 machine_type 枚举
  参数/z_ground 标高类——kb 为 FZ-4 计算期守卫的报告面镜像，域语义
  一致性优先于逐键域强度甄别）；expression 单子句单侧正性 `<field> > 0`
  （NaN>0=False→越带→警告——声明期 NaN 检出=FZ-4 计算期 InvalidUnitConfig
  守卫的前置报告面；数值域零新造）。②**单侧正性域声明载体=T3 口径成文**：
  manifest range 只收双侧闭区间（GR-06 闭区间口径+FZ-3「无上界真值不
  声明」）——kb param_band 收单侧正性域，两载体互补不双源（manifest
  range 面=手册表出处带域起草表，本族=代码面守卫镜像，收录面不相涉）。
  ③**unit_kinds 非空=节点 ID 选条判据**（geometry_guard 非空先例形态
  ——kb 字段名义为 unit_kinds、实配值=单元 ID〔节点 ID=unit_id 全仓约定，
  server services/calculation.py L160 直证〕；与 input_band/mass_balance
  恒空 kind 直判族的接线红线分立——两判据族并行不混载）。④**缺项跳检=
  声明面稀疏语义**：用户只声明改过的参数，default 面域由 manifest 起草表
  保证不校（params_guard face④ 在册执法面）；非数值（str/bool）不入表
  同态跳检。severity 全 WARN/enforcement 全 flag（仪表灯——block 断路器
  归 P1 后续批挂账）；source=族级出处+归类（几何/时间/流量负荷/数量/步长
  /水质/标高/其余物理量——正性域=物理必然非阈值条文，不逐键造精确条文；
  与 1A3 带域出处的差异在 value_basis 注明）。**消费面（2.0.0 时点）**：
  core app_validation param_band 分支（1A4 批接线——选条=节点 ID∈
  unit_kinds，越带产警告码不阻断=flag 语义；遍历独立于进水声明面——
  矿井线整族可达〔回炉 W1 拆门勘正〕）；`_maint_face` 字段准入
  （expression_fields⊆offline_dims）对 params 声明键自然不选中——maint
  标注面零新键（**D1 勘正注记〔回炉 W2——门一双审证伪陈述修正**〕：
  上句论断对与离线 dims 同名的参数键不成立——aao 离线 dims 含 n/h2
  →param.n/h2.positive 经字段准入**合法选中**，golden 案 param_band
  注入的 maint 标注面增量恰 4 键全 PASS（kb.param.n/h2.positive=1.0+
  any_fail=0.0+fixgeom.min=0.0），零值变零删减=纯标注增量非行为破坏；
  详见批档 impl-report 实现裁量 D1+app_validation 头注等义记载）；
  枚举面仅消费显式勾选（param_band 不在勾选清单）。
  **已追认（Ruling 2026-10-05 P10 批——109 存量标记回写+4 补录键随批追认）**。
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
| Kz（总变化系数） | 行业上下限 | constraint_kb `input_band`（inlet.kz_band——1A1 批 1.7.0 录入，静态包络带；流量相关精确内插表挂账不录） | 已接线（1A2 批 2026-10-04——plant 级进水面 kind 直判选条，unit_kinds 不参与；违规=警告码不阻断〔flag 语义〕） | 已录入；已追认（用户裁决 2026-10-04，1.8.1 回写——§1a1 清单） |
| q_avg_daily（厂界流量） | A-1~A-3：≤0 或 >60 m³/s 拒收；(0,10 m³/d) 与 >100 万 m³/d 提示不阻塞 | `flows/params_guard.py` builtin 常量（builtin kind 无 manifest——锚=b3a-research §二 A 组+§七追认 2026-09-26） | server 422 整批拒+core ParamVerdict | 已落地（批3b） |
| 单元参数（30 包 94 条） | 手册表出处 range（闭区间 GR-06） | units_lib manifest `params.range` | `params_guard` face④ 闭区间执法 | 已落地（批3b） |
| 几何四量（l_pool/b_pool/v_pool/n_aerator） | 提示/拒收双门 | constraint_kb `geometry_guard` 8 条（1.5.0） | `apply_constraints` 勾选过滤 | 已落地（批3b） |
| 枚举可行带 | 存量 6 条+1.6.0 扩 5 条（AAO/CASS 双侧带） | constraint_kb `enumeration_filter` | `apply_constraints` 勾选过滤 | 已追认（存量 Ruling 2026-08-31；扩 5 条 Ruling 2026-10-01） |
| 水质浓度（六指标） | 负浓度/非有限=数学不变量；行业上限带 | 契约面=`contracts/quality.py`（构造拒绝）；上限带=constraint_kb `input_band`（inlet.quality_upper.* 6 条——1A1 批 1.7.0 录入） | 契约在册；kb 上限带已接线（1A2 批 2026-10-04——同 Kz 行口径） | 契约面已定义；上限带已录入，已追认（用户裁决 2026-10-04，1.8.1 回写——§1a1 清单） |

> 新增量的归属判断规则：数学不变量（符号/有限性/量纲）一律契约面；
> 行业带（上下限/常用档）一律数据面（本库或 manifest range）——两不
> 混载（契约带=硬编译、数据带=可追认可演进）。

## 起草清单（1.7.0 input_band 七条——已追认）

> 起草表全文（七条·每条八键逐字+数值起草依据+挂账注记）=
> `.workflow/1a1-20261003/draft-table.md`（仓外批档——呈用户追认的
> 唯一材料）；本节为库内索引面。已追认（用户裁决 2026-10-04，
> 1.8.1 回写——RATIFY-CP1 先例形态；1.7.0 起草态叠加由 1.8.0 承载
> 不单独定稿，追认随 1.8.1 统一回写，无 1.7.1 槽位）。

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
  复核归追认批（severity 逐条定级已由 1A6 批 enforcement 起草承载）；
  ③执法面（进水输入校验接线）已由 1A2 批落地（2026-10-04：plant 级
  kind 直判选条+警告码面——block 断路器接线仍挂账 P1 后续批）。

## 定级起草清单（1.8.0 enforcement 41 条——已追认）

> 起草表全文（41 条逐条 key/enforcement/一句理由引 kind 语义或 P1 件
> 层级+挂账清单）=`.workflow/1a6-20261003/draft-table.md`（仓外批档
> ——呈用户追认的唯一材料）；本节为库内索引面。与 1A1 七条数值合并
> 呈报，已追认（用户裁决 2026-10-04，1.8.1 回写——RATIFY-CP1 先例
> 形态；含 effluent 四行取严格档裁量一并追认）。

| kind（条数） | enforcement | 定级依据（一句话——逐条理由见起草表） |
|---|---|---|
| enumeration_filter（11） | 全 flag | 可行带过滤——带外行已可勾选过滤，P1 件 §六选项 3「filter 带类=仪表灯」原文 |
| effluent_standard（12） | 全 block | 出流超标=工艺交付失败——P1 件 §七「计算器+门禁」哲学+出水标准数据性地位；工况分级豁免显式挂账 |
| spacing_check（2） | WARN 通用=flag/ERROR 沼气间距=block | 与既有 severity 双门语义一一对应（提示门/安全红线） |
| boundary_check（1） | block | 用地红线越界=硬失败（P1 件 §六 red_line 类原型） |
| geometry_guard（8） | hint 4=flag/reject 4=block | 提示门（超工程常用）/拒收门（荒诞域）与 severity 双门一一对应 |
| input_band（7） | 全 flag | WARN 提示不拒收——1A1 起草表语义承接（越上界=疑工业废水/单位错录提示复核） |
| mass_balance（1） | flag | 量级互校仪表灯——失衡提示复核（1A3 批起草：1.0 上界守恒包络/0.2 下界宽放；见下方 1.9.0 起草清单） |

## 起草清单（1.9.0 mass_balance 一条——已追认）

> 1A3 批（UF-55 泥量量级互校）增条；呈用户追认材料=本表+任务书 §3 预裁决
> （.workflow/1a3-20261004/）。已追认（Ruling 2026-10-05 P10 批——标记
> 回写+宽放 0.5 专家背书消化+ratio 末位勘正在档；RATIFY-CP1 先例形态）。

| key | expression | severity | 数值权威 |
|---|---|---|---|
| `sludge.primary_load_band` | `primary_ss_ratio >= 0.2 and primary_ss_ratio <= 1.0` | WARN | GB 50014-2021 §6.5（初沉池 SS 去除率 40%~60%——上界 1.0=η<1 守恒包络）+给水排水设计手册（第 5 册 城镇排水）初沉污泥量计算式（=SS 负荷×去除率——CC-F10 同源口径）——追认单直录起草：下界 0.2=η 下端 0.4×上游格栅/沉砂 SS 削减系数宽放 0.5（仓内佐证：34760 案例初沉入流 SS 186.4242/进水声明 250=削减系数 0.746；golden 三案例 ratio=0.372849 带内零漂移；2 量级失衡验收 ratio≥100 与 ≤0.01 均落带外）——已追认（Ruling 2026-10-05 P10 批） |

- 注记：expression 落 `primary_ss_ratio` 派生比值列（DSL 右值不支持字段
  算术——起草算术式 `ds_primary >= SS * q_avg_daily / 1000 * 0.2 and …`
  的最小面落地形态；换算因子经 pint 单源，代码零数值——收录边界
  mass_balance 段详注）。
- 宽放因子登记（回炉 W2-d1）：下界宽放因子 0.5 系仓内裁量（佐证=34760
  案例削减系数 0.746 的约双倍宽放防误伤），专家背书归 P10 追认批——
  不推翻预裁决（value_basis 已如实披露裁量链）。
- 挂账：block 断路器接线（enforcement 消费）仍挂账 P1 后续批（flag
  仪表灯先行——1A6 定级面 input_band 同款）。

## 起草清单（2.0.0 param_band 109 条+P10 批 2.1.0 补录 4 条——已追认）

> 1A4 批（单元级参数域校验）增条；呈用户追认材料=任务书 §3.1 预裁决
> +扫描矩阵（.workflow/1a4-20261004/scan_output.txt——逐字段×单元全集，
> 189 参数次/109 唯一键）。已追认（Ruling 2026-10-05 P10 批——109 存量
> 标记回写+4 补录键〔h/s/alpha/b_throat——31 单元 200 参数次，批档
> scan_output_p10.txt〕生而已追认；RATIFY-CP1 先例形态）。
> 全量 113 条逐条九键入 constraints.json（族级 source/value_basis 同文，
> 逐条差异面=key/unit_kinds/label〔归类名〕/expression 四键）——库内
> 不重复罗列，抽样高频三键：

| key | expression | unit_kinds（升序） | severity |
|---|---|---|---|
| `param.n.positive` | `n > 0` | 15 单元（conveyance 3+mine_water 5+municipal 7——扫描矩阵单源〔P10 批 +cugeshan/xigeshan〕） | WARN |
| `param.side_disc_step.positive` | `side_disc_step > 0` | 10 单元（扫描矩阵单源） | WARN |
| `param.z_water_inlet.positive` | `z_water_inlet > 0` | 1 单元（mine_water_input） | WARN |

- 注记：enforcement 全 flag（仪表灯——1A6 定级面 input_band/mass_balance
  同款）；出处=族级（GB 50014-2021 相关构筑物节+手册第 5 册——正性域=
  物理必然非阈值条文，逐条 label 括注归类名，不逐键造精确条文）；
  **已追认（Ruling 2026-10-05 P10 批——109 存量标记回写+4 补录键随批追认）**。
- 挂账：block 断路器接线（enforcement 消费）仍挂账 P1 后续批（flag
  仪表灯先行——1A6 定级面同款）。
