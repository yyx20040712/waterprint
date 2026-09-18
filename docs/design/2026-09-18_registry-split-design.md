# 批 2「registry 分性质改造」终裁书与定案设计（2026-09-18）

> 性质：架构级三段通道第 3 段（主控终裁）产物——设计书 v1（第 1 段拟定）
> 与对抗审核报告 v1（第 2 段，B=0/W=12/N=6/VERDICT=PASS）合并裁决后的
> **定案**。实装批 B2-4/B2-5/B2-6 以本件为准。
> 上游指针：`docs/design/2026-09-18_complexity-governance-ruling.md`
> 方案三（用户裁决③「registry 走分性质方案」）。
> 过程件（任务书/设计书 v1 原稿/审核指令包/审出件）=仓外档案区
> `waterprint-archive/b2-registry-design-2026-09/`（不入仓）。
> 事实底座：终裁前对设计书全部关键主张做了独立复核（实测记录见附录 D），
> 两处数字口径勘正、一处探针入口缺陷新发现，均已并入定案。

## 1. 终裁记录（D1~D6）

### D1 公式分片对象 —— 裁定：候选 B（意图读法：机制件拆子包，条目留 manifest 原位）

**事实**（附录 D 复核坐实）：`registry/formulas.py` 487 行为纯机制件（唯
一 `FormulaSpec(` 字样在第 11 行规格头文档串，非实登记）；实登记条目
429 处=32 个单元 manifest（416 处）+2 个 L3 件（elevation/losses.py 4 处
+network/manning.py 9 处）。裁决书方案三步②「formulas.py → 按线分片」
的**字面对象不存在**。

**裁定理由**：候选 A（429 条目抽到按线分片文件）与两条既有铁律正面
冲突——「manifest=单元声明式真源」（AGENTS 单元包铁律段+manifest
真源区：`units_lib/**/manifest.py` 默认值=带出处的声明式真源；ADR-007
声明式映射先例）与「单元包互不 import」（AGENTS 工艺单元包互不 import
+import-linter independence 契约）；且条目搬迁必然扰动
import 序→注册序→golden 风险敞口放大。候选 B 达成裁决③的真实意图
（formulas.py 487/500 腾槽、公式留 Python、扩容槽位成型——新单元=加
manifest 条目，本就按线分布），行为零变成本最低。**A 否决**。

**呈报标注**：本裁定涉裁决③「按线分片」字面释义（字面读法不可执行，
实取意图读法）——列 Rulings 呈用户追认（§5 R-B2-3-1），不阻塞实施
（唯一可执行读法+每步独立 revert 可逆）。

### D2 第 3 步处置 —— 裁定：候选 A（撤销字面动作，降为验证型零动作步）

**事实**（附录 D 复核坐实）：`dimension_specs.py` 为结果字段量纲数据件
（FieldSpec 五元组：field_id/dim/unit/i18n_key/category，258 行），非逐
公式输出量纲平行表；GR-42 条文明定「量纲真源单归
FormulaSpec.output_dim（manifest out_dims.dim 是消费投影+对账断言件，
非第二真源）」——步③前提（裁决书原文自带条件句「**若**为逐公式输出
量纲表」）不成立，条件句走假分支=对裁决书的忠实执行而非方向变更。

**裁定理由**：候选 B（dimension_specs 按批次组分片+装载器）解决不存在的
问题（258 行无槽位压力、GR-42 已满足）且引入装载序新变量；候选 C（塞入
无关治理）超票面污染行为零变承诺。**B/C 否决**。步③定案为零文件改动的
确认性验收步（跑既有 out_dims 对账门禁），见 §4.6 步③。

**呈报标注**：三步变两实装步+一验证步——列 Rulings 呈报知悉（§5
R-B2-3-2），不阻塞实施。

### D3 版本面 —— 裁定：候选 A（不引入独立 data_version；B 永久否决，依据升格为实证）

