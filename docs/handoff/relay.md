# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

> **标准注入词（rev5 口径 2026-09-26——workflow 通道）**：
> - 调度员窗口（迁火/接任用，工作区不限；布火为重活允许载技能，此后每班只读板）：「接任交接：你是 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 的当班 hub 总调度员——读板头+protocol 段（现行 rev）→ 按 batch-relay 技能 references/ops-manual.md 换防协议迁火并回填 automation_id → 提交推送 → 随即按 protocol 段开批通道 rev5（CreateWorkflow saved batch-relay-executor）发布执行者并原子写 last_dispatch_utc+workflow_run_id → 此后每班火只读板调度，禁执行禁重活禁载技能」
> - 执行者窗口（手动兜底发布用；常规发布=执行工作流子代理，无需此窗）：「基于 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 交接文档继续开发——读板（板头字段区+protocol 段+执行路由+执行清单+批次日志末 3 条）按 protocol 段执行者条款认领并执行本批；组织主干优先 Skill 加载 ai-dev-org，无 Skill 工具则直接读工作区根 AGENTS.md 与 .zcode/org-ledger.jsonl 等价替代；板 protocol 段缺失/预检失败才加载技能 batch-relay 兜底。无人值守：不等待人工答疑，用户域阻塞按停止事由 HOLD(stop_matter) 收口。工作区根 E:\class\智水蓝图\waterprint，相对路径以此为基。禁止创建任何新自动化。」

- status: READY <!-- 2026-09-26 增补五十五：批6d 收口 READY（AAO capex 区分度数据面——1 commit c878b8d〔HUMAN-LOCK〕/门一双席 B0 PASS+门二双路径复算/三检全绿）；next=批6e -->
- automation_id: automation-143e250a-5e96-4e6b-9016-7ac16fa7fb21 <!-- 2026-09-26 换防迁火回填（增补五十一）；旧值 automation-cf38af42…（已熄——CronList 空实核，增补五十火情观察证实） -->
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-26T16:26:13Z <!-- 增补五十五收口刷 -->
- claim: - <!-- 批6d 收口释放（executor-b6d-20260926T151400Z，勾选 40→41） -->
- no_progress_count: 0 <!-- 2026-09-25 新排程重置（原 1=B4-5 用户门控非系统性卡死） -->
- checked_total: 52 <!-- 2026-09-26 增补四十九：38+14（第六波全局收尾 批6a~6n——单源工单 wave6-master-plan.md；旧值 38=增补二十五口径） -->
- checked_done: 41 <!-- 2026-09-26 批6d 收口 40→41（增补五十五） -->
- protocol_rev: 6 <!-- 2026-09-26 换防升版 rev5→6（执行指令锚根批=现行：仓根锚定纪律+执行指令行参数化+开批通道标签去 rev 化）；旧值 5 -->
- last_dispatch_utc: 2026-09-26T15:12:43.008Z <!-- 2026-09-26 批6d 首班发布成立（回读=run dwfrun-a8431da0-a14b-42ce-868c-01d20fec3333 running+执行者子代理 executing）；旧值 2026-09-26T14:16:56.911Z（批6c 首班） -->
- workflow_run_id: dwfrun-a8431da0-a14b-42ce-868c-01d20fec3333 <!-- 批6d 首班执行工作流（AAO capex 区分度数据面——field_mapping 三扩行+设备单价万元尺度+AAO 轴分化对拍断言+设备基数退化修复锚） -->
- relay_started_utc: 2026-09-26T12:10:48.865Z <!-- 2026-09-26 rev6 换防时刻（本会话）；旧值 2026-09-26T04:00:36.124Z（rev5 二次换防） -->
- batch_count: 4 <!-- 2026-09-26 批6d 收口 3→4（增补五十五） -->
- max_batches: 60
- max_wall_hours: 90
- hold_reason: - <!-- 2026-09-26 增补四十八清空：批3a 追认已签+CI 已修——⑤b 软著仍为用户域终态项（批3b 后停板待用户不变） -->
- last_handover: 2026-09-26
- claimed_by: executor-b6d-20260926T151400Z <!-- 批6d 收口留档 -->
- claimed_at: 2026-09-26T15:14:00Z <!-- 批6d 认领时戳（收口留档） -->
- next_batch: 批6e 全工况投影端点（calc sensitivity 投影 API+龙卷风幅度轴升级——批2d 欠账①；快照 stale 语义） -->

## protocol（角色自识别+两角色行动细则唯一源——调度员/执行者按此执行；技能文件仅兜底）
- 本板 protocol_rev=6；rev5/4/3/2/1 存量板读法向下兼容（rev0 无此行读旧字段名 last_dispatch，仅警告不阻断），换防时迁移至现行 rev。
- 时间一律 UTC（ISO8601 带 Z 后缀）；「距今 N min」=（当前 UTC−字段值）÷60000 向下取整；解析失败=预检失败。写板一律写 Z 后缀新字段名；旧字段行冻结不删。
- 预检（任何行动前，rev 感知）：字段行完整（rev5/6 全集=rev1 全集+workflow_run_id；rev1-4 旧集；rev0 旧集）/ 时间戳可解析（rev0 旧格式仅警告）/ 数值字段纯非负整数（R10）/ status∈{READY,RUNNING,DONE,HOLD} / 无重复 status 行 / protocol_rev∈{0,1,2,3,4,5,6}——任一失败：输出 `fire: abort (reason=board_precheck_failed:<规则名>)` 后退出，并在批次日志追加欠账行。
- 收到火 prompt 的会话=调度员。**调度员=纯调度（用户裁决 2026-09-25 rev4）**：只读本板板头字段区+本 protocol 段——不加载技能文件、不读批次日志/计划全文/ai-dev-org 等一切开工依赖（全部下传一线执行者自载）；调度所需一切以本段为准，技能 batch-relay 仅布防/换防/事故会话加载（本段缺失/预检失败时才兜底加载）。一切一行退出只用固定枚举三族，禁引用板面原文：`fire: skip (reason=quiet_window|running_fresh|candidate_alive|no_ready_board)`；`fire: terminal (reason=done|hold|board_missing)`；`fire: abort (reason=board_precheck_failed:<规则名>)`。
  - 板不存在 → 单项目：CronDelete(automation_id) 后 `fire: terminal (reason=board_missing)`；shared_fire=true 板缺失=从轮转清单跳过+本轮终报记欠账，不删全局火——删火仅当全部板终态或缺失。
  - DONE/HOLD → 单项目：CronDelete(automation_id) 后 terminal(done|hold)；shared_fire=true 板只终报不删火（删火权归 hub 调度员，须全部板终态）。
  - last_dispatch_utc 距今 < quiet_window_min=30 → `fire: skip (reason=quiet_window)`（READY 未认领/RUNNING 均适用；仅约束调度员，刚被发布的执行者照常认领；值为 `-`=从未发布——窗口视为已过，非解析失败）。
  - RUNNING 且 heartbeat_utc 距今 < heartbeat_stale_min=30 → `fire: skip (reason=running_fresh)`。
  - RUNNING 且心跳距今 ≥ heartbeat_stale_min=30 → 先核执行工作流：GetWorkflowRun(板头 workflow_run_id)——running/pending → `fire: skip (reason=candidate_alive)`（工作流活=执行者活，覆盖批内长同步子任务的心跳盲区）；completed/errored/stopped 或无 run 可查 → 核对实际进度防重复执行再重置 claim → READY（接管后重新发布则更新 last_dispatch_utc 与 workflow_run_id）。
  - READY → 开批四条件：①status=READY ②静默窗已过（last_dispatch_utc 距今 ≥ quiet_window_min=30；值 `-`=从未发布视为已过）③上一批执行工作流已收口（workflow_run_id=`-` 或 GetWorkflowRun 非 running；查询失败退回板面 mtime 与 git 最近提交距今 ≥ physical_quiet_min=5，无 git 仓以板面与 plan 文件 mtime 代之）④熔断未触发（batch_count<max_batches 且距今运行 <max_wall_hours 小时）。④触发 → 置 HOLD(hold_reason=circuit_batches|circuit_wall)+终报首行「熔断裂闸…」；①-③任一不满足 → 让位下一班火。四条件齐 → 走下方开批通道（workflow 通道）。
