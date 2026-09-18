# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: RUNNING
- automation_id: automation-9d2ab6a4-8aa2-4f96-9a44-fa9b23577f85
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T01:31:13+08:00
- heartbeat_utc: 2026-09-18T17:33:10Z
- claim: hubfire-B2-5-20260919T0132-b25f5
- no_progress_count: 0
- checked_total: 20
- checked_done: 8
- last_handover: 2026-09-18
- claimed_by: hubfire-B2-5 执行者会话
- claimed_at: 2026-09-19T01:33:10+08:00
- next_batch: B2-5（实装·第二步：formulas 机制件拆子包——定案 §4.6 步②+勘误后三段聚合入口口径：白名单三态+四探针（dump=flows+manning+discover_units 三段叠加插入序）；行数预算 spec≤150/store≤150/apply≤200/__init__≤40；开工先跑私有名前置探针+改造前 dump 留档会话区；structure-graph §1a 再生成 diff 非空=红停批）

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
    E:\class\智水蓝图\waterprint，相对路径以此为基）。用户指令（2026-09-18
    调度员转达）：B2-3 的 R-B2-3-1（D1 释义）用户已追认、R-B2-3-2（D2）用户
    已知悉——收口时两项 Rulings 销案并在批次日志登记用户裁决回执」
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
- [x] B2-3｜主控终裁（负面清单/规格冲突留用户）——D1 释义与 D2 知悉列 Rulings 呈报（定案=docs/design/2026-09-18_registry-split-design.md）
- [x] B2-4｜实装·第一步：assumptions 数值 YAML 化（golden 三案哈希零变硬闸）
- [ ] B2-5｜实装·第二步：formulas 机制件拆子包（条目留 manifest 原位；注册表 dump 序与集双一致硬闸——D1-B 定案）
- [ ] B2-6｜实装·第三步：量纲步·验证型零动作（out_dims 对账门禁确认性验收——D2-A 定案）

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

### batch B2-2 补记 — 2026-09-18 22:50（CI 守望定性+挂账登记）
- CI 守望：ae5efa4 run 35355924457 红=代号门禁 2 处（本会话卫生事故，9ebc7e1 已修）
  ；9ebc7e1 run 35356746052 **全绿**（10 job 含架构门禁 9s）——绿证随批呈报。
- 连带发现（挂账·主控级小批）：红 run 的锁面草稿诊断步（ci.yml `if: failure()`
  才跑）暴露 draft_lock_manifest.py 扫描根不含 agent/tests——19 键假报「删除」
  （实存 296/296、哈希变 0、check_readonly 真门禁全绿）；修复=补扫描根（该件非
  三信任根，AI 可改），下次任意批搭车，不单开批。
- 会话终态：B2-1+B2-2 两批完成（勾选 4→6/20），READY，claim 归位，CI 绿。

### batch B2-3 — 2026-09-18 23:04（hub 火执行者会话：批 2 三段通道第 3 段·主控终裁，完成）
- 交付：终裁书+定案设计入仓 docs/design/2026-09-18_registry-split-design.md（D1~D6 全裁+审核
  W12/N6 逐条处置表+设计书 8 遗留项处置+修正版三步实施蓝图——B2-4/5/6 实装唯一依据）；
  《裁决书》方案三追加「批 2 终裁定案」最小指针块（防双源）；设计书 v1 自会话区升格入仓
  （零代号零指称，check_model_names 门禁实证过）。
- 终裁要点：D1=意图读法（机制件拆子包+条目留 manifest 原位；字面读法违 manifest 唯一真源+
  单元包互不 import 两铁律，否决）；D2=步③降验证型零动作步（条件句「若为逐公式输出量纲表」
  前提实证不成立）；D3=不引入独立 data_version——ReproTriple 必填键集实测确含 data_version 域，
  B 案由假设否决升格永久否决（W6 闭卷），过期语义补写=数值变更随 engine_version 联动+独立
  版本化另立批（W5 闭卷）；D4=四件 21 键+design_map 伴生注入尾挂 1 键（W7/W8 闭卷）；D5=急切+
  单元口径统一 32 包（N1/N4 闭卷）；D6=维持序（N5 闭卷）。