**实证**（附录 D）：`contracts/result_schema.py` ReproTriple
（design_hash/engine_version/data_version）为结果对账必填键集——序列化
面**确含** data_version 域；`contracts/run_env.py` 定稿口径
「data_version=系数+单价聚合」（ARCH1 D4）。引入独立 assumptions
data_version=三元组成员语义变更+序列化面漂移双违反——设计书 v1 中
D3-B 的否决前提由「假设」升格为「实测事实」，**B 永久否决**（双重依据：
版本面语义 P4 约束+序列化实证，审核 W6 的「否决依据不完整」就此闭卷）。

**过期语义补写**（审核 W5 处置）：现状 assumptions 数值=引擎行为常数，
其变更随 engine_version 升版联动（YAML 化不改变此语义——数值等价搬家
零升版）；data_version 覆盖面维持「系数+单价」不变。后续若需独立版本化
assumptions 数据，**单独立批**并明示「旧结果一次性过期」，禁止搭车本批。

### D4 YAML 分件粒度 —— 裁定：候选 A（按真实键域分件；键数与归属勘正）

**勘正**（附录 D 逐键实测）：22 键=七域——safety 1、loop 3、
solution.grid 1、elevation 9、geometry 1、network 6、solution.design_map 1。
其中 solution.design_map.max_points **不在数值数据面**——它由
`assumptions_design_map.py` 伴生件类注入（防环机制，装配序尾挂，本批
不动）。故四件 YAML 外置 **21 键**+伴生注入 1 键=22：

| 文件 | 键数 | 域 |
|---|---|---|
| safety.yaml | 1 | safety.superheight |
| engine.yaml | 4 | loop×3（tolerance/max_iterations/damping）+solution.grid×1 |
| geo.yaml | 10 | elevation×9+geometry×1 |
| network.yaml | 6 | network×6 |

（设计书 v1 表内「geo.yaml(11)」系把 design_map 键误计入——审核 W7/W8
就势闭卷：design_map 键归属=伴生注入不入 YAML；engine.yaml 合并域命名
说明=「求解引擎行为假设（回路迭代+枚举网格）」。）候选 B（硬套四线名）
维持否决：22 键无一属业务线域，映射规则无真源。候选 C（单件）维持降级
退路备案。

### D5 注册时机 —— 裁定：候选 A（急切聚合，现状语义保持）

32 单元量级属「小而受信」端；429 条目现状即 import 期注册且 golden 绿=
急切序已被现有测试面锁定，改惰性=主动打开高危面而无启动收益。
**B（惰性）否决**。单元数口径统一为 **32 包**（设计书 v1「30 manifest/
32 单元」混用就此勘正——附录 D：municipal 13+mine_water 8+sludge 7+
conveyance 4=32，全部含 FormulaSpec 构造；「34 构造点」=32 manifest+2
L3 文件数，成立）。

### D6 步骤顺序 —— 裁定：候选 A（维持 ①②③）

D2-A 后 ③=验证步（零文件动作），序义=「两实装步+一确认步」（审核 N5
就势闭卷：候选语义更新说明即本句）。重排无收益，维持裁决书排程。

## 2. 审核发现处置表（W12 逐条；N6 并入正文勘正）

