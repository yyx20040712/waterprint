# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: READY
- automation_id: automation-bf8fd7d7-fa7b-4194-a850-2c702565068e
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-18T22:01:29+08:00
- heartbeat_utc: 2026-09-18T14:28:33Z
- claim: -
- no_progress_count: 0
- checked_total: 20
- checked_done: 6
- last_handover: 2026-09-18
- claimed_by: -
- claimed_at: -
- next_batch: B2-3（主控终裁——输入=设计书v1（.workflow/plans/registry-split-design-v1.md）+审核报告v1（.workflow/briefs/b2-2-auditor-output.md，B0/W12/N6/PASS）+仓外镜像 waterprint-archive/b2-registry-design-2026-09/；D1/D2 前提出入涉用户裁决方向实质→呈用户；W 级发现并入终裁处置）

## protocol（角色自识别 + 最小兜底协议）

- **手动会话按板领批=当前唯一路径**（本项目未部署自动化接力；未来若立火式
  接力=用户裁决位，届时本段扩调度员/执行者双角色协议）：
  开工首步 Skill 加载 `ai-dev-org`（组织主干）→ `org-config resolve` →
  读本板+《裁决书》→ 按「执行清单」领下一批 → 按 AGENTS.md 管道执行
  （架构级批走三段通道：社区调研→拟定→对抗审核→主控终裁；实现批双门；
  文档批轻量双审）→ **收口四步=勾选框更新（含板头计数/next_batch/
  last_handover 同步刷新）+批次日志追加（勿改写）+收口即推送+守望
  CI 至绿**（三轮裁决④常态化）。
- 领批纪律：领批即改板（claimed_by/claimed_at 回填）即推送——领批状态对
  板外可见；收口时 claim 字段归「-」。他席读板见 claimed_by≠- 即避让。
- 停止事由：破坏性/安全敏感/计划破碎到每条路都是猜 → status: HOLD 后呈报用户。
- **hub 火式接力（2026-09-18 21:56 用户显式 /batch-relay 布防——首条「手动路径=
  当前唯一路径」自此由本段接替，手动路径降为火不可用时备径；本段即建板时预留的
  扩展位兑现）**：
  - 收到 hub 火 prompt 的会话=**调度员**（薄调度，不自跑批）：轮转规则=在 READY ∧
    last_dispatch 距今 ≥30min（发布静默窗）的成员板中挑 last_dispatch 最老一块
    （`-`=从未发布视作最老；并列取火 prompt 清单序），每回合至多开一批 → UI 开批
    （侧边栏展开 → AXPress「新建任务」→「选择项目」勾选本工作区 → Escape 收菜单 →
    真实点击 textfield 建立焦点 → app 级 strategy=event 键盘写入下方执行指令 →
    回读确认文本落框且发送按钮激活 → 点发送）→ 发送成功后原子更新本板
    last_dispatch（ISO8601 本地时间）。RUNNING 且心跳 <30min → 退出；≥30min →
    先核对 git 进度再接管。UI 选择器漂移时降级为会话内直跑，批次日志记欠账。
  - 被注入执行指令的新任务会话=**执行者**：开工首步 Skill 加载 ai-dev-org（组织
    主干）→ `org-config resolve` → 读板 → 原子 claim（写 RUNNING+claim/claimed_by
    /claimed_at+心跳后回读确认，保留 last_dispatch）→ 按「执行清单」领批至
    fire_budget_min → 收口四步照手动路径条款（勾选框+板头计数/next_batch/
    last_handover 同步刷新+批次日志追加+收口即推送+守望 CI 至绿）；无进展计数
    （勾选数未增 +1，连续 3 → HOLD+终报）；清单全勾（`grep -c '^- \[ \]'` 计 0）
    → DONE+终报（含 Rulings 全清单）；否则 → READY（保留 last_dispatch）。
  - **hub 守卫（shared_fire 板）**：DONE/HOLD/无进展 3 连只置状态+终报，**禁删火**
    ——删火权归 hub 调度员（须全部成员板终态才收线）。
  - **执行指令**（调度员注入新任务用，原文）：「（引用技能 batch-relay）基于
    E:\class\智水蓝图\waterprint\docs\handoff\relay.md 交接文档继续开发——开工
    首步先加载技能 ai-dev-org，再按接力火协议认领并执行本批（工作区根
    E:\class\智水蓝图\waterprint，相对路径以此为基）」
  - 禁止创建任何新自动化（成员板禁自布第二条火——hub 全局一条火红线）。