- 开批通道（workflow 通道，rev5 引入——2026-09-26 用户裁决弃 UI 通道改 dynamic workflow，零前台依赖；rev3 UI 通道及其前台门/回读①-④/死胎处置整段废止，史证见技能 ops-manual「开批通道演进史」）：
  - 步骤 1 发布：CreateWorkflow 运行已存全局工作流 batch-relay-executor（`saved: { name: "batch-relay-executor", args: { board: <本板绝对路径>, mode: "execute" } }`——运行已存工作流无需加载任何技能）。失败（未部署/参数拒/确认不可得）→ 批次日志记欠账行让位下一班；连续 dispatch_fail_max=2 班失败 → 置 HOLD(hold_reason=dispatch_channel)+终报请用户重新部署工作流（恢复走换防）。
  - 步骤 2 回读（发布成立唯一判据=后端事实）：取得 run_id 且 GetWorkflowRun 状态 running/pending → 成立（run_id 即后端事实——本通道无 UI 表象可误读）→ 原子写 last_dispatch_utc+workflow_run_id（status 保持 READY）→ 收线退出。
  - 步骤 3 每回合至多开一批；hub 轮转在合格板中挑 last_dispatch_utc 最老者（并列取 prompt 清单序），成员板缺 shared_fire: true 行 → 跳过该板+日志欠账行。
- 调度员会话卫生：当班调度会话只做调度（读板+至多一次 CreateWorkflow+至多一笔板写）——禁执行批次、禁换防/板面手术/长事故响应等重活，重活另开会话（肥会话每班纯耗上下文：2026-09-26 实证整夜 ~300K token/班空转于 skip 判定）；布火会话变重 → 按换防纪律迁火新薄会话（全局单火不变式保持）。
- 被发布的执行工作流子代理（或被注入执行指令的新任务会话）=执行者：开工首步按执行指令行取组织主干（优先 Skill 加载 ai-dev-org；无 Skill 工具则直接读工作区根 AGENTS.md 与 .zcode/org-ledger.jsonl 等价替代）→ 读板预检（只取板头字段区+执行路由+执行清单+批次日志末 3 条——防上下文膨胀，日志全量仅按需追溯）→ 仓根锚定（rev6：默认 cwd=调度侧工作区≠目标仓根；仓根=板绝对路径去掉尾部 docs/handoff/relay.md——一切文件/命令操作锚定仓根绝对路径：Bash 先 cd 该根或一律绝对路径/git -C，中间产物落仓内，禁止在默认 cwd 运行仓内命令）→ READY 时原子 claim（tmp 写 status:RUNNING+claim token+heartbeat_utc+勾选数快照，保留 last_dispatch_utc 与 workflow_run_id → mv -f 覆盖 → 回读确认，非己让位退出；此后执行者一切板写（心跳/收口/翻回/修复）落笔前同样回读，非己=已被接管停笔让位，遗留只终报呈报）→ 执行 plan 未勾任务至 fire_budget_min=60（板字段可调；每任务始末刷心跳，任务内每隔 heartbeat_refresh_min=15 亦必刷——活执行者心跳永不陈旧到接管阈值）→ 收口按固定次序判定（首中即断）：①`grep -cE '^[[:space:]]*- \[ \]'` 计 0（行首允许缩进，误报方向=晚 DONE 安全）→ DONE+终报（收线删火由下一班调度员按 DONE 状态机行完成——执行者无 CronDelete 工具）②停止事由（不可逆/破坏性、安全敏感、仓外副作用、计划破碎）→ HOLD(stop_matter)+终报 ③熔断（batch_count+1 后 ≥max_batches 或墙钟 ≥max_wall_hours）→ HOLD(circuit_batches|circuit_wall)+终报 ④勾选数未增 → no_progress_count+1，达 no_progress_max=3 → HOLD(no_progress)+终报 ⑤否则 READY。收口必做（同一原子写）：勾选框更新（有 git 提交；无 git 仓记 `commit: n/a (no-git)`）+批次日志追加+heartbeat_utc 刷新+batch_count+1（无条件；唯一例外=翻回 RUNNING 修复的回炉收口不再 +1，③按现值重判④⑤照常，日志记「回炉收口」）+claim → -。置 READY/DONE/HOLD 必须是最后一笔，置位后禁写板/仓；要修先回读（被新 claim 占据则不写，遗留只在终报呈报）→ 原子翻回 RUNNING 修毕重新收口。
- 执行指令（调度员发布工作流 ask 词/手动注入通用，rev6 口径——执行者读板为主径、不预载技能；改本口径=改本源并重新部署已存工作流保持同文，同文机检=check-relay channel 子命令）：「基于 <board 绝对路径> 交接文档继续开发——读板（板头字段区+protocol 段+执行路由+执行清单+批次日志末 3 条）按 protocol 段执行者条款认领并执行本批；组织主干优先 Skill 加载 ai-dev-org，无 Skill 工具则直接读 <工作区根>/AGENTS.md 与 .zcode/org-ledger.jsonl 等价替代；板 protocol 段缺失/预检失败才加载技能 batch-relay 兜底。时间戳一律 Bash 取 UTC（date -u +%Y-%m-%dT%H:%M:%SZ）。无人值守：不等待人工答疑，用户域阻塞按停止事由 HOLD(stop_matter) 收口并终报。<工作区根>=<board 绝对路径> 去掉尾部 docs/handoff/relay.md 所得仓根，相对路径一律以此为基；默认 cwd 是调度侧工作区、多半≠该根——一切文件/命令操作先锚定 <工作区根>（Bash 先 cd 该根或一律绝对路径/git -C，中间产物落仓内），禁止在默认 cwd 下运行任何仓内命令。禁止创建任何新自动化。」
- 停止只许 CronDelete；禁止创建任何新自动化（CronCreate/CronUpdate）。运行已存工作流（CreateWorkflow saved）=开批通道，不属创建自动化。

## 执行路由（ai-dev-org 项目——批内引擎）

- 会话内岗优先 ops-* 绑定子代理（主承载）；外部派发器=健康探针+后备
  （ORG-SEG v2）；外部派发一律 Node 24（AGENTS §0.1）。
- 收口前 `run_gates` 全绿 + `gen_status.py --check` 零漂移 + health-scan RED=0
  （三者并行不互并）。
- 手写计数禁令（ADR-023 D3）与审档归档登记纪律（reviews-archive.json）全批适用。
- 测试锁面：tests/** 改动走 [HUMAN-LOCK] 四根全量重锁。
- **第六波预授权口径（用户 2026-09-26「全部安排上+连续开工」指令——增补四十九记档）**：
  ①批内测试呈批件经门一烤验（或小批主控亲验矩阵）后**随批落地** [HUMAN-LOCK]——commit
  注明「预授权依据=用户 2026-09-26 全局规划指令」（CI 绿连续性前提）；②新数值键按
  AGENTS §14 工程常用范围起草带出处实装+**事后批量追认**（数据策略 v2 非前置口径）；
  ③四闭项按主控推荐案执行+Rulings 呈报（AUD-W10=维持硬滤+注记/池数扩档=不扩〔已裁〕/
  UF-25=中文单语定版/UF-26=重启即丢明示）——终裁权保留，用户翻案=独立勘误批；
  ④批间不停板（连续开工），清单末项 ⑤b 仍按 stop_matter 停板待用户亲查。
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
- [x] B2-5｜实装·第二步：formulas 机制件拆子包（条目留 manifest 原位；注册表 dump 序与集双一致硬闸——D1-B 定案）
- [x] B2-6｜实装·第三步：量纲步·验证型零动作（out_dims 对账门禁确认性验收——D2-A 定案）

### 第三波·批 3 同层晋升（复制收敛——《裁决书》方案二）

- [x] B3-a｜server 七份 `_latest_calc_result` 复制→services/_shared/（准入五条）
- [x] B3-b｜webapp SSE 生命周期双实现+域色双源→shared 收敛
- [x] B3-c｜core B4 双胞胎+异常表两份→§1c 同层边（架构级三段通道）

### 第四波·业务线（《裁决书》方案五排序）

- [x] B4-1｜操作链集中 debug 观测面（复用 calc-diag+事件流聚合）
- [x] B4-2a｜碳核算·前置一：能耗药耗计算面（**计算逻辑呈用户审查——R-B42a-1~4 四项全批**）
- [x] B4-2b｜碳核算·前置二：运行成本面（opex）
- [x] B4-2c｜碳核算本体（先详细调研再立项——三轮裁决④；**R-B42c-1~4 四项全批 2026-09-20**——B 案全口径/2019+AR6/全套口径/锁面笔授权）
- [x] B4-3｜联合枚举（**2026-09-20 收官**——ADR-025 解冻承接+分层 beam+静态预检双轴预算+新正门 /api/solution/joint-enumerate；三段设计链全档=.workflow/b4-3/）
- [x] B4-4｜AI 集成深化（**2026-09-24 收官**——a 段演示版产物 2026-09-20 随用户裁决回退；b 段深化段全量重建=①NL 入口[CLI 单发三话术口径]+②多轮对话[agent chat/ 编排环——迭代 12/降级直译/会话 JSONL]+③前端聊天 pane[Drawer+SSE 任务流]+④方案比选[agent 工具 #22 全链+聊天呈现——solutions 专用 UI 欠账 R-B44b-4]+⑤工具三面[#23 概观/知识第三源/轨道丙叙述草稿]；三段设计链全档=.workflow/b4-4b/）
<!-- B4-5 原行已拆分（2026-09-25 用户裁决①——勘误确认，见第五波 ⑤a/⑤b 与增补二十五勘误记） -->

### 插队战役·e2e-audit 修复（2026-09-25 增补十纳入——用户直排工单位阶高于波次排序，先于 B4-5 开工；
工单源=docs/handoff/e2e-audit-fix-plan-2026-09-24.md §4 批次+§7 开工指引 与 e2e-audit-round2-2026-09-24.md §4 增量——
明细以工单为准，本区只放指针防双源漂移）

- [x] E2E-1｜fix-plan 批1【server-data】P0-A 数据包路径自愈+启动 fail-fast（+round2 批1 扩 R2-P2-1 no-store）
- [x] E2E-2｜fix-plan 批2【webapp-calc】P0-B 只读态提交计算复活（+round2 批2 扩 R2-P1-2 fitView 引导/R2-P1-3 保存语义）
- [x] E2E-3｜fix-plan 批3【chat】P0-C 聊天桥 repo_root+P0-D 输入框锁死
- [x] E2E-4｜round2 §4 新立【server-scene】R2-P0-1 场景 kind 映射 500+R2-P1-1 布局避让+R2-P1-4 进水物理域检（编号撞前篇批3，按独立新批解读——排序/并批主控裁量）
- [x] E2E-5｜fix-plan 批4【hygiene】卫生批（+round2 批4 扩 R2-P2-2 孤立警告/R2-P2-3 枚举 URL 回写）

### 治理小批·用户直排（2026-09-19 对话内裁决——B4-2a 收尾批后、B4-2b 前开工）

- [x] G-1｜同族一致性门禁：aao/cass 同族公式族（需氧量/曝气/污泥/能耗）结构恒等机器断言+显式 delta 清单（如 CASS duty_ratio）——静默分叉变响红（可维护性答疑①，用户裁决入下波工单）
- [x] G-2｜拆件配方回写宪法：ADR-024 D1 的 formulas_*/energy 预算墙拆件规则写入 AGENTS §11——撞墙拆法从即兴变规则（可维护性答疑②，用户裁决入下波工单）