| # | 发现（摘要） | 处置 |
|---|---|---|
| W1 | 私有名探针覆盖不完备；dump 探针从聚合正门引私有名自相矛盾 | **采纳**。前置探针扩正则（§4.6 步②探针 1：四形态覆盖）；dump 探针拆两版——改造前从 `registry.formulas` 导入、改造后从 `registry.formulas.store` 导入（探针=诊断面允许私有名，导入路径随架构版本各自锁定，对账基准=输出而非路径；生产面私有名零引用前提经附录 D 全仓 grep 实证成立） |
| W2 | dump 用 sorted 只验集不验序；注册序归因不准确 | **采纳并强化**。归因修正（§4.4：注册序=L3 模块导入序+discover_units 扫描序，聚合正门只定机制件加载序不定条目注册序）；探针改**插入序 dump**（dict 保序，弃 sorted）——序与集双一致。终裁复核另发现更强缺陷：单独 import registry/app 仅得 0~4 条，且 **flows+discover_units 也只有 420 条（manning 9 条须显式导入）**——探针必须叠加三段聚合入口（§4.6 步②探针 2 定稿） |
| W3 | file-contracts 漏删旧 formulas.py 登记行 | **采纳**。步②白名单明确「删 formulas.py 旧登记行+增子包四件登记行」（§4.6 步②） |
| W4 | D2-A 须终裁前置防实施批误执行 | **本件即前置**。终裁已下（§1 D2），B2-6 按验证型零动作步执行——闭卷 |
| W5 | D3 过期语义缺失 | **采纳**。§1 D3 过期语义补写段（engine_version 联动+独立版本化单独立批） |
| W6 | D3-B 否决依据不完整（依赖未验假设） | **采纳**。终裁前实测 serialize 必填键集含 data_version（附录 D）——假设转事实，双依据否决——闭卷 |
| W7 | design_map_entries 键归属未列明 | **采纳**。§1 D4 勘正：design_map 键=伴生注入尾挂，不入 YAML；逐键归属=§1 D4 四件表+附录 D.5 全键序实测 |
| W8 | engine.yaml 合并域与「按真实键域」表述不一致 | **采纳**。命名说明定案：「engine=求解引擎行为假设（回路迭代 3+枚举网格 1）」——两子域同属引擎行为面，合并成立 |
| W9 | 步①幂等哨兵违规（ordered_files 键存在性=产出串哨兵） | **采纳**。哨兵修正（§4.7）：双标记均锚**被改代码件自身**（契约头批次行+数据目录常量行），产出面存在性一律不作哨兵 |
| W10 | 类型校验只查 default、bool 可能穿透 | **采纳**。装载器校验序=先 bool 拒后 float() 收编，覆盖 default+tuning_impact 内全部数值（§4.3）；探针 3 同步扩展（§4.6 步①） |
| W11 | 基线快照获取步骤缺失 | **采纳（就势简化）**。基线=仓内 golden 快照（e2e 测试内嵌 serialize_bytes 长度+sha256[:16] 期望值，附录 D 实证）——`pytest core/tests/golden -q` 全绿即哈希零变的机器判定，无需另建基线采集步骤；命令行 dump 仅作诊断输出 |
| W12 | dump 口径「429 含规格头」与「不预设数目」矛盾 | **采纳**。口径统一：改造前基线 dump 实数为准（附录 D 实测=429=416+13，规格头文档串不计入）；实施批探针断言值以改造前 dump 回填，不预设 |
| N1 | D1 表「34 处（30+2+1）」算术不符 | 勘正入 §1 D5：34=32 manifest+2 L3（文件数）；规格头 1 处=文档串非构造点 |
| N2 | 拆后行数预算缺失 | 补入 §4.6 步②：预算 spec≤150/store≤150/apply≤200/`__init__`≤40（合计≤540 对 487 源+新增契约头注记，check_file_budgets 逐件 ≤500 硬闸不变） |
| N3 | manifest 字段「留位」触禁占位符；字段未命名 | 定案：manifest.yaml 键集=`ordered_files`+`schema_version`（即刻实装，初值 1；已知键白名单内，未知键拒不冲突）——无占位符 |
| N4 | 单元数口径 32/30 混用 | 统一 32 包（§1 D5） |
| N5 | D6 候选意义变化未说明 | §1 D6 补句——闭卷 |
| N6 | 步②探针 4 红判据两可 | 判据唯一化（§4.6 步②探针 4）：structure-graph §1a 再生成 `git diff` 非空=红=停批上报，无「列入验证清单处理」分支 |