- 模型路由事实：门一主源周额度达上限（2026-09-18 用户告知）——门一/拟定者
  一律备源承载直至用户另行通知；逐字指令在组织账本 ruling 行。

## 执行路由（ai-dev-org 项目——批内引擎）

- 会话内岗优先 ops-* 绑定子代理（主承载）；外部派发器=健康探针+后备
  （ORG-SEG v2）；外部派发一律 Node 24（AGENTS §0.1）。
- 收口前 `run_gates` 全绿 + `gen_status.py --check` 零漂移 + health-scan RED=0
  （三者并行不互并）。
- 手写计数禁令（ADR-023 D3）与审档归档登记纪律（reviews-archive.json）全批适用。
- 测试锁面：tests/** 改动走 [HUMAN-LOCK] 四根全量重锁。
- 未规划裁决项：用户级（负面清单/新依赖/制度修订/防线变更/视觉决策）→挂起
  呈报+批次日志记 Rulings；主控级→回炉三分法自处。

## 执行清单（波次=接力顺序；`- [ ]` 勾选即完成）

### 第一波·治理底盘（已完成——详见批次日志 batch 1~3）

- [x] 批 0｜宪法 ORG-SEG v2 适配+失效文件清理（1700376+4de4405）
- [x] 批 1｜sunset 登记表+status 生成源+README 瘦身+漂移勘误（34128a9+8b69253）
- [x] CI 修复批｜审档归档指针+ADR-023（5ee40a4+8d60672+8ea43dd）
- [x] 批 2 第 0 步｜社区实践调研（回填《裁决书》调研清单节）

### 第二波·批 2 registry 分性质改造（架构级三段通道）

- [x] B2-1｜拟定者任务书起草+派发（备源承载）→设计书（候选≥2+权衡）
- [x] B2-2｜对抗审核（审核者岗——异构挑刺不改写）
- [ ] B2-3｜主控终裁（负面清单/规格冲突留用户）
- [ ] B2-4｜实装·第一步：assumptions 数值 YAML 化（golden 三案哈希零变硬闸）
- [ ] B2-5｜实装·第二步：formulas 按线分片（注册表 dump 前后一致硬闸）
- [ ] B2-6｜实装·第三步：量纲声明随片（out_dims 对账门禁绿）

### 第三波·批 3 同层晋升（复制收敛——《裁决书》方案二）

- [ ] B3-a｜server 七份 `_latest_calc_result` 复制→services/_shared/（准入五条）
- [ ] B3-b｜webapp SSE 生命周期双实现+域色双源→shared 收敛
- [ ] B3-c｜core B4 双胞胎+异常表两份→§1c 同层边（架构级三段通道）

### 第四波·业务线（《裁决书》方案五排序）

- [ ] B4-1｜操作链集中 debug 观测面（复用 calc-diag+事件流聚合）
- [ ] B4-2a｜碳核算·前置一：能耗药耗计算面（**计算逻辑呈用户审查**）
- [ ] B4-2b｜碳核算·前置二：运行成本面（opex）
- [ ] B4-2c｜碳核算本体（先详细调研再立项——三轮裁决④）
- [ ] B4-3｜联合枚举（ADR-005 解冻须用户裁决）
- [ ] B4-4｜AI 集成深化
- [ ] B4-5｜矿井水段二（norms 追认前置）+软著（用户亲查计算核心优先）

### 挂账池（不入波次，触发时呈报）

> 单源=《裁决书》「沿册挂账」与各方案挂账节——本池仅指针不复制（防双源
> 漂移，门一审 W2 处置）；明细以裁决书为准：纵断真实站距/ODA E2E/软著
> 签章页/UF 开放条目/sunset 观察项（触发条件与复核节奏见 sunset 表）。

## 批次日志（追加，勿改写）

### batch 3 增补二 — 2026-09-18 21:56（hub 布防：用户显式 /batch-relay，挂全局轮转火）
- 深度设计门（ai-dev-org 路线）：过——`.zcode/org-ledger.jsonl` 活跃（21:43
  交接面升级批门一 PASS B0W2N4）、《裁决书》20.5KB 占位符零命中（grep TBD|TODO|
  稍后实现|适当处理|implement later）、执行清单机检 4/20 勾与板头计数一致。
- 板面补齐（只增行不改既有行语义）：+automation_id（待 hub 火回填）+
  shared_fire: true +poll_interval_min/fire_budget_min/last_dispatch/heartbeat_utc/
  claim/no_progress_count（火协议字段对齐当前技能模板）；fire_budget_min=120
  （架构级三段通道批重，对齐姊妹板 Synapse_remake）；claim 与既有 claimed_by/
  claimed_at 同义互映，收口时两者同步归「-」。
- protocol 扩 hub 调度员/执行者双角色段（建板时预留扩展位兑现）+hub 守卫句
  （收口禁删火——删火权归 hub 调度员）。
- hub 火=全局唯一 */10 轮转火（hub 调度会话创建，服务本板+Synapse_remake 板）；
  本板 last_dispatch=`-`（从未发布，轮转视作最老）——首班有效火大概率先开本板
  B2-1（拟定者任务书起草+派发，备源承载）。