### 第五波·总排程（2026-09-25 用户四裁决——交错序全 12 项；波内序=接力顺序，
自动化连续开工；单批明细以各工单/战役档案为准本区持指针防双源）

- [x] R3｜孤立警告组装+锁面呈批（e2e-fix-round3 批3——B-3；草稿 .workflow/e2e-fix/E2E-5/isolated_warn.draft.md；实现侧 helper 抽取过 PLR0912+core 全量仅预期红+锁定测试期望 diff 走 .workflow 呈批）
- [x] 批2b｜capex 第四真键（backend-calc-complete——evaluate_combo 全厂计算后按 services/cost.py 同款装配 takeoff→build_estimate 总造价进 metrics；registry 增 objective_weight_capex 假设键+四键权重 .25/.30/.20/.25 专家追认；纯几何参数恢复区分度）
- [x] R4｜server 卫生（e2e-fix-round3 批4——C-1 uvicorn 直启校验收敛〔方案1 entrypoint〕/C-2 no-store 全 GET 面中间件/C-3 manifest 内容校验；C-1/C-2 方案呈门一并抄送用户——**2026-09-25 收官**：Docker 实测抓漏 dockerignore 真缺陷+双容器态实证；烤验三轮双审全 PASS+裁决部有条件可收口〔M1/M2/C1/C2 全落实〕）
- [x] 批2d｜方案比选可视化三图+picker 修复（backend-calc-complete 批2d——帕累托前沿/平行坐标/龙卷风 echarts 6.1；**含** webapp constraintPicker 2-kind 锁死 vs kb 实发 4 类修复+真目录形状用例〔批2a 裁决部 C4〕；联合枚举 UI R-B44b-4 并案裁量）
- [x] R5｜门禁绊线+定版脚本（e2e-fix-round3 批5——C-4 check_model_names 两处〔OSError 计数+目录漂移绊线〕+D-1 15 万吨定版脚本沉淀 p150k_final.py+React 重复 key 警告定位顺手〔healthcheck 挂账〕）
- [x] 批3.5｜范围一补全·调研先行（backend-calc-complete——ganhua 燃料因子权威源检索：有源则起草立键标注待追认/无源登记挂账；xiaohua 消化 MCF 分档〔IPCC 2019 Refinement Table 6.3 消化档〕）
- [x] 批5｜低优先堆（backend-calc-complete——NaN 可行口径统一/timeout 诊断维度/severity 执法统一/裁决档勘误两处〔W2:549→548 与 34760.46→34760.70〕/beam.py 拆件结构债/app.py 500 贴墙欠账/main.py 余量观察项）
- [x] ⑤a｜矿井水污泥线新单元（B4-5 拆项——**2026-09-26 勘误收口〔增补四十四〕**：实质=链级复用 hebing→nongsuo→tuoshui 已落图 golden（用户 2026-08-28 追认 D1「非新单元包」+MSLUDGE2；「wp new-unit 新建包」字面与已追认设计冲突不执行，判定链+验证矩阵见增补四十四）；三维模板族缺位=三维战役 P6 参数化族队列指针）
- [x] 批2c｜gwp_ch4 27.0 呈批件制备（backend-calc-complete——factors.yaml 改值 diff+golden 五工况期望值重算草案+锁面工序 README；**制备批不实装不提交**——golden 重录涉 core/tests 锁面须人类随批落地，呈批件齐即收口转用户）
- [x] 批3a｜几何域数值检索起草（backend-calc-complete 批3 前半——**2026-09-26 起草收口〔增补四十六〕**：数值单 15 条+追认单呈用户〔入口流量上界/池长上限/曝气密度/AAO·CASS 尺度告警/池数档〕逐条带出处+证据分级，卷宗 b3a-research.md §七 追认单签字后批3b 开工）
- [x] 批3b｜几何域拒数据包实装（backend-calc-complete 批3 后半——**追认已签 2026-09-26（全部追认——D-2 案乙维持现值+口径注记/B-6 宽带并集）**：constraint_kb 几何条目+入口流量上界+params_guard range 执法面）
- [ ] ⑤b｜软著（B4-5 拆项——用户亲查窗，**用户域终态项**：自动化到此处按 stop_matter 停板待用户；亲查参考=round2 §2 手算对照表 26 项全吻合+15 万吨核对表）

### 第六波·全局收尾（2026-09-26 全局规划上板——增补四十九；单源工单=.workflow/backend-calc-complete/wave6-master-plan.md；用户指令「全部安排上+新会话 batch 技能连续开工」——预授权口径见执行路由新增段）

- [x] 批6a｜gwp_ch4 27.2→27.0 数据勘误实装（批2c 八步工序——**2026-09-26 收官〔增补五十二〕**：4b550e6 八步零偏离〔27.0/1.5.1/golden 五件/快照 3 行/36 根重锁〕+0c31196 B-6/D-8 factors 笔〔增补五十欠账路由：band 4 键 0.3/0.75+note 升格+1.6.0〕——双路径复算+DV 单因回代证明）
- [x] 批6b｜碳范围一+能耗上游补全（批3.5 实装面〔ganhua 21.622+xiaohua MCF 0.8 案 A+三新键已追认〕+AUD-W4 反冲洗三键/磁分离能耗——新数值 §14 起草带出处事后追认）<!-- 2026-09-26 收官〔增补五十三〕：C-F10~F12+XL-F20~F22/KS-F9+确定性勘正 1 commit 87bc7b1〔HUMAN-LOCK〕+门一双席 B0 PASS+门二双路径 fp 级一致 -->
- [x] 批6c｜LCC 折旧面（AUD-W11 后半：opex 折旧/资本摊销口径——三段通道设计先行；推荐 v1=展示维度不进 objective）<!-- 2026-09-26 收官〔增补五十四〕：直线法双键 cost_capex_annualized_yuan_a 展示维度+factor.lcc 两键 30/10 a（D 级待追认）+coefficients 1.8.0——1 commit be23fb3〔HUMAN-LOCK〕+门一三席 PASS+门二双路径 diff=0.0+golden/快照零重录 -->
- [x] 批6d｜AAO capex 区分度数据面（field_mapping 段三扩行+设备单价万元尺度——批2b 欠账①②；AAO 轴分化对拍断言；含批6c 欠账②设备基数退化 E=54 元同批修复锚）<!-- 2026-09-26 收官〔增补五十五〕：万元×10⁴ 折元契约+按组计价扩行+dims n 回显——门一 k1 B0/W3/N4+d1 B0/W5/N6 双 PASS+门二双路径复算 PASS+1 commit c878b8d〔HUMAN-LOCK〕 -->
- [ ] 批6e｜全工况投影端点（calc sensitivity 投影 API+龙卷风幅度轴升级——批2d 欠账①；快照 stale 语义）
- [ ] 批6f｜任务系统补完（chat 失败横幅 error 明细〔任务状态查询面〕+joint failed/cancelled 幽灵文案+UF-26 重启即丢 v1 明示闭项）
- [ ] 批6g｜结构债拆件批（beam.py/app.py/main.py 三顶格件按 ADR-024 配方腾位——双跑 diff=0 行为等价烤验）
- [ ] 批6h｜门禁硬化+部署卫生+杂项闭项（R5 结转观测护栏四项+p150k 首跑留证+ENTRYPOINT 绝对路径+classic builder 实测+AUD-W9 对拍门禁+AUD-W10 维持硬滤注记闭项+UF-25 中文单语定版闭项+HEAD 版本耦合注记）
- [ ] 批6i｜纵断真实站距（README 在册剩余面——三段通道设计先行〔站距源两案呈裁：布置连线长度 vs 手动输入〕+profile 桩号轴实装）
- [ ] 批6j｜DXF 绝对标高+ODA 验证工具（UF-50 通道收口 _REL_DATUM 退役路径+ODA 本地手动冒烟脚本〔不入 CI〕）
- [ ] 批6k｜UF 规格冻结批（UF-06 汇流派生定版+UF-09 温度字段位置+UF-11 Ri 归属勘误+UF-12 图谱缺边+UF-19 缺项下游+UF-24 带归属——六行闭合）
- [ ] 批6l｜UF-46/47 收口（core app 面 load_run_env/design_hash 用例→server 适配器/双胞胎退役——D7 边界经 app 再导出面保持）
- [ ] 批6m｜单元库浏览前端实现（UF-52——设计件 units-browser-design.md 已备，上板=实现批追认成立）
- [ ] 批6n｜UF-53 域色双轴归一（CSS/JS 同值双源单源化+双轴同值机器断言——C1 纪律设计裁量）