**审核遗漏项三件处置**：①扩容槽位维护面（新单元=加 manifest 条目+加
YAML 分文件，无需再动 registry 主件——收益陈述即此，量化成本=每新单元
约 2 文件触碰，随 B2-4/5 落地后在 status.md 生效面复核）；②装载器只读
纪律：assumptions 装载器**禁写 data/**（内核只读，与 coefficients 装载
器同纪律）写入 §4.3；③`registry/__init__.py` 列入步②白名单「修改」面
预登记（子包化不改其 import 路径——`from waterprint.registry.formulas
import …` 语句面零变，预期零改动，白名单预登记防意外面遗漏）。

## 3. 设计书 §7 遗留裁决项处置（八条）

1. **输出路径**：定案=本件 `docs/design/2026-09-18_registry-split-design.md`。
2. **D1 取舍**：意图读法（§1 D1）；字面读法连带的 manifest 铁律修订面
   **不启动**（A 否决即无此面）。
3. **D2 处置**：撤销字面动作（§1 D2）。
4. **D3 版本面**：不引入（§1 D3）；serialize_bytes 含 data_version 已实
   证，B 永久否决——遗留验证项闭卷。
5. **manifest 有序列表偏离文件名排序先例**：**批准**（键序锁定优先；
   偏离理由与先例同载 §4.3）。
6. **§2 补充矛盾（排序先例 vs [0] 锁定）**：确认成立，处置=有序列表
   （同 5）。
7. **锁面**：零新增测试文件确认；本定案不要求 schema 守卫测试（装载器
   内建校验+既有 golden 承担）；若未来要求新增，走 [HUMAN-LOCK] 三连锁。
8. **dump 429 口径**：以改造前实际 dump 为准（附录 D 实测 429 供参照，
   探针断言值由实施批改造前 dump 回填）。

## 4. 定案设计（v1 修订版——含全部 W/N 处置）

### 4.1 文件树（改造后）

```
core/waterprint/registry/
  __init__.py            # 聚合正门：21 符号 __all__ 零改（步②白名单预登记，预期零改动）
  assumptions.py         # ≤200 行：类与守卫面+装载器+schema 校验（数据面迁出）
  assumptions_design_map.py  # 64 行不动（伴生注入防环机制保留 Python 面）
  coefficients.py        # 不动（装载器形态先例）
  dimension_specs.py     # 不动（D2-A）
  dimensions.py          # 禁改
  effluent.py            # 不动
  formulas/              # 新子包（替换 formulas.py 机制件）
    __init__.py          # 聚合正门：re-export 全部无下划线公开名（9 名，§4.2）
    spec.py              # FormulaSpec 五字段+构造守卫+InvalidFormulaError
    store.py             # _REGISTRY + register/by_id/norm_ref_of/validate_all
    apply.py             # _apply_scalar/apply 正门 + apply_batch
  formulas_kernel.py     # 禁改
data/assumptions/        # 四件数值 YAML+manifest（21 键，§4.3）
docs/file-contracts.md   # 步①增 5 行、步②删 1 行增 4 行
```

### 4.2 公开面变化

**零**。两种消费形态经子包聚合正门均不断：`from waterprint.registry
import formulas`（命名空间消费）与 `from waterprint.registry.formulas
import FormulaSpec, register`（直名消费）。子包 `__init__` re-export 清单
=改造前 formulas.py 全部无下划线名 **9 个**（InvalidFormulaError/
FormulaSpec/ValidationReport/register/by_id/validate_all/norm_ref_of/
apply/apply_batch——设计书 v1「6 符号」勘正；其中 7 名经 registry/
`__init__` 聚合再导出，norm_ref_of/apply_batch 为直名消费面），实施批
以改造前 `dir()` 无下划线面探针锁定清单后照单 re-export。白名单外新
导出=无；file-contracts.md 登记义务见 §4.6。私有名（_REGISTRY 等）外部
引用=零（附录 D 全仓 grep 实证），生产面零风险。

### 4.3 装载与校验流（assumptions）

1. 读 `data/assumptions/manifest.yaml`（`yaml.safe_load`，
   encoding="utf-8" 显式）：键集白名单={ordered_files, schema_version}，
   未知键拒；`ordered_files`=非空字符串列表（有序——对 coefficients
   文件名排序先例的**批准偏离**：[0]=safety.superheight 键序锁定优先）；
   `schema_version`=int 即刻实装（初值 1，无占位符）。
2. 按 `ordered_files` 列表序逐件装载：safety→engine→geo→network，
   组内键序照抄现代码面（§1 D4 表）。
3. 条目六字段：key/default/dim/source/note/tuning_impact{direction,
   constraint_keys}。数值口径：default 与 tuning_impact 内数值一律 YAML
   加引号字符串；装载后**先 bool 拒后** `float()` 收编并断言
   `type(x) is float`（W10）；科学计数法（1e-10 容差类）同径。未知键拒、
   缺字段拒、重复键拒（复用 AssumptionSet 既有守卫）；校验失败抛
   InvalidAssumptionError（禁裸 except 静默）。
4. 装配 DEFAULT_ASSUMPTIONS：`_items`=装载序 21 键 +
   `*design_map_entries(Assumption, TuningImpact)` 尾挂注入（伴生件
   64 行不动）＝22 键全序锁定；[0] 断言由既有锁定测试承担，装载器内
   不加新断言。
5. **只读纪律**：装载器禁写 `data/**`（内核只读，与 coefficients
   装载器同款）。
6. **版本/过期语义**：见 §1 D3——本批数值等价搬家零升版；后续数值
   变更随 engine_version 联动；独立版本化另立批。

### 4.4 注册流与聚合入口（formulas 子包）

急切语义保持：子包 `__init__` 按 spec→store→apply 显式序 import 并
re-export 公开面。**注册序归因（W2 修正）**：条目注册序由
（a）L3 公式模块导入序（flows 链：EL-F* 在前）与（b）
`units_lib.discover_units()` 扫描序（32 包，实测 AO→…→PQ）决定；
聚合正门只定机制件三件的加载序，**不定条目注册序**——子包化对两者
零触碰。**聚合入口实证（附录 D，三段组成）**：单独 import registry 或 app 仅得
0~4 条；`import waterprint.flows` → 4 条（EL-F*，losses 链）；
`+discover_units()`（32 包）→ 420 条；`+import waterprint.network.manning`
→ **429 条全量**（NM-F* 9 条，manning 模块无上游 import 链主动装载，
须显式导入）。任何注册表 dump 探针必须叠加**全部三段**（§4.6 步②探针 2
定稿口径）——缺 manning 段即采到 420 条残表。

### 4.5 确定性保障

键序=manifest 有序列表+组内照抄序；注册序=L3 模块导入序（flows→losses
链+network.manning 显式链）+discover_units 扫描序（现状冻结，子包化
不改）；序列化面不动（键排序/round(x,10)
既有纪律）；YAML 全件 UTF-8 显式；GR-18 排序装载/排序返回不受扰。

### 4.6 分步实施蓝图（每步独立成批、独立 revert）

#### 步①=B2-4：assumptions 数值 YAML 化

- **白名单三态**：新建=`data/assumptions/{manifest,safety,engine,geo,network}.yaml`；
  修改=`registry/assumptions.py`（500→≤200 行）、`docs/file-contracts.md`
  （+5 行）；禁改=`core/tests/**`、`scripts/run_gates.py` 及 15 门禁、
  `registry/{coefficients,dimensions,formulas,formulas_kernel,dimension_specs,effluent}.py`、
  `assumptions_design_map.py`、`contracts/**`、全部消费面。
- **迁移机械**：按 §1 D4 表分组剪切 21 键数值条目入四件 YAML（default
  数值加引号）；Python 面重写为装载器（§4.3 六条）。
- **验收探针**：
  1. golden 红线：`pytest core/tests/golden -q` 全绿（4 件 e2e 内嵌
     serialize_bytes 长度+sha256[:16] 期望值=仓内快照即基线——W11 口径）；
     红=立即停批上报，禁调 golden 迁就；
  2. 键集+键序探针：`python -c "from waterprint.registry.assumptions
     import DEFAULT_ASSUMPTIONS as D; assert len(D)==22 and
     D[0].key=='safety.superheight'; print('|'.join(a.key for a in D))"`
     输出与改造前同命令逐字符一致（改造前先跑一次留档会话区）；
  3. 类型探针（W10 扩展）：assert 全 22 键 `type(a.default) is float`，
     且 tuning_impact 内数值面同口径校验（装载器单测化探针——命令行
     逐项断言）；
  4. `python scripts/run_gates.py` 15 门禁全绿（check_file_budgets 验证
     assumptions.py≤200）。
- **回退**：git revert 单批（5 数据件一并撤除），重跑探针 1/2 复原确认。

#### 步②=B2-5：formulas 机制件拆子包（D1-B）

- **白名单三态**：新建=`registry/formulas/{__init__,spec,store,apply}.py`；
  修改=删除 `registry/formulas.py`、`docs/file-contracts.md`
  （**删旧 formulas.py 登记行+增子包四件登记行**——W3）、
  `registry/__init__.py`（预登记：import 语句面零变，预期 diff=0，意外
  面遗漏兜底）；禁改=`formulas_kernel.py`、`units_lib/**`、
  `elevation/**`、`network/**`、`solution/**`、`core/tests/**`、15 门禁面。
- **迁移机械**：按主概念切分（一文件一主概念）；行数预算（N2）：
  spec≤150/store≤150/apply≤200/`__init__`≤40；`__init__` 聚合序=
  spec→store→apply，re-export §4.2 九名清单。
- **验收探针**：
  1. 私有名前置探针（W1 扩正则）：
     `grep -rnE "formulas\._REGISTRY|formulas\.eval_checked|from +[^ ]*formulas +import +(_REGISTRY|eval_checked)|import +formulas\._REGISTRY" core/ server/ scripts/ --include="*.py"`
     命中=红（附录 D 实证当前零命中；eval_checked 为防御面正则项）；
  2. 注册表全量 dump（W2 修正版）——**聚合入口三段+插入序**：
     改造前：`python -c "import waterprint.flows; import
     waterprint.network.manning; from waterprint.units_lib import
     discover_units; discover_units(); from
     waterprint.registry.formulas import _REGISTRY as R; import
     hashlib; [print(k, hashlib.sha256(repr((s.expression,
     tuple(sorted(s.symbols)), s.output_dim, s.norm_ref)).encode()).
     hexdigest()[:16]) for k,s in R.items()]"`（dict 插入序，弃 sorted；
     三段导入缺一即残表——附录 D 实测 flows=4/+units=420/+manning=429）
     ——改造后同命令仅末行导入路径改
     `from waterprint.registry.formulas.store import _REGISTRY`；
     两版输出**逐行一致**（序与集双一致；条目数断言=改造前 dump 实数
     回填，附录 D 实测 429）；
  3. golden 4 件+`pytest core/tests -q` 绿+`python scripts/run_gates.py`
     15 绿（check_lint_imports/check_module_graph 验证子包内三件互不
     越层、四注册表无跨表 import）；
  4. structure-graph §1a 复核：既有生成管线再生成节点表 `git diff`
     为空=绿；**非空=红=停批上报**（判据唯一化，N6）。
- **回退**：git revert 单批恢复单文件 formulas.py，重跑探针 2/3 复核。

#### 步③=B2-6：量纲步（D2-A 验证型零动作步）

- **白名单三态**：新建=无；修改=无；禁改=全仓（零文件动作）。
- **验收探针**：`python scripts/run_gates.py` 中
  check_out_dims_consistency 绿+15 门禁全量绿+`pytest core/tests -q` 绿
  ——确认性验收：量纲真源单归 FormulaSpec.output_dim（GR-42）经门禁
  机器判定持续成立。
- **回退**：无动作可回退。

### 4.7 幂等哨兵（W9 修正版——双标记均锚被改代码件）

- 步①：assumptions.py 契约头规格节批次行「批次: b2-s1-assumptions-yaml」
  ＋同件 YAML 数据目录常量行（`_YAML_DATA_DIR`）——两标记同在=已迁移；
  数据件键存在性不作哨兵。
- 步②：`formulas/__init__.py` 契约头规格节批次行
  「批次: b2-s2-formulas-package」＋同件聚合 import 三行（spec/store/
  apply）——两标记同在=已迁移；旧件删除与否由 file-contracts 双向
  校验门禁承担，不混入哨兵。

### 4.8 风险与回退

| 风险 | 落点与处置 |
|---|---|
| 红线：装载序差异→浮点差异→golden 漂移 | 步①探针 1 首位；红=停批上报禁调 golden；每步独立单批 revert 隔离 |
| YAML 隐式类型强转（1.0→int、1e-10 误判） | 字符串口径+bool 先拒+float() 收编+类型断言（§4.3-3）；探针 3 机检 |
| 键序漂移破 [0] 锁定 | manifest 有序列表+组内照抄；探针 2 序级对账 |
| 子包化断私有名 import | 步②探针 1 前置（当前零命中实证） |
| 子包化扰动层契约/节点口径 | import-linter 绿+§1a 再生成 diff 为空（探针 3/4，判据唯一） |
| 注册序扰动 | 三段导入序现状冻结（§4.4）；探针 2 插入序 dump 序集双一致兜底 |
| dump 探针入口踩空（0/4/420 条残表） | 聚合入口定稿=flows+manning+discover_units 三段叠加（§4.4 实测逐级 4/420/429）；探针内断言条目数防残表 |

回退总原则：每步独立单批、git revert 可逆、回退后重跑该步探针复核。

## 5. Rulings 呈报（用户追认项——不阻塞实施，收口终报呈送）

- **R-B2-3-1（D1 释义）**：裁决③「公式留 Python 但按线分片」的字面对象
  经实证不存在（429 条目本就按 32 单元 manifest 分布=比线更细的按线
  分布；formulas.py 本体=机制件）。终裁取意图读法：机制件拆子包+条目
  原位；字面读法因违 manifest 唯一真源+单元包互不 import 两铁律否决。
  请追认释义（或指示重议）。
- **R-B2-3-2（D2 知悉）**：裁决书方案三步③自带条件句前提不成立
  （dimension_specs.py=结果字段量纲件，GR-42 已满足），步③降为验证型
  零动作步——三步=两实装步+一确认步。请知悉。

## 附录 D：终裁前独立复核记录（2026-09-18 实测，core venv Python 3.14）

1. `wc -l registry/{formulas,assumptions,dimension_specs,assumptions_design_map}.py`
   → 487/500/258/64（行数底座与设计书一致）。
2. `grep -c "FormulaSpec(" registry/formulas.py` → 1，位于第 11 行规格头
   文档串（R-1 机制件定性坐实）。
3. `grep -rln "FormulaSpec(" units_lib/` → 32 文件，**全部为 manifest.py**
   （municipal 13+mine_water 8+sludge 7+conveyance 4）；构造计数 416。
4. L3 两件：manning.py 9+losses.py 4=13；416+13=429（与设计书 429 精确
   一致）。装载链差异：losses 4 条经 flows 链自动注册；manning 9 条无
   上游 import 链，须显式导入方注册（见 8）。
5. `DEFAULT_ASSUMPTIONS` 实测：22 键、[0]=safety.superheight、七域键序
   （safety 1|loop 3|grid 1|elevation 9|geometry 1|network 6|design_map 1，
   design_map 尾挂）。
6. `contracts/result_schema.py`：ReproTriple 必填键集
   {design_hash, engine_version, data_version}——序列化面确含
   data_version（D3-B 否决实证）；`contracts/run_env.py` 口径
   data_version=系数+单价聚合。
7. `dimension_specs.py` 头注：结果字段五元组数据件（B3 R3 拆分自
   dimensions.py）；GR-42 条文（engineering-conventions.md §GR-42）：
   量纲真源单归 FormulaSpec.output_dim——D2 前提不成立坐实。
8. 注册表填充实测：仅 `import waterprint.registry.formulas` → 0 条；
   `import waterprint.app` → 4 条（EL-F1~F4）；`import waterprint.flows`
   → 4 条；`+discover_units()`（32 包）→ **420 条**；
   `+import waterprint.network.manning` → **429 条全量**。全量聚合口径
   =三段叠加。**勘正记**（2026-09-18 收口后复核）：初版 §4.4/本条误记
   flows+discover_units=429，实测=420（manning 9 条不在该两段装载面）；
   429 总数本身不变（构造点算术 416+13 与三段全量 dump 恰一致），勘正
   的是探针聚合入口组成——已同步 §4.4/§4.6 步②探针 2/§4.8。
9. `_REGISTRY` 全仓引用：除 formulas.py 自身外**零命中**（私有名前提
   成立）；formulas.py 无 `__all__`，无下划线公开名 9 个；
   `registry/__init__.py` 自 formulas 聚合 7 名。
10. golden 基线机制：4 件 e2e（municipal/municipal_loop/municipal_
    recycle/mine_water）内嵌 `serialize_bytes` 长度+`serialize_sha256_head`
    断言，期望值随快照入仓——pytest golden 绿=哈希零变机器判定。