- 模型路由事实（门一/拟定者备源承载）继续有效，随执行者开工自账本 ruling 行
  对齐。

### batch 3 增补 — 2026-09-18（门一审 R1 处置+CI 抖动重跑）
- 门一审（备源承载）PASS B0/W2/N4——两 W 批内消化：W1=claim 字段落地
  （板头 +claimed_by/claimed_at+领批即改板即推条款）；W2=挂账池单源化
  （改指针，明细归裁决书）。N 级吸收：next_batch 锚条目 ID（B2-1）；
  裁决书补三轮裁决块+恢复条件句+user_think.png 行闭卷（门一 N3 不确定项
  复核坐实为真缺口后补——三轮裁决此前只入账本未回填方案文档即升格）。
- CI 35350914070 首跑 failure=基础设施抖动（runner 拉 pnpm tarball
  ECONNRESET——本批零 webapp 触碰），--failed 重跑，绿证随收口呈报。

### batch 3 — 2026-09-18（主控会话：CI 修复批+ADR-023+交接面升格，完成）
- 交付：审档归档指针（reviews-archive.json+check_templates 归档分支+对账纪律）
  +ADR-023 决策记录+ADR regex 放宽+status 重生成（ADR 22→23）+补笔 W1 行实落。
  commits 5ee40a4/8d60672/8ea43dd 已推送，CI 双绿（35349702953/35349744970）。
- 门审：轻量双审（备源承载）PASS B0/W2/N4——两 W 批内消化（吞错 WARN+对账
  纪律行；W1 首次落地失败由补笔勘正，教训入 commit message：补丁类操作必须
  grep 验证落地后再 commit）。
- 事故与根因：CI 红=T5 批移审档未同步门禁（两日无 CI 运行潜伏，推送首跑暴露）
  ——修法=三轮裁决①方案 A 档案清单指针。