> ③ vector 全表面期望外移 JSON 数据件（可维护性答疑③）＝**用户亲改保留项**——AI 批次不自动开工；第三次锁面摩擦事件发生时仅呈报提醒不代做（用户裁决 2026-09-19）。

### 挂账池（不入波次，触发时呈报）

> 单源=《裁决书》「沿册挂账」与各方案挂账节——本池仅指针不复制（防双源
> 漂移，门一审 W2 处置）；明细以裁决书为准：纵断真实站距/ODA E2E/软著
> 签章页/UF 开放条目/sunset 观察项（触发条件与复核节奏见 sunset 表）。

## 批次日志（追加，勿改写；全量历史见 relay-archive-001~004——读板卫生：执行者只取本节末 3 条）

### 增补四十七 — 2026-09-26T06:17:28Z（批3b 收口：HOLD(stop_matter)——待追认批开工前置未满足，清单余 2 项全用户门控停板待用户）

- **claim/commits**：executor-b3b-20260926T061611Z（06:16:11Z 认领，rev5 四班=run dwfrun-fb81b03e 执行者子代理——板头 workflow_run_id 在案，调度员发布注记「待追认批，可否开工由执行者按清单条款判定」）；本收口笔（零代码批——仅板面；组织主干=ai-dev-org v2.1.0 Skill 载入）。
- **判定链（收口判定②停止事由首中即断；①不成立=未勾 grep 计 2≠0：批3b+⑤b）**：批3b 开工前置=批3a 数值单 §七 15 条用户签字（执行清单条款+增补二十五③用户裁决「逐条带出处呈用户签字追认后实装」）——核验四证全否：§七 15 条签字框全 ☐（☑×1 仅签字方式说明行自指）／卷宗 mtime=05:46:40Z 早于批3a 收口 05:48:47Z 零后续编辑／git 末笔 b0c4945（05:49:07Z 批3a 收口笔）后零新提交／docs/norms 2026-09-16 后无新追认档——**未签字实锤不可开工**（越权实装=直接违反用户明示裁决+B 组全 D 级 AI 建议值零追认源，§14 数据策略）。⑤b 软著=清单明示「用户域终态项：自动化到此处按 stop_matter 停板待用户」。清单余 2/38 项全用户门控=增补十八 B4-5 双门控 HOLD(stop_matter) 同款判定。
- **收口三检**（零代码纯判定批免烤验对抗位=增补十八先例；三检照跑）：run_gates 16 门禁全绿（[OK] 全部门禁通过）；gen_status --check 零漂移（2158 字节逐字节一致）；health-scan RED=0／WARN×3 存量回显（可收口）。
- **移交人类（停板待办——重启前置）**：①批3a 追认单签字（.workflow/backend-calc-complete/b3a-research.md §七 15 条逐条可改可否——B 组全 D 级 AI 建议值尤须专家复核；§四冲突呈报必读：CASS 长宽比案甲/乙择一〔主控推荐案乙〕+曝气服务面积双带 0.3~0.75 vs 0.3~0.65 择一）→签字后批3b 开工；②⑤b 软著亲查窗（用户域终态项——亲查参考=round2 §2 手算对照表 26 项+15 万吨核对表）；③存量八笔 [HUMAN-LOCK] 呈批件+批3.5 追认单+批2c golden 重录（增补二十五集中索引不变）。
- **重启**：/batch-relay 换防（板头标准注入词调度员窗口 rev5 口径）；班火见 HOLD 按 protocol 固定枚举 terminal (reason=hold) 终报（shared_fire=true 不删火，删火权归 hub）。
- **收口判定=②HOLD(stop_matter)**：勾选 36/38 未增（no_progress_count 保持 0=②先于④）；batch_count 3→4（无条件）；claim 释放；置 HOLD 最后一笔。

### 增补四十八 — 2026-09-26T07:37:00Z（用户直派主控手术：全部追认+CI 修复批——HOLD 解锁 READY+存量呈批件九笔清账+CI 红根因根治）

- **会话性质**：用户直派主控会话（板 HOLD 中非执行者通道——增补二十五同款手术先例）；用户指令两件：①「全部追认」②「修复CI错误」。盘点件=.workflow/skills-inventory-ratify-cifix-2026-09-26.md。
- **追认登记（用户指令代录——非逐条亲笔，如实记档）**：
  - **批3a 数值单 15 条全 ☑**（b3a-research.md §七 追认记录节）：D-2 CASS 长宽比=**案乙**（维持 2.0~3.0+口径注记——主控推荐案）；B-6 曝气服务面积带=**宽带并集 [0.30, 0.75]**；手册原册复核与 GB 转载件抽核建议保留开放（后续发现出入按 §14 另批勘误不追改本签字）。
  - **批3.5 两项全批**（b35-research.md §五 追认记录节）：xiaohua MCF 分档=**案 A**（污泥线独立核算 0.8 档，废水线 0.03 毯式维持）；ganhua EF=21.622 tCO₂/万Nm³；沼气 CH₄ 体积比=0.60（IPCC 2006 缺省）；气回收率=0.90；CH₄/N₂O 天然气次要面一并立键——实装面并入后续碳核算实现批。
  - **批2c 呈批件 Rulings 三条全批**（gwp_ch4 27.2→27.0 勘误）：①data_version 升 1.5.1（patch 位=纯值勘误）②快照 ambr 豁免锁定清单+git 跟踪随笔提交③镜像桩值 27.0 一致性维护——**八步工序实装待排**（b2c-lock-drafts/ 呈批件四件已批可执行；排程=批3b 后或用户直排，本手术不代行数据勘误重工序）。
  - **批2b Rulings 四件**（增补三十呈报）：①§1c 边节点归一化 ②unit_prices 硬契约 ③四键权重 .25/.30/.20/.25 初值 ④AUD-W11 LCC 折旧面挂账维持——全数追认。