- 终裁前独立复核（定案附录 D 全实测）：①429=32 manifest 416+L3 两件（manning 9+losses 4）13
  精确闭合，「30 manifest」勘正 32；②formulas.py 487 行唯一 FormulaSpec=规格头文档串（机制件
  定性坐实）；③22 键七域实测，design_map 键=伴生注入（「geo 11」勘正 10）；④聚合入口实证=
  flows+discover_units（仅 import registry/app 得 0~4 条——dump 探针入口缺陷强于审核 W2 表述，
  探针定稿改聚合入口+插入序 dump）；⑤_REGISTRY 全仓外部引用零（私有名前提成立）；⑥golden
  基线=仓内快照内嵌 serialize_bytes/sha256 期望值（W11 就势简化闭卷）。
- Rulings 待用户（终报呈送，不阻塞实施）：R-B2-3-1=D1 释义追认（裁决③「按线分片」字面对象
  不存在，实取意图读法）；R-B2-3-2=D2 知悉（三步=两实装+一确认）。
- 账本：ruling 行 1 笔（manual-b23-final-ruling——D1~D6+复核要点+定案指针）。
- 三查：run_gates 15 绿（含 check_model_names——新入仓件实证过）+gen_status --check 零漂移
  （2072B）+health-scan RED=0/WARN×3（历史欠账回显：2026-09-13 设计链同源行/15 行缺 usage/
  1 行 in=0——非本批引入）。
- 勾选 6→7/20；next_batch=B2-4（实装第一步，输入=定案 §4.6 步①蓝图）。

### batch B2-3 补记 — 2026-09-18 23:20（CI 守望定性）
- CI 守望：496cd63 run 35360177697 **全绿**（10 job：镜像构建/内核质量×3.12·3.13·3.14/
  依赖审计/服务层×2/架构门禁/前端构建/性能基准）——绿证随批呈报；认领笔 c7c1f99 run
  35358584688 亦绿。
- 连带观察（非故障）：runner 信息性告警 ubuntu-latest 将于 2026-10-19 迁移 Ubuntu 26
  ——届时首跑留意 runner 镜像差异（依赖安装/路径面），暂不挂账。
- 会话终态：B2-3 一批完成（勾选 6→7/20），READY，claim 归位；B2-4=下批（实装第一步，
  输入=定案 §4.6 步①）。

### batch B2-3 补记二 — 2026-09-18 23:4X（用户令即刻复核——勘正一处+全项确认）
- 复核范围：终裁全部事实主张重跑实证+交付件一致性+板面/git/账本终态。
- **勘正一处（定案已修）**：注册表聚合入口原记「flows+discover_units=429」——实测该两段
  =420 条（416 单元+4 losses），manning 的 9 条（NM-F*）无上游 import 链须显式导入，
  三段叠加（flows+manning+discover_units）方=429 全量。初版把构造点算术（416+13）误记为
  两段 dump 实测。**429 总数与 D1/D2 裁决均不受影响**（构造点普查与全量 dump 双向恰合）；
  受影响的只是 B2-5 dump 探针入口组成——定案 §4.4/§4.6 步②探针 2/§4.8/附录 D 已同步
  勘正并留勘正记。教训：实测数字与算术数字必须分径记账，不得互证。
- 全项确认：①429=32 manifest 416+L3 两件 13（manning 9+losses 4）双向闭合，清单外
  FormulaSpec 构造=0；②22 键七域分组复核（safety1/engine4/geo10/network6/伴生注入1，
  design_map 键在末位）；③_REGISTRY 外部引用零成立（8 命中=7 处 formulas.py 自身+1 处
  无关环境变量名，初判 grep 路径分隔符伪影已排除）；④ReproTriple 必填键集含 data_version
  成立；⑤铁律引用精化（AGENTS 单元包铁律段+manifest 真源区 L142-143；原「ADR-007/
  AGENTS §11」锚点含糊）；⑥审核 W12/N6 处置逐条对回审计报告原文=全覆盖无漏项；⑦板面
  READY/claim 归位/7-20 勾选/HEAD 已推；⑧账本 ruling 行在册。
- Rulings 内容不变：R-B2-3-1（D1 释义追认）/R-B2-3-2（D2 知悉）——等用户裁决，B2-4
  按不阻塞原则待火班接续。