- 交接面升格：本板建立（格式参考姊妹项目常驻状态板——机器门控+追加制+
  入仓可达），《裁决书》入仓 docs/design/（岗位词中性化，模型代号门禁零命中
  实证）；仓外一次性交接文档内容并入本日志后停更。
- Rulings 待用户：无新增。下批=B2-1（拟定者派发，备源承载）。

### batch 2 — 2026-09-18（主控会话：sunset 机制+status 生成源，完成）
- 交付：docs/governance-sunset.md（S1/S2/S3 三模板+软退役+>50 行盘点红线+零
  门禁脚本）+scripts/gen_status.py（纯标准库全文件派生+--check 字节比对）
  +docs/status.md 首版+CI status 零漂移步骤+README 178 行状态段砍四行（编年史
  174 行迁归档区）+testing/index/user-manual 手写计数句改指针。commits
  34128a9/8b69253。
- 门审：轻量双审（备源承载——主源两连认证失败换源，任务书未放宽）R0 FAIL
  （B1=README 旗舰段自留「32 单元」手写数违「不手写数字」宣言）→R1 真修
  （count_units 指标新增+手写数删除+ADR glob 收紧+退役记录分批+price_data_version
  通配）复签 PASS。
- 生成源首版即暴露两真值：unit_prices 版本字段实名变体、UF 表 9 条状态表述
  不规则。CI status 步骤首跑绿（run 35348257364 server job）。
- 搭车：user_think.png 删除（用户裁决）；碳核算前置探针完成（电耗空白/药耗
  部分/运行成本缺位——路线修正三段，回填《裁决书》方案五）。

### batch 1 — 2026-09-18（主控会话：宪法适配+失效文件清理，完成）
- 交付：ORG-SEG v2（绑定子承载/回炉 ≤5 轮 R≤3/账本指针/承载变更护栏——预算
  582/600）+§0.0 健康检查+§0.1 Node 24 守卫+词汇映射+2 行；清理=M0.5 占位骨架
  五件+plan-structure-wiring.md 删除+mkdocs 悬空行+幽灵引用改真源+.gitignore 根
  锚定；磁盘面 .workflow 615MB→13MB+12 日志删除。commits 1700376/4de4405。
- 门审：轻量双审 R0 FAIL（B1=gitignore `projects/` 未锚定全层级吞目录）→R1
  真修（根锚定+docs 面引用零命中复核+护栏回归）复签 PASS。
- 战役起点：四岗探索调研（core/server/webapp/docs）+五方案设计+用户五裁决。

### batch 0 — 2026-09-18（建板前史：交接补录）
- 用户问询「交接文档是否更新」发现断点未记遗漏——仓外一次性交接文档补建
  （内容已并入本日志 batch 1~3），随后按用户指示升格为本常驻板。教训：
  交接面必须在每批收口路径上（板协议收口四步自此承载）。

### batch B2-1 — 2026-09-18 22:35（hub 火执行者会话：批 2 三段通道第 1 段，完成）
- 交付：拟定者任务书（.workflow/briefs/b2-1-drafter-brief.md——七段+四附录自包含
  零仓库接触，含基线数字与两处「草图前提 vs 现实」出入）→备源派发一次成功
  （第二配额备源承载/Node 24.21.0，runId=20260918141243-lvht0ygd，in=6042/out=9705，
  325s 零换源）→设计书 v1（.workflow/plans/registry-split-design-v1.md，未入仓——
  终裁定案后随 B2-3 升格）。机检：8 章/6 决策组 D1~D6/15 候选行/占位 0/污染 0
  （零模型代号与 AI 指称）/自检行对账。
- 设计书要点：推荐组合=公式机制件拆子包（条目留 manifest 原位）+第 3 步降验证型
  零动作步+assumptions 不引入独立 data_version+按真实键域四件 YAML+急切聚合注册
  +维持三步序；每步白名单三态/迁移机械（幂等哨兵=改动点标记）/验收探针/回退齐备。