- **CI 红根因与修复（CI 连红 2026-09-24T17:49Z 起）**：①mypy 两错=relax.py RetryOutcome.outcome Any 面批5 拆件遗留+settings.py:306 dict 泛型（c47b476 修复笔：TYPE_CHECKING 导入 JointOutcome 真类型化+dict[str,Any]|None——core 349 文件+server 58 文件 mypy 双绿）；②pytest 15F 预期红=九笔 [HUMAN-LOCK] 呈批件未落地（core 8F+server 7F——本轮九笔全部落地红归零）。
- **九笔锁面笔落地（commit 4e4ce4c/a6f96c9/785673f/f7d140f/60df3ff/a6e2aaf/846e5d2/4fb3027+agent/uv.lock 同步笔）**：E2E-5 孤立警告期望翻转；批2b capex 五文件 diff+12 草稿用例转正；批5 双源口径双 diff+两镜像新件（mirror_rule 门禁转绿）；audit-norms 两新件（**两用例断言按批5 现行语义校正**——原草稿批5 前旧语义 relaxed=True，改 relaxed=False+事由注记，原意=诊断不断链保留）；批2a 裕度 16 用例；F1 ai_config 新件 233 行+端点集 42；E2E-3 聊天桥 repo_root 锚；E2E-1+R4 数据包自愈/C-3 八用例/C-2 五用例（E2E-1 草稿漏 @pytest.mark.anyio 落地补齐）。manifest 323→328 键+status.md 再生成（4fb3027 锁面勘误笔）。
- **验证（三检+双全量）**：core 全量 1554P+2F（=ruff/file_budgets 镜像测试启动时旧态——修复后复跑 8P 绿）；server 全量 **372P 零失败**（7F 预期红全清）；core mypy 349+server mypy 58 双绿；run_gates 16 门禁全绿；gen_status --check 零漂移（2158 字节）；health-scan RED=0/WARN×3 存量回显——**可收口**。
- **板面手术**：status HOLD→READY（hold_reason 清空）；heartbeat 刷新；next_batch/清单批3b 行措辞=追认已签可开工；checked_done 36/38 不变（批3b+⑤b 未完成）；batch_count 4 不变（主控手术非批次）。
- **重启路径**：班火（automation-cf38af42 每 10min）见 READY 按开批四条件核验——last_dispatch_utc=06:11:50Z 距今 >30min 静默窗已过+workflow_run_id 对应 run 已 completed+熔断未触发——下一班应开批通道 rev5 发布批3b 执行者。
- **移交人类**：①⑤b 软著亲查窗（清单末项用户域终态项——批3b 收口后停板待用户）②批2c 八步工序实装排程裁量（呈批件已批可执行——建议批3b 后主控直排或并入下一实现批）。

### 增补四十九 — 2026-09-26T08:15:00Z（全局规划上板：第六波·全局收尾 14 项——用户「全部安排上+新会话 batch 技能连续开工」）

- **会话性质**：用户直派主控手术（接增补四十八——CI 已全绿 10/10 job+流水线解锁后，用户指令做全局规划并全部排程）。
- **盘点源**（四源合一）：板面清单余项+audit-norms AUD-W 处置映射（11 项中 6 项已修：W2/W5/W6/W7/批1 防御三笔/W11 主面）+各批登记欠账（批2b①②③/R4①②③④⑤⑥/批2d①②③/B4-4b chat/R5 结转）+UF 登记册开放 14 行后端相关+README 在册剩余面（纵断真实站距/ODA E2E）。
- **编排**：第六波 14 批依赖序（数值批先行/结构批后置/用户域殿后）：6a 勘误实装→6b 碳范围一+能耗上游→6c LCC→6d AAO capex 数据面→6e 投影端点→6f 任务补完→6g 拆件→6h 卫生闭项→6i 纵断站距（设计先行）→6j 标高+ODA→6k UF 冻结→6l 46/47 收口→6m 单元库浏览→6n 域色归一；单源工单=.workflow/backend-calc-complete/wave6-master-plan.md（每批目标/改动面/验收/风险/依赖）。
- **预授权口径（执行路由新增段）**：①锁面随批落地 [HUMAN-LOCK]（预授权依据记 commit）；②新数值 §14 事后追认制；③四闭项按主控推荐案+Rulings（AUD-W10 维持硬滤/池数不扩〔已裁〕/UF-25 中文单语/UF-26 重启即丢）——终裁权保留；④批间不停板，⑤b 仍停板待亲查。
- **不排批项（外部依赖/用户保留，如实记档）**：手册原册复核+kz 带+D-7 文字化（原册不可得——批3a 留白维持）；vector 期望外移（用户亲改保留 2026-09-19）；audit 存疑专家位（pac/pam+TKN/TN——随 ⑤b 亲查窗）。
- **板面手术**：清单+第六波 14 项；checked_total 38→52（done 36 不变）；执行路由+预授权段；本增补笔。
- **熔断预算**：batch_count 4/60+墙钟 90h（rev5 换防 2026-09-26T04:00Z 起）——14 批估 28~40h 在限内；触发则按 protocol HOLD 收口，恢复=换防重置（用户在场）。
- **开工方式**：用户新会话调用 batch 技能（rev5 开批通道 CreateWorkflow saved batch-relay-executor）或班火自然轮转——next_batch=批3b（第五波）→6a→…→6n→⑤b 依序。

### 增补五十 — 2026-09-26T11:43:25Z（批3b 收口：几何域拒数据包实装完成——READY）

- **claim/commits**：executor-b3b-20260926T092235Z（09:22:35Z 认领——用户直派执行者窗口手动兜底发布；组织主干=ai-dev-org v2.1.0 Skill 载入，主控+实现者/门一 k1·d1/门二 probe·裁决部全管道）。九笔：52837a7（kb 1.5.0 geometry_guard+server kind 面+openapi 级联）/bc7fc8b（D 组出处升格+t_draw range+properties 收编）/a7de2d1+3275e59+d831a6c（三笔 [HUMAN-LOCK] 锁面——预授权①依据=用户 2026-09-26 全局规划指令）/39a702f（params_guard 拆件+face④+builtin 带+warn 字段+魔法数字白名单——B-3b-1/2 案甲主控裁定）/1515d24（server 尾半 422/warn 日志）/1e6a7e9（门一 B1 极性勘正）/6e9a52b（断言补强）。卷宗：b3b-brief/b3b-blockers/b3b-gate1-package/b3b-gate1-round2/probe-b3b-report（.workflow/backend-calc-complete/）。
- **交付四件**：①params_guard 第四面 range 闭区间执法（**30 包 94 条既有声明全量激活**——键分布 conveyance10/mine_water24/municipal44/sludge16=94、包 4+8+12+6=30〔裁决部逐包实勘；执行者回执分项 8/24/49/13 系笔误以本行为准〕）+builtin q_avg_daily 带 A-1~A-3（≤0 或 >60 m³/s 拒收；(0,10 m³/d) 与 >100 万 m³/d 提示 accepted+warn 不阻塞；60.0 恰界=accepted+warn 双态〔两带算术重叠=追认值事实〕；60.0 换算二进制精确断言钉死；kz 无带如实登记）；拆件=flows/params_guard.py 兄弟件（499/500 预算墙 AGENTS §11 停批呈裁定→案甲）再导出签名零变。②constraint_kb 1.5.0 geometry_guard 8 条（l_pool/b_pool/v_pool/n_aerator 四量 WARN/ERROR 双门；expression=`field <= 阈值` 真=门内合规——**门一 B1 勘正**：初版 `>` 真=越门致 feasible 倒置〔勾选保留荒诞行滤掉合规行〕，阈值零变=追认值原样；恰等值闭门语义用例钉死）。③server 消费面（_KINDS/Literal+计数勘误〔旧 20 系 1.4.0 漏更实 21〕+422 整批拒+warn 不阻塞仅日志——E2E-1 fail-fast 软提示面）。④D 组升格（D-1 h2 §7.6.5/§7.6.39 确证/D-2 案乙 ratio_lb 维持 2.0~3.0+包络口径注记/D-3 条号勘正 §7.6.39→§7.6.18-2〔厌氧 HRT 误植〕/D-4 §7.6.12/D-6 §7.6.17-1 全带注记/D-5 t_draw range 1.0~1.5 落地即被 face④ 执法）。
- **追认→实装映射（15 条——裁决部 C2 落档）**：A-1/A-2/A-3 实装（builtin 带）；B-1~B-5 实装（kb 8 条四量双门）；B-6 [0.30,0.75] **挂账→批6a factors 笔落键+供气量法批接线**（无行字段可接——死条目勾选即 InvalidConstraintError 炸枚举，主控裁量不实装）；C-1 n≥2 维持（grid 既有零改动）；C-2 grid 2~6 维持（扩档=产品裁决位）；C-3 单组 >25 万 m³/d 提示**挂账→联合枚举/结果校核批**（跨单元派生量无单一执法面）；D-1/D-3/D-4/D-6 出处升格实装；D-2 案乙实装；D-5 t_draw range 实装+执法；D-7 维持待追认（GB 表 7.6.19 未文字化——零改动）；D-8 方法学=既存锚（manifest FormulaSpec §7.9.6 注记增补前已在）+factors note 升格**挂账→批6a 同笔**；E 组 range 执法面实装（94 条全量+builtin 新增面）。
- **烤验（实现批全对抗位）**：门一 k1 首轮 PASS B0/W5/N11、d1 首轮 **FAIL B1**（几何极性倒置——与 k1-W1 同指；主控亲验 apply_constraints feasible=matrix.all 实锤）→回炉轮2 `>`→`<=` 勘正+断言互翻+恰等值用例→复核 k1 PASS B0/W1/N6（W1 包数口径主控 grep 勘正销）/d1 PASS B0/W0/N6（首轮 W 九销二降N；W2 severity 双语义=批5 AUD-W10 定版口径复引——勾选=过滤 CP1 用户裁决 2026-08-31，severity=元数据，非新缺陷）；d1 首轮拒审事件=审包未内联违其岗卡输入契约→内联重派合规（流程教训：d1 位审包必须随简报内联）。门二 probe=MATRIX PASS **偏离 0**（独立复算：8 阈值对 b3a §二 B 组集合恰等/60.0 二进制精确/audit 病例 8 门全假/golden 全真/core 1566P+server 376P+16 门禁+gen_status 零漂移+329 键五项全对表）；裁决部=**收口准予**（附条件 C1~C6 登记/文档面，本笔全落）。
- **收口三检**：run_gates 16 门禁全绿（probe 复跑）；gen_status --check 零漂移（2158 字节，probe 复跑）；health-scan **RED=0**/WARN×3 存量回显（设计链同源 W-8 降级+账本 usage 缺 27 行+in=0 一行——批前存量非本批引入）——可收口。
- **欠账登记（裁决部 C1~C6+烤验欠账）**：C1 aao/manifest.py:104/435 两处「§7.6.39 厌氧 HRT」误植残留（注释面零逻辑影响）→下一出处笔勘正；C4 本机 webapp orval 生成物缺 geometry_guard（CI 强制先行仓库面不受影响——本机开发前 pnpm orval）；C5 cass/manifest.py 恰 500 行顶墙（后续触碰先筹划拆件）；C6 评审档补存 k1/d1 终判原文+projects.py:179「三面」注释下次顺手更新；**warn 用户可达性**（CLI 零消费/MCP 投影契约冻结恰三键——webapp 横幅/MCP 加键两候选面）→批6f 任务系统补完邻域裁量；**webapp constraintPicker filterSelectable 不含 geometry_guard**（geometry 门现仅 API 显式 options.constraints/design 态 constraint_choices=on 两路可达）→批6 picker kind 面扩裁量；环境实录：server venv core 快照滞后需 --reinstall-package waterprint-core（CI 全新装不受影响）。
- **预算记档**：fire_budget 120min 实耗≈2.4h（09:22Z~11:43Z）——超支=门一 B1 烤验回炉两轮+门二全实证，判定⑤照常（超支非停止事由，如实记档）。
- **火情观察**：增补四十九 08:15Z 置 READY 后 66min 班火零派发（workflow_run_id 恒旧值+claim 恒 -）+执行者会话工作区 CronList 空——automation-cf38af42 **疑似已熄**（执行者角色禁建自动化未核实他工作区火态）。续跑路径：用户直派执行者窗口（板头标准注入词）或 /batch-relay 换防重布火。
- **收口判定=⑤READY**：勾选 36→37（批3b ☑，余 15=批6a~6n+⑤b）；batch_count 4→5（<60）；墙钟≈7.7h<90h；no_progress 0；claim 释放；置 READY 最后一笔。