### 调度员增补 — 2026-09-18 23:33（用户裁决回执转达：B2-3 两项 Rulings 销案依据）
- 用户在 hub 调度会话下达（2026-09-18 23:31）：**R-B2-3-1（D1 释义）→ 追认；
  R-B2-3-2（D2）→ 知悉**。
- 已随板头执行指令字段追加转达条款（Synapse 门一换源指令同款模式）——B2-4
  收口后的下一班发布即随注入指令收到，该批执行者收口时销案并在批次日志登记
  用户裁决回执。
- 板面其余未动（B2-4 在跑，claim 归执行者；本增补纯尾部追加零竞态）。

### 调度员增补二 — 2026-09-18T23:55:50+08:00（hub 停火：用户令删火，新会话接替换防）
- 用户在 hub 调度会话下达删火令：全局轮转火 automation-bf8fd7d7-fa7b-4194-a850-
  2c702565068e 已 CronDelete（回执 deleted:true，CronList 空集复核）。本条为
  调度员尾部纯追加，claim/状态字段未动（B2-4 在跑）。
- 用户将开新会话接替 hub 调度位，按技能「换防协议」hub 变体重布防：板不重建、
  新火 id 届时锚定回填本板 automation_id 字段行（本行现值仅历史审计指向）。
- 板头执行指令中的用户转达条款（B2-3 两项 Rulings 裁决回执）与备源承载事实
  保持有效，新调度员发布时照板上原文注入即自动携带。

### batch B2-4 — 2026-09-19 00:05（hub 火执行者会话：批 2 实装步①，完成）
- 交付：assumptions 数值 YAML 化——数据包 data/assumptions/ 5 件（manifest+四域 21 键，
  default 加引号串，组内键序照抄改造前）+ registry/assumptions.py 500→**200 行**装载器
  （§4.3 六条全落：白名单/有序装载/恰六键/bool 拒 float 收编+type is float 断言/21+1 伴生
  尾挂装配/只读纪律；W9 双哨兵=批次行+_YAML_DATA_DIR）+file-contracts 6 行（5 数据件行
  +1 更新行——「≤200 行」注记入行使 check_file_budgets 注记一致性机锁预算=设计探针④括注
  的机制化兑现）+status.md 派生重生成（新行「assumptions（未声明）」=D3 无 data_version
  的正确显示口径）。
- 等价性证据：全 22 键 repr 串 sha256 改造前后恒等（332eb54c…094a）；键序探针逐字符一致
  （1|3|1|9|1|6|1 分段闭合）；golden 4 绿；core 773+server 313 绿；门禁 15 绿+gen_status
  零漂移+health-scan RED=0（WARN×3 历史欠账回显）。
- 门一（ops-gate1-k2 备源承载，审包 727 行自包含）：B0/W3/N6 PASS——三 W 批内修复复验：
  F-1 _load_yaml except 增 OSError（条目文件缺失不再裸逃逸）；F-2 constraint_keys 补
  Sequence 守卫（堵映射键静默收编+非可迭代 TypeError 逃逸）；F-3 覆盖值路径 no_str=True
  恢复拒 str（签名契约回归）；负例三项实测全拒。门二（ops-probe 独立重跑）：验证矩阵
  10/10 PASS。审档与三件 YAML 全文存 .workflow/reviews/（F-4 处置）。
- 预算裁剪披露（200 行达成代价，门一 N 级过）：异常消息文本精简（键+病因保留，测试面
  match .+ 不锁文本）/类 docstring 撤并模块头/dunder 单行化（ruff E704 未启用实测过）。
  挂账：F-7 ordered_files 路径形态约束（受控数据场景低险，开放外部输入前补）；F-8 PyYAML
  同名键静默覆盖（票面批注内数据维护风险知悉）。
- 批前收编：设计书聚合入口三段勘误（上批会话遗留未提交笔——manning 段补入，涉 B2-5
  dump 探针口径；独立复测 flows=4/+discover_units=420/+manning=429 一致后单独 commit）。
- Rulings 销案（调度员增补转达用户裁决 2026-09-18 23:31）：**R-B2-3-1（D1 释义）→用户
  追认；R-B2-3-2（D2 知悉）→用户已知悉**。本批无新增 Rulings。
- 账本：gate1（含 findings 字段——B2-1 教训兑现）/probe/impl 三行。
- 勾选 7→8/20；next_batch=B2-5（实装步②，输入=定案 §4.6 步②）。