- 关键发现三条：①公式条目（429 处）本就按线分布在 30 单元 manifest+2 子系统件，
  formulas.py 本体=机制件——草图「按线分片」字面对象不存在（D1 两案呈报）；
  ②dimension_specs.py=结果字段量纲件非公式量纲表，GR-42 已满足（D2 条件句不成立）；
  ③拟定者新增：coefficients 文件名排序装载先例与 DEFAULT_ASSUMPTIONS[0] 锁定冲突
  →manifest 有序文件列表处置（留终裁）。
- 事故与修正：主控任务书报告契约漏 audit_surface 岗 FINDINGS 机读尾栏→health-scan
  RED×1→三步修正（审出件补代渲染尾栏带出处披露+账本缺陷行补 findings 字段+主控
  披露行 manual-findings-backfill），复扫 RED=0；教训入 B2-2 起任务书模板补尾栏
  条款。health-scan WARN×3 回显（历史欠账：2026-09-13 设计链同源行/15 行 ok 缺
  usage/1 行 in=0——非本批引入）。
- 门禁：run_gates 15 绿+gen_status --check 零漂移（2072B）+health-scan RED=0。
- Rulings 待用户：无新增（D1~D6 取舍留 B2-3 终裁汇总；若涉方向实质变更届时升格
  用户裁决）。会话预算内续跑 B2-2（claim 保持，心跳刷新）。

### batch B2-2 — 2026-09-18 22:40（hub 火执行者会话：批 2 三段通道第 2 段，完成）
- 交付：对抗审核派发一次成功（auditor-readonly/按量审计源，runId=
  20260918142418-t5679jxq，in=12603/out=31676，137s 零换源；与拟定者承载（第二配额备源）
  异构成立）→审核报告 v1：**B=0 W=12 N=6 VERDICT=PASS**——FINDINGS 尾栏由派发器
  自动解析入账本 findings 字段（B2-1 事故教训批内兑现，零人工修正）。
- 审核要点（真问题清单，终裁须逐条处置）：①注册序只验集不验序（sorted 探针盲区
  +注册序实际由 30 manifest import 序决定，归因修正）②步①幂等哨兵违规（ordered_files
  键存在性=产出串哨兵）③golden 基线快照获取步骤缺失（探针不可执行）④私有名探针
  自相矛盾（探针 2 从正门 import _REGISTRY vs 假设私有名零引用）⑤file-contracts
  双向校验漏删旧 formulas.py 行⑥D3 过期语义缺失（假设数值变更→旧结果过期联动）
  ⑦design_map_entries 键归属未列明（YAML/注入来源与顺序）⑧D2 撤销第 3 步须终裁
  前置防实施批误执行；另 4W+6N（数字口径/行数预算/装载器只读纪律等）。
- 归档：四件套（任务书/设计书/审核指令包/审出件）落仓外
  waterprint-archive/b2-registry-design-2026-09/（08 §6 审档归宿）+本机 .workflow/
  双镜像；盘点件两份（b2-1-drafter/b2-2-auditor）偏差补记齐。
- 门禁：本批零仓内代码面改动（板面外）；三查随会话终收口复跑呈报。
- Rulings 待用户：无新增（D1/D2 升格判断留 B2-3 终裁汇总呈报）。
- 会话终收口：本会话 fire 预算内完成 B2-1+B2-2 两批（勾选 4→6/20），claim 归位
  READY，last_dispatch 保留；B2-3 主控终裁=下批（输入路径已锚 next_batch 行）。
- 卫生事故与修正：本会话两条批次日志误带外部模型代号 3 处（08 §6 产出面纪律）
  ——check_model_names 门禁拦截后新笔中性化（已随 ae5eea4 推送的 B2-1 条一并
  本笔修正，不重写历史）；同犯 commit message 面（ae5eea4 信息带代号）——已推送
  不重写，记教训：**板面/日志/commit 三面一律先过代号门禁再落笔**。