### 增补五十一 — 2026-09-26T12:12:39Z（换防重布：班火熄灭迁火+板面 rev5→6 版本对齐+批6a 首班发布）

- **会话性质**：用户显式 /batch-relay 换防（板头标准注入词调度员窗口）。契机=增补五十火情观察证实：旧火 automation-cf38af42 已熄（本会话 CronList 全局空复核），批3b 收口（11:43Z）后零派发，用户明示续跑。
- **换防两门+清场**：工作流部署门过（batch-relay-executor 全局在册；check-relay channel=0 fail 0 warn=rev6 ask 词同文机检绿）；深度设计门过（ai-dev-org 项目=.zcode/org-ledger.jsonl 在案+《裁决书》/第六波单源工单 wave6-master-plan.md 齐备）；旧火清场=CronList 空、零残留免 CronDelete。
- **板面复位+版本对齐**：batch_count 5→0、relay_started_utc→2026-09-26T12:10:48.865Z（熔断复位 0/60 批+90h 墙钟重计）、workflow_run_id→-（旧值 dwfrun-fb81b03e…=批3b 首班 run，GetWorkflowRun 实核 completed）、status READY/claim -/no_progress 0/hold_reason - 零位维持、last_handover→2026-09-26。protocol 段已刷新 rev5→6（旧段机证=golden rev5 逐字：rev5 标记 4/4 命中+rev6 标记 0 命中+18 弹点同构，零现场批注免归档；rev6 增量=执行者仓根锚定纪律+执行指令行参数化+开批通道标签去 rev 化）；protocol_rev 5→6。复位后 check-relay board=0 fail（R3 legacy last_dispatch 冻结行警告=正常过渡痕迹）。
- **开批四条件核验（批6a）**：①READY ✓②静默窗过（last_dispatch_utc=06:11:50.897Z 距今 ≈358min ≥30）✓③上一批 run=completed（GetWorkflowRun 实核）+git 末笔 7958d48（11:43:42Z）距今 ≈27min 实物静默 ≥5 ✓④熔断复位未触发（0<60/0h<90h）✓——四条件齐。
- **开批（workflow 通道，先于迁火防双开批竞态）**：CreateWorkflow saved batch-relay-executor（board=本板，mode=execute）→ run_id=dwfrun-f764559b-9237-499f-b299-a48bf7942b05（GetWorkflowRun 回读=running+执行者子代理 executing=发布成立）→ 原子写 last_dispatch_utc=2026-09-26T12:12:01.958Z+workflow_run_id（板头笔）。
- **迁火**：CronCreate 新火 */10（automation-143e250a-5e96-4e6b-9016-7ac16fa7fb21）→ 板头 automation_id 字段行锚定回填（替换计数=1 守卫过）；首班火将命中静默窗（last_dispatch_utc 新鲜）一行退出——节律照旧：发布后静默 30min，有效班=30/40/50/60…。
- **移交**：next=批6a gwp_ch4 27.2→27.0 数据勘误八步工序（呈批件四件已批 2026-09-26 可执行——b2c-lock-drafts/）；批6a→6b…6n 依序连续开工（预授权口径=执行路由段）；⑤b 软著=用户域终态项停板待亲查。

### 增补五十二 — 2026-09-26T12:41:30Z（批6a 收口：gwp_ch4 27.2→27.0 数据勘误八步工序+B-6/D-8 factors 笔双笔落地——READY）

- **claim/commits**：executor-b6a-20260926T121422Z（12:14:22Z 认领——批6a 首班=workflow 通道 run dwfrun-f764559b〔12:12:01Z 发布成立〕；换防会话收口笔 4dcdf89 与本班并发实录——认领前重读板头 claim=- 无冲突；组织主干=ai-dev-org v2.1.0 Skill 载入）。两笔：4b550e6（八步工序单笔〔HUMAN-LOCK〕）/0c31196（B-6/D-8 factors 笔〔HUMAN-LOCK〕）。
- **笔1=批2c 八步零偏离**（呈批件四件已批——门一 k1 两轮 PASS 复用未改呈批件字节）：apply 三 diff（factors 27.2→27.0+勘误注记/manifest 1.5.0→1.5.1/镜像桩 T6 27.0）→relock --check 全量对照过（15 工况块 60 值+4 案 serialize 双锚+8 m3 步锚=草案逐值逐锚）→--write 五件（municipal 三案 ch4 3403.767744282009→3378.740040279936+direct/total/intensity 随链；mine 零值变仅锚）→快照恰 3 处（audit HTML+双 DXF；xlsx 不变）→core 全量 890P+1F=恰 readonly 门工序中间态→lock_tests 36 根重锁（329 键 dropped=0）→test_lock 2/2 绿。
- **笔2=增补五十欠账路由兑现**（批3b 裁决部 C2 落档）：factors 增 4 键 factor.{aao,cass}.aerator.service_area_band.{min,max}=0.3/0.75（B-6 宽带并集追认〔增补四十八〕；零消费面前瞻校核位——供气量法批接线；命名循 surface_load_band.* 先例；同族同值注记）+aao/cass service_area note 升格（D-8 GB §7.9.6 条文级方法学确证+带宽注记 0.3~0.65→0.30~0.75）+manifest 1.5.1→1.6.0（键增批 minor 位先例；548→552）。
- **烤验（数据批对抗位=独立复算+专家追认——两已在位）**：笔1 复算=b2c 制备批沙箱双路径（基线 12/12 锚复现+解析缩放 fp 级 0 差异）+本班 --check 逐值复算一致；笔2 复算=本班 b6a-band-relock.py 双路径（四案 WATCHED 值块 66 键与 1.5.1 落地态逐位恒等+bytes 逐案恒等〔DV 同长〕+sha 全变〔DV 串效应独证〕）；快照 DV 单因严格证明=新工件字节回代 1.6.0→1.5.1 后 sha256 与旧冻结值逐位相等（audit html/plan dxf 实证；profile 锚④同管线同机制）；专家追认=gwp 勘误（audit 裁决③ 2026-09-25）+Rulings 三条（增补四十八）+B-6/D-8（增补四十八批3a §七 ☑）。
- **收口三检**：run_gates 16 门禁全绿（两笔提交后各复跑〔OK〕全部门禁通过）；gen_status --check 零漂移（status.md DV 行 1.5.1→1.6.0 两段再生成，2158 字节）；health-scan RED=0/WARN×3 存量回显（同增补五十口径）——可收口。server 全量 376P 零失败（零 server 改动理论零扰动实证）。
- **注记欠账**：①README §三步⑥「AI 禁跑 AGENTS §7」注=批2c 制备时点（04:52Z）口径——增补四十八预授权①（07:37Z）后按批3b 先例由执行者跑锁面笔+commit 注明预授权依据；②C1 aao/manifest.py:104/435 §7.6.39 误植残留未触（本批出处笔=coefficients 包侧非 aao 单元侧——维持挂账批6b/下一 aao 出处笔）；③B-6 kb 接线欠账维持（供气量法批——4 键已就位待消费方）；④笔2 段心跳 13:06 系未来时戳笔误（取钟错写），收口笔已改正——无接管/竞态后果（claim 全程在己）。
- **预算记档**：fire_budget 120min 实耗≈27min（12:14:22Z~12:41:30Z）在限内。
- **收口判定=⑤READY**：勾选 37→38（批6a ☑，余 14=批6b~6n+⑤b）；batch_count 0→1（<60）；墙钟≈0.5h<90h；no_progress 0；claim 释放；置 READY 最后一笔。