### batch B2-4 增补一 — 2026-09-19 01:00（CI 红事故+R1 复审+装载器解析器修复）
- 事故：收口笔 997ef7e CI run 35367488476——server 3.13/3.14 双 job pytest 退出码 4
  （bash -e 吞 cat 日志、~6s 即死=conftest 导入炸）；core 三版本/其余 job 全绿。
- 根因：server venv 对 waterprint-core 是**非 editable site-packages 拷贝**（uv path
  依赖默认 wheel 形态）——装载器 `__file__` 仓内回溯在拷贝面失效（data/assumptions
  不可达）；本地 server 313 绿系**陈旧 500 行副本假绿**（改源不落 venv）。deploy 容器
  同构受影响（WORKDIR /app+data 拷贝 /app/data）。
- 修复：解析器=源树回溯优先+CWD 上溯兜底+残缺包 fail-fast（目录在而 manifest 缺=
  带路径拒绝）；异常类前移（负例实测抓出 raise 路径 NameError 潜伏缺陷）。三路径
  负例+正例全验（残缺/未找到/正常）；CI 形态复现=server venv reinstall 后 313 绿+
  `__file__`=site-packages/`_YAML_DATA_DIR`=仓库根归属核验。行数保持 200（注记机锁），
  等价 sha256 恒等，core 773+门禁 15+gen_status 零漂移+health-scan RED=0 复验。
- 门一 R1（同岗复签）：B0/W2/N3 PASS——F-2 残缺包静默跳过批内修复；F-1 CWD 无界
  上溯+零包身份校验=受控三态不触发，file-contracts 追认句+挂账（开放部署面扩容前
  补身份校验或上溯限深）；F-3 撤装载器内 type-is-float 断言——**主控追认**（W10
  载体=探针 3；同义反复断言 -O 即剥），设计书 §4.3-3 该句勘误挂账下批搭车。
- 三段式复盘档：.workflow/probes/b2-4/ci-incident-retrospective.md（机制化三条：
  探针矩阵补 server venv 重装+import 归属条目；审包路径类假设须附实测；ci.yml
  pytest 步吞日志形态挂账下批）。
- 账本：gate1-R1 行（findings 齐）+incident 行。

### batch B2-4 增补二 — 2026-09-19 01:10（CI 守望定性：绿）
- 修复笔 1acbefd run 35372021848 **全绿**（10 job：架构门禁/服务层×2[3.13·3.14]/
  内核×3[3.12·3.13·3.14]/镜像构建/依赖审计/前端构建/性能基准）——绿证随批呈报；
  事故闭环（红 run 35367488476→根因→修复→复签→绿）。
- 会话终态：B2-4 一批完成（勾选 7→8/20），READY+claim 归位；B2-5=下批（实装步②
  formulas 机制件拆子包，输入=定案 §4.6 步②+勘误后三段聚合入口口径）。

### 调度员增补三 — 2026-09-19T01:19:16+08:00（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——增补二删火令对象 automation-bf8fd7d7-… 确认已亡，
  无双火风险，零清场动作。
- 深度设计门（换防重走）：过——`.zcode/org-ledger.jsonl` 活跃（末笔=B2-4 CI
  事故复盘行 @09-19 01:02）、《裁决书》占位符 grep 零命中、执行清单机检 8 勾+12
  开=20 与板头计数一致。
- 板面处置：status READY/claim 归「-」/no_progress 0 均为换防期望态零复位；字段
  对照当前技能模板零缺失；本条尾部纯追加；板头 automation_id 字段行已锚定替换为
  新火 id（历史日志旧 id 存量不动）。
- 新全局火=automation-9d2ab6a4-8aa2-4f96-9a44-fa9b23577f85（新 hub 调度会话创建，
  全局唯一 */10 轮转，服务本板+Synapse 板）；本板 last_dispatch=09-18T23:19:54 晚于
  姊妹板 22:56:11——首班有效火先轮 Synapse 板，本板次班承接（next_batch=B2-5
  不变）。
- B2-3 两项 Rulings 已由 B2-4 执行者销案（批次日志在案）；板头执行指令转达条款
  留存原文不改，发布时照原文携带；备源承载事实继续有效。