### 增补五十三 — 2026-09-26T14:09:28Z（批6b 收口：碳范围一补全+能耗上游扩键——READY）

- **claim/commit**：executor-b6b-20260926T125402Z（12:54:02Z 认领——批6b 首班=workflow 通道 run dwfrun-0cd27217〔12:52:46Z 发布成立〕；组织主干=ai-dev-org v2.1.0 Skill 载入）。单笔：87bc7b1〔HUMAN-LOCK〕（预授权①依据=用户 2026-09-26 全局规划指令——26 文件 +1498/−365）。
- **交付四件**：①app_carbon C-F10 燃料 CO₂（w_fuel×2.1622=21.622 t/万Nm³ 换算）/C-F11 燃烧次要 CH₄+N₂O（1 kg/TJ×389.31 GJ/万Nm³ 链）/C-F12 消化净 CH₄（案 A：gross−R，dig_mcf 0.8 独立核算废水线毯式 0.03 维持）——三式入 direct 合计+sparse 双律（因子缺席跳/消化双源缺一整式跳）；②AUD-W4 上游：vxinglvchi XL-F20~F22（w_air/w_sweep 日耗 dims+e_backwash=w_air×0.02+v_wash_daily×0.044——扫洗含于全量水不双计）+cifenli KS-F9（e_magnetic=n_units×3.0×24）+app_energy 新能耗两名入 power_total；③碳上游供数族 w_fuel/w_vs_deg/v_biogas→fuel_gas_nm3_d/vs_degraded_kg_d/biogas_m3_d（碳件消费面专用聚合通道）；④factors 10 新键+coefficients 1.6.0→1.7.0（552→562）+projection 两冻结表登记新 dims。
- **确定性勘正（批内显形潜伏缺陷）**：app_energy power_total 原 set 迭代序求和受哈希随机化影响——跨进程浮点舍入不同→serialize 字节漂移（三进程实证：同长异 sha）；本批新增两 power 键将和推过序敏感阈值显形。勘正=_POWER_FIELDS 声明序求和（语义不变仅舍入确定）；m3 基线跨进程三跑恒等复证+relock --check 归零。
- **烤验（实现+数据复合批=并集对抗位）**：门一 k1（主源席 in=13320）首轮 PASS B0/W3/N3+门一 d1（异构源席 in=14801）首轮 PASS B0/W3/N5——双席共指 C-F12 跨基 B0 呈裁（追认文本原文如此——VS 基独立键=数值面变更归用户裁量），处置全表 b6b-rulings.md §二（W2→T11 带界恒正不变式测试落地/W3→测试补档/N1→表号核对随追认）；门二实证部双路径复算（碳三式引擎 vs 手算 diff≤1.8e-15+能耗上游逐式手算一致+vector 六变体独立实算重录）+mine 负向面（新供数键零在场/回归锚 7 键逐位不变）+图域零变更（m3 四语义锚 7 步不变）；专家追认=碳七键批3.5 已签+能耗三键起草随批 Rulings（b6b-numeric-sheet/b6b-rulings）。〔b6c 勘正 2026-09-26：本行原录模型代号两枚，出仓合规 scrub 为主源席/异构源席——产出面纪律（check_model_names md 面）；原始字面=org-ledger.jsonl 在案，语义零变〕
- **锁面**：golden 四案重录（municipal direct +7126.24=fuel 2135.108+minor 11.533+digest 4979.600/power_total +63.374=e_backwash/intensity 0.5867→0.7927；mine +power_magnetic 288 无供数键面）+m3 种子 meta/7 步 serialize 锚+快照恰 3 哈希行（audit HTML+双 DXF，xlsx 不变——批6a 同形态）+镜像测试 T8~T11/vector 六变体+lock 329 根重锁零丢失（b6b-golden-relock.py --check/--write 双模式在卷宗）。
- **收口三检**：run_gates 16 门禁全绿（提交后复跑〔OK〕）；gen_status --check 零漂移（DV 行 1.6.0→1.7.0 再生成，2158 字节）；health-scan RED=0/WARN×3 存量回显（同增补五十口径）——可收口。全量：core 897P+单元包 136P 零失败（benchmark 时基断言一次负载假红——单跑绿复证记录在案）+server 376P 零失败（零 server 改动理论零扰动实证；server venv core 快照 uv --reinstall-package 同步）。
- **欠账登记**：①KV 族（mine_water/vxinglvchi）反冲洗折电未建模（AUD-W4 指针=municipal XL 侧）——manifest 头注+本行双锚，后续批 §14 起草；②C-F12 B0 跨基（BOD 基键乘 kgVS——追认原文口径）+越带负值逃逸口径+扫洗保守比能三项呈裁（b6b-rulings §三，终裁权保留）；③CH₄/N₂O 表号级核对随追认补做；④test_vector_variants 500 行顶墙（预算内，下次触碰先筹划）；⑤审包 15k tokens 超组织目标 3×（ORG-12 申报——总量 30k<40~50k 常态）。
- **预算记档**：fire_budget 120min 实耗≈75min（12:54Z~14:09Z）在限内。
- **收口判定=⑤READY**：勾选 38→39（批6b ☑，余 13=批6c~6n+⑤b）；batch_count 1→2（<60）；墙钟≈1.9h<90h；no_progress 0；claim 释放；置 READY 最后一笔。

### 增补五十四 — 2026-09-26T15:06:06Z（批6c 收口：LCC 折旧面落地——READY）

- **claim/commit**：executor-b6c-20260926T141855Z（14:18:55Z 认领——批6c 首班=workflow 通道 run dwfrun-dbe63cec〔14:16:56Z 发布成立〕；组织主干=ai-dev-org v2.1.0 Skill 载入）。单笔：be23fb3〔HUMAN-LOCK〕（11 文件 +243/−20；预授权①依据=用户 2026-09-26 全局规划指令）。
- **设计（三段轻量版）**：b6c-design.md 两案拟定（单键综合折旧率 vs 分构筑/设备双键直线）→门一 k1 设计席首轮 PASS B0/W4/N4（案乙维持：选型/结构性排除/sparse 矩阵三件均获代码证据支撑）→终裁回填 §七；W1 税入基数补 Ruling⑥/W2 golden 锚面澄清（golden=e2e calc summary 期望，不锚 joint metrics 与包 DV）/W3 零权重消费面措辞/W4 sparse 机制落点——N1~N4 全处置。
- **交付四件**：①metrics 新键 cost_capex_annualized_yuan_a（design 口径展示维度——直线法=equipment_subtotal/10 a+其余资本化全量/30 a〔税/间接/预备/递延并径=Ruling⑥ 呈报〕；不进 objective=_METRIC_KEYS/权重/基线零变更结构性排除，lcc 在场/缺席两跑 score 逐位同行为证）；②factors 两键 factor.lcc.life_{civil_structure,equipment}_a=30/10 a（D 级起草待追认——税法条例六十条法定下界+可研实践带双锚+两带相切于 30 注记）+coefficients 1.7.0→1.8.0（562→564）；③capex 装配单次化 capex_estimate 拆层（grand_total 与年折旧同源单次复用——批2b 公开面 capex_grand_total 薄壳零变）+cost 包根 EstimateSheet 再导出（§1c 既定边内三类型→四类型）；④app_opex 头注折旧挂账收敛（AUD-W11 后半收口）+file-contracts 两行+structure-graph 注记+status.md DV 行再生成（2158 字节）。
- **烤验（设计轻量三段+实现双审并集）**：门一三席=设计 k1（B0/W4/N4）+实现 k1（B0/W1/N2）+实现 d1 异构席（B0/W1/N3）全 PASS；双席独立反解共指金样链设备基数 E≈54 元退化（门二直链实测 E=54.000000 证实）——W-1 两轮处置：包络收紧 [G/30,G/10]（真上界）+集成层哨兵声明（d1 案 b：退化数据下公式判别由纯函数手算用例承担——lives 互换 866.67≠466.67 必红）+设备行近零映射=批6d 扩行范围注记；门二实证=双路径独立复算（beam 管线 vs app.run_full_calc 正门+cost 直链 takeoff→build_estimate：G 与年折旧 diff=0.0 精确相等）+N-2 展示消费面闭环（server jobs/worker.py combos asdict 直通无白名单——新键自动随任务结果下发）。
- **锁面**：测试镜像四用例随批落地〔HUMAN-LOCK〕（test_final_eval 纯函数公式+sparse/test_beam 集成包络+kit 缺席+score 不变性两跑）+329 根两轮重锁零丢失（用例落地+W-1 收紧）。
- **收口三检**：run_gates 16 门禁全绿（提交后复跑〔OK〕）；gen_status --check 零漂移（DV 行 1.7.0→1.8.0 再生成，2158 字节）；health-scan RED=0/WARN×3 存量回显（同增补五十口径）——可收口。全量：core 1575P+1F（benchmark 时基负载假红——单跑 5P 绿复证，批6b 同款在册）+server 376P 零失败（venv core 快照 uv --reinstall-package 同步后）。
- **批间勘正（批6b 遗留潜伏红推送前拦截）**：增补五十三行内模型代号两枚（dd0c785 未推送——CI 跑 run_gates 必红）出仓合规 scrub 为主源席/异构源席+行内勘正注记（语义零变，原始字面=org-ledger 在案）；教训入册：板面批次日志禁落模型代号（check_model_names 词表六 token，md 面在扫）。
- **欠账登记**：①数值两键 D 级待追认（b6c-numeric-sheet——残值率 0/安装费归并/税入基数三项口径随 Rulings 呈报）；②金样链设备基数退化 E=54 元=field_mapping 设备行近零映射——批6d 既定范围（LCC 设备支路判别力随扩行恢复）；③webapp 展示位（API 直通自动可取，UI 呈现=前端批裁量 6e/6m 域）；④本班派发 cwd 失锚一次（scripts 目录跑致账本三行错落 scripts 项目——已迁正+错位件清除；后续派发仓根 cwd 或 --project 锚定）；⑤d1 行账本 outcome 字段瘦身（审包未带机器 outcome 域——判文全文在卷宗）。
- **预算记档**：fire_budget 120min 实耗≈59min（14:18:55Z~15:18Z）在限内。
- **收口判定=⑤READY**：勾选 39→40（批6c ☑，余 12=批6d~6n+⑤b）；batch_count 2→3（<60）；墙钟≈3.1h<90h；no_progress 0；claim 释放；置 READY 最后一笔。

### 增补五十五 — 2026-09-26T16:26:13Z（批6d 收口：AAO capex 区分度数据面落地——READY）

- **claim/commit**：executor-b6d-20260926T151400Z（15:14:00Z 认领——批6d 首班=workflow 通道 run dwfrun-a8431da0〔15:12:43Z 发布成立〕；组织主干=ai-dev-org v2.1.0 Skill 载入）。实现单笔：c878b8d〔HUMAN-LOCK〕（28 文件 +365/−96；预授权①依据=用户 2026-09-26 全局规划指令）。
- **设计（轻量档+实装中勘正）**：b6d-design.md 两案（万元尺度=消费面 10⁴ 归一案甲落——面值零变；扩行最小集）。**计价语义勘正（实装中显形）**：初拟 count_times_value 全厂台数=池数×单池——实测两档同为 6954 台（AO-F20 服务面积法=总量代理，ceil 级差抵消=零区分度）且 6954×22 万=15.3 亿设备费失真（22 万≠单头价）→正解=按组计价：cass 组同款条目 quantity=4=池数实证「台=每池一套系统」→量=池数 n（direct），档差恰 22 万×10⁴×费率级联。
- **交付四件**：①manifest unit_scales 金额倍率契约（单位→折元倍率全条目全覆盖缺列即拒——九单位集实测；万元族 1e4；price_data_version 1.0.0→1.1.0；PriceItem.scale 装载+estimate amount=量×面值×scale——批6c E=54 元退化结清〔LCC 设备支路判别力恢复：金样 E=800,000/1,020,000 元两档〕）；②field_mapping 段三扩行 aao.microporous_aerator_piping（万元/台 direct ["n"] @municipal_aao equipment——AAO 轴 capex 区分度：beam 金样 n=2/3 档差 341,265.38=220,000×费率级联 1.5512）；③aao dims 回显 n（cass n_pool 先例平移：compute._geometry+out_dims+projection dim_of/non_drawn 三面登记——condition_fields 28→29 面自然扩）；④installations aao 组一条 22.0 万元/台（同物同价沿用 cass 组 2024 询价；82 条）+README/manifest-status 同步。
- **烤验（实现+数据复合批=并集对抗位）**：门一 k1（kimi-main）首轮 PASS **B0/W3/N4**+门一 d1（deepseek）首轮 PASS **B0/W5/N6**——零 B 级；回炉一轮四项实修（takeoff 对拍 n=3 判别力〔双席共指 d1-W1/k1-N1〕/万元族 common.* 点名对拍/beam 容差显式 rel=1e-6+fee_rules 耦合注记/「格=系列」术语注）+构造点审计闭项（PriceItem 全仓恰 prices.py:179/290 两处——k1-W1/d1-W3）+复引包口径（quantity=参考值不参与计算——k1-W3）+「万元/套」词表标准化呈裁（k1-N2 用户域）；处置全表 b6d-rulings.md。门二实证部=双路径复算 PASS（正门 build_estimate vs 手写费率级联+万元前缀独立倍率：三案 G/E/detail/subtotal 逐位相等+AAO 轴差 341,265.38 在窗+E 手算 800,000.00 精确+golden 重录锚 19,415,730.31428396 三方对表+分案对拍表〔municipal 三案 Δ+750.7/836.0/836.0 万、mine 零漂〕）；报告 b6d-probe-report.md（会话内实证位 E3 口径申报+账本行在案）。
- **锁面**：golden 四案+m3 种子重录（b6d-golden-relock.py --check/--write 双模式：effluent 平键零漂=碳/能耗面未触碰实证；estimate_total 三 municipal 案重录；generated DV 锚 coefficients@1.8.0+unit_prices@1.1.0+serialize 随 dims n 键漂移——种子锚 DV 串耦合二过收敛）+快照恰 3 哈希行（audit HTML+双 DXF，xlsx 不变——ambr diff 人审）+vector 六处 'n': 2.0 行内零增行（variants 493 行贴墙）+三镜像 30/29/29+329 根两轮重锁零丢失。
- **收口三检**：run_gates 16 门禁全绿（〔OK〕全部门禁通过——c878b8d 提交后 trust_root 绿）；gen_status --check 零漂移（DV 行 unit_prices 1.0.0→1.1.0 再生成，2158 字节）；health-scan RED=0/WARN×3 存量回显（同增补五十口径）——可收口。全量：core **1582P 零失败**（早轮 1581P+1=benchmark 满载时基假红——单跑绿复证，批6b/6c 同款在册；末轮复跑零失败）+server 376P 零失败（venv core 快照 uv --reinstall-package 同步后）+mypy 350/58 双绿+ruff 零违规。
- **欠账登记**：①数值单 aao.microporous_aerator_piping=22.0 万元/台 追认请求（b6d-numeric-sheet §四——预授权②事后追认制，用户域非阻断）；②「万元/套」单位词表标准化呈裁（k1-N2——42 条设备条目旧源词表一致性 vs 单条语义精度，独立数据批裁量）；③direct 条目 quantity 一致性装载告警=后续批池位（k1-W3）；④PriceItem 手构造防线缺口（k1-W1——后续 cost 域新增构造点须走 load_prices 或显式 scale）；⑤count_times_value 通道维持预留（其语义对 n 恒定量无承载——field_mapping 头注在册）；⑥aao manifest 495 行/variants 499 行双贴墙（下次触碰先筹划拆件/外移）；⑦厌氧/缺氧搅拌器计数字段挂账维持（AO-F20 头注口径——无诚实字段禁臆造）。
- **预算记档**：fire_budget 120min 实耗≈72min（15:14:00Z~16:26:13Z）在限内。
- **收口判定=⑤READY**：勾选 40→41（批6d ☑，余 11=批6e~6n+⑤b）；batch_count 3→4（<60）；墙钟≈4.3h<90h；no_progress 0；claim 释放；置 READY 最后一笔。
