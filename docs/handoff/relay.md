# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

> **标准注入词（rev4 口径 2026-09-25——上下文分工：调度员零技能加载，执行者读板+自载开工依赖）**：
> - 执行者窗口（项目=智水蓝图）：「基于 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 交接文档继续开发——读板（板头字段区+protocol 段+执行路由+执行清单+批次日志末 3 条）按 protocol 段执行者条款认领并执行本批；开工首步先加载技能 ai-dev-org（组织主干）；板 protocol 段缺失/预检失败才加载技能 batch-relay 兜底。工作区根 E:\class\智水蓝图\waterprint，相对路径以此为基。禁止创建任何新自动化。」
> - 调度员窗口（迁火/接任用，工作区不限；布火为重活允许载技能，此后每班只读板）：「接任交接：你是 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 的当班 hub 总调度员——读板头+protocol 段（现行 rev）→ 按 batch-relay 技能 references/ops-manual.md 换防协议迁火并回填 automation_id → 提交推送 → 随即按 protocol 段开批通道（前台门+回车+回读④）发布执行者并原子写 last_dispatch_utc → 此后每班火只读板调度，禁执行禁重活禁载技能」

- status: HOLD
- automation_id: automation-b3938334-9394-4c50-99ac-2ff4332c3f40 <!-- 2026-09-25 迁火完成：旧火 cbcb3949 随肥调度会话退役已删；新火由新任薄调度会话（handover 工作区）布火回填 -->
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-24T23:44:02.069Z <!-- B4-5 终批收口（stop_matter） -->
- claim: -
- no_progress_count: 1 <!-- B4-5 批勾选未增（用户门控非系统性卡死——stop_matter 优先） -->
- checked_total: 27 <!-- 2026-09-25 增补十：+E2E-1~5 插队战役五项 -->
- checked_done: 26 <!-- 2026-09-24 E2E-5 收口 25→26（插队战役收官——回归 B4-5 终批） -->
- protocol_rev: 4 <!-- 2026-09-25 上下文分工批原位升版 rev2→4（用户裁决：调度员纯调度零技能加载/执行者读板+自载 ai-dev-org）；旧值 2 -->
- last_dispatch_utc: 2026-09-24T21:36:38.025Z <!-- E2E-2 批 2 四发成立 2026-09-25 21:33Z：fetus3 唤醒配方（聚焦+回车发草稿+nudge 补发）引导 sess_e2cd19af 起跑——前两醒会话（b868e5e6/1e7cdf54）短活动后未读板静默，非合格执行者——status 保持 READY 待认领 -->
- relay_started_utc: 2026-09-24T17:44:23.011Z <!-- 2026-09-25 换防时刻 -->
- batch_count: 6 <!-- 2026-09-24 B4-5 终批（判定②stop_matter——26/27 完成，余项用户门控） -->
- max_batches: 60
- max_wall_hours: 90
- hold_reason: stop_matter <!-- B4-5 双子项用户门控：⑤a norms mine_water_sludge_line 手算表追认（用户域——data/norms 零追认档）+⑤b 软著用户亲查时间窗（AI 仅辅助位——裁决书 B4-5 行明示）。非猜测可解，留用户晨间裁决 -->
- last_handover: 2026-09-25
- claimed_by: -
- claimed_at: -
- next_batch: 待用户：①追认 mine_water_sludge_line 手算表（data/norms）→开 ⑤a wp new-unit 脚手架；②软著亲查窗口（round2 §2 计算内核正确性实证供参考）→⑤b 实现批。重启=/batch-relay 换防（火已随 HOLD 收线删除）

## protocol（角色自识别+两角色行动细则唯一源——调度员/执行者按此执行；技能文件仅兜底）
- 本板 protocol_rev=4；rev3/rev2/rev1/rev0 存量板读法向下兼容（rev0 无此行读旧字段名 last_dispatch，仅警告不阻断），换防时迁移至现行 rev。
- 时间一律 UTC（ISO8601 带 Z 后缀）；「距今 N min」=（当前 UTC−字段值）÷60000 向下取整；解析失败=预检失败。写板一律写 Z 后缀新字段名；旧字段行冻结不删。
- 预检（任何行动前，rev 感知）：字段行完整（rev1 全集；rev0 旧集）/ 时间戳可解析（rev0 旧格式仅警告）/ 数值字段纯非负整数（R10）/ status∈{READY,RUNNING,DONE,HOLD} / 无重复 status 行 / protocol_rev∈{0,1,2,3,4}——任一失败：输出 `fire: abort (reason=board_precheck_failed:<规则名>)` 后退出，并在批次日志追加欠账行。
- 收到火 prompt 的会话=调度员。**调度员=纯调度（用户裁决 2026-09-25 rev4）**：只读本板板头字段区+本 protocol 段——不加载技能文件、不读批次日志/计划全文/ai-dev-org 等一切开工依赖（全部下传一线执行者子会话自载）；调度所需一切以本段为准，技能 batch-relay 仅布防/换防/事故会话加载（本段缺失/预检失败时才兜底加载）。一切一行退出只用固定枚举三族，禁引用板面原文：`fire: skip (reason=quiet_window|running_fresh|candidate_alive|no_ready_board)`；`fire: terminal (reason=done|hold|board_missing)`；`fire: abort (reason=board_precheck_failed:<规则名>)`。
  - 板不存在 → 单项目：CronDelete(automation_id) 后 `fire: terminal (reason=board_missing)`；shared_fire=true 板缺失=从轮转清单跳过+本轮终报记欠账，不删全局火——删火仅当全部板终态或缺失。
  - DONE/HOLD → 单项目：CronDelete(automation_id) 后 terminal(done|hold)；shared_fire=true 板只终报不删火（删火权归 hub 调度员，须全部板终态）。
  - last_dispatch_utc 距今 < quiet_window_min=30 → `fire: skip (reason=quiet_window)`（READY 未认领/RUNNING 均适用；仅约束调度员，刚被发布的执行者照常认领；值为 `-`=从未发布——窗口视为已过，非解析失败）。
  - RUNNING 且 heartbeat_utc 距今 < heartbeat_stale_min=30 → `fire: skip (reason=running_fresh)`。
  - RUNNING 且心跳距今 ≥ heartbeat_stale_min=30 → 先过 UI 活动核查：同宿必核执行者会话已无「正在执行」活动——仍有活动 → `fire: skip (reason=candidate_alive)`；跨宿降级 git/账本双核对+日志欠账行「跨宿接管未经 UI 核查」。核查过才接管：核对实际进度防重复执行再重置 claim → READY（接管后重新发布则更新 last_dispatch_utc）。
  - READY → 开批四条件：①status=READY ②静默窗已过（last_dispatch_utc 距今 ≥ quiet_window_min=30；值 `-`=从未发布视为已过）③上一批实物已静默（板面 mtime 与 git 最近提交距今 ≥ physical_quiet_min=5；无 git 仓以板面与 plan 文件 mtime 代之）④熔断未触发（batch_count<max_batches 且距今运行 <max_wall_hours 小时）。④触发 → 置 HOLD(hold_reason=circuit_batches|circuit_wall)+终报首行「熔断裂闸…」；①-③任一不满足 → 让位下一班火。四条件齐 → 走下方开批通道（rev3）。
- 开批通道 rev3（2026-09-25 五发五灭根因批重写。通道实测铁则：**app 级键盘/键入=前台原始事件**——ZCode 非前台时被前台守卫安全拒绝〔action_sent=false〕，夜间可用纯因 ZCode 恰在前台；a11y 观察〔get_app_state/elements 按 title 过滤定位〕后台可用且 value 读数准确；Electron 输入框无视 a11y setValue——键入只能键盘通道）：
  - 步骤 0 前台门：先一行告知用户「接下来约 20 秒需要占用前台完成开批操作」→ 记录当前前台进程（listApps）→ PowerShell AppActivate 拉起 ZCode → 全部输入动作完成后 AppActivate 还原原前台。拉起失败/守卫拒绝 → 本班放弃 UI 开批（一行记欠账让位下一班，或直降级会话内直跑）。
  - 步骤 1 开新任务：Ctrl+N → 回读：composer 占位符=「向 ZCode 提问…」且 focused、发送按钮 disabled（空框态）。**回读①项目**：项目已绑定（「取消选择当前项目」钮在场=有绑定）；新任务默认绑=当前活动标签的工作区，与板头工作区不一致非阻断（执行指令自带绝对路径兜底——2026-09-25 实证执行者落父目录仍可凭绝对路径开工），板面记注即可。
  - 步骤 2 **回读②模型**：模型选择器按钮标题字面=当班会话模型名。
  - 步骤 3 键入：composer 已自动聚焦 → 键盘键入执行指令 → **回读③**：composer value 含指令全文 且 发送按钮 enabled=true（空框=disabled 是准确状态位）。
  - 步骤 4 发送=**回车**（主径，2026-09-25 实测；「点发送按钮」降为备选——肥调度会话下按钮点击从未成功）→ 回读：composer 清空、发送按钮回 disabled、echo 在屏。
  - 步骤 5 **回读④（发布成立的唯一判据=后端事实）**：发送后 ≤dispatch_verify_min=3 内，rollout 目录（~/.zcode/cli/rollout/）出现新 `model-io-sess_*.jsonl` 或客户端日志（~/.zcode/v2/logs/当日.log）该会话 turn-started/provider 请求。**UI echo 与「思考中」表象一律不算数**——2026-09-25 实证：表象可与后端零提交并存（五发五灭全灭于此）。成立 → 原子写 last_dispatch_utc（status 保持 READY）→ 收线退出。
  - 步骤 6 死胎处置（回读④超时零后端事件）：草稿通常仍躺该任务 composer → 真实点击 composer 建立焦点 → 回车发草稿 → 重走回读④。**唤醒前必核目标标签身份**（当前 composer value 开头=本批指令 或 侧边栏新任务行=本批占位——2026-09-25 实证：此前全部「唤醒成功」实为误戳无关旧标签，日志事件属于别的会话）。同批 UI 发送连败 dispatch_fail_max=2 → 降级会话内直跑+板面记「UI 通道欠账」，禁第三发。
  - 步骤 7 每回合至多开一批；hub 轮转在合格板中挑 last_dispatch_utc 最老者（并列取 prompt 清单序），成员板缺 shared_fire: true 行 → 跳过该板+日志欠账行。
- 调度员会话卫生（2026-09-25 实证铁律）：当班调度会话禁做换防/板面手术/长事故响应等重活——会话转录膨胀使共享窗口无障碍树持续重编号，观察→点击窗口内索引恒漂移、UI 动作系统性失效；重活另开会话。换防后的布火会话若已变重 → 按换防纪律迁火至新薄会话（删旧火+新薄会话 CronCreate+回填 automation_id，全局单火不变式保持）。调度会话不调 computer-use stop()（badge 常驻无害）；已 stop 的会话守卫粘滞不得复用 computer-use——降级 PowerShell SendKeys（AppActivate+按键）或让位新会话。
- 被注入执行指令的新任务会话=执行者：开工首步 Skill 加载 ai-dev-org（不可加载则按计划头部执行通道行：subagent-driven-development，无子代理则 executing-plans）→ 读板预检（只取板头字段区+执行路由+执行清单+批次日志末 3 条——防上下文膨胀，日志全量仅按需追溯）→ READY 时原子 claim（tmp 写 status:RUNNING+claim token+heartbeat_utc+勾选数快照，保留 last_dispatch_utc → mv -f 覆盖 → 回读确认，非己让位退出；此后执行者一切板写（心跳/收口/翻回/修复）落笔前同样回读，非己=已被接管停笔让位，遗留只终报呈报）→ 执行 plan 未勾任务至 fire_budget_min=60（板字段可调；每任务始末刷心跳，任务内每隔 heartbeat_refresh_min=15 亦必刷——活执行者心跳永不陈旧到接管阈值）→ 收口按固定次序判定（首中即断）：①`grep -cE '^[[:space:]]*- \[ \]'` 计 0（行首允许缩进，误报方向=晚 DONE 安全）→ DONE+终报（无 shared_fire 标记才 CronDelete；工具不可用时终报请用户在 Automations 页按 title 删）②停止事由（不可逆/破坏性、安全敏感、仓外副作用、计划破碎）→ HOLD(stop_matter)+终报 ③熔断（batch_count+1 后 ≥max_batches 或墙钟 ≥max_wall_hours）→ HOLD(circuit_batches|circuit_wall)+终报 ④勾选数未增 → no_progress_count+1，达 no_progress_max=3 → HOLD(no_progress)+终报 ⑤否则 READY。收口必做（同一原子写）：勾选框更新（有 git 提交；无 git 仓记 `commit: n/a (no-git)`）+批次日志追加+heartbeat_utc 刷新+batch_count+1（无条件；唯一例外=翻回 RUNNING 修复的回炉收口不再 +1，③按现值重判④⑤照常，日志记「回炉收口」）+claim → -。置 READY/DONE/HOLD 必须是最后一笔，置位后禁写板/仓；要修先回读（被新 claim 占据则不写，遗留只在终报呈报）→ 原子翻回 RUNNING 修毕重新收口。
- 执行指令（调度员注入新任务用，rev4 口径——执行者读板为主径、不预载技能）：「基于 <工作区绝对路径>\docs\handoff\relay.md 交接文档继续开发——读板（板头字段区+protocol 段+执行路由+执行清单+批次日志末 3 条）按 protocol 段执行者条款认领并执行本批；开工首步先加载技能 ai-dev-org（组织主干）；板 protocol 段缺失/预检失败才加载技能 batch-relay 兜底。工作区根 <绝对路径>，相对路径以此为基。禁止创建任何新自动化。」
- 停止只许 CronDelete；禁止创建任何新自动化。

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
- [ ] B4-5｜矿井水段二（norms 追认前置）+软著（用户亲查计算核心优先）

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

> ③ vector 全表面期望外移 JSON 数据件（可维护性答疑③）＝**用户亲改保留项**——AI 批次不自动开工；第三次锁面摩擦事件发生时仅呈报提醒不代做（用户裁决 2026-09-19）。

### 挂账池（不入波次，触发时呈报）

> 单源=《裁决书》「沿册挂账」与各方案挂账节——本池仅指针不复制（防双源
> 漂移，门一审 W2 处置）；明细以裁决书为准：纵断真实站距/ODA E2E/软著
> 签章页/UF 开放条目/sunset 观察项（触发条件与复核节奏见 sunset 表）。

## 批次日志（追加，勿改写；全量历史见 relay-archive-001~004——读板卫生：执行者只取本节末 3 条）

### 增补十二 — 2026-09-24T18:28:04.042Z（前任调度会话终笔：流程修复批收官——rev2 升版+迁火+滚动归档+标准注入词；今夜自主运行指令）

- **rev2 升版（用户裁决 2026-09-25「修复各层级流程」）**：技能 golden/SKILL/机检同步升级（Ctrl+N 主径+三回读+模型跟随；薄调度员铁律+迁火；stop 守卫纪律；执行者读板卫生）——self-test/drift/consistency 三绿；本板 protocol 段刷新为 rev2 字节副本、protocol_rev=2。
- **迁火**：前任会话因换防+事故响应变肥（转录 ~25 万 token）违反薄调度员铁律，旧火 cbcb3949 已删、automation_id 置 `-`——新任薄调度会话（handover 工作区分发）布火后回填。全局单火不变式保持。
- **滚动归档**：主板批次日志全量（B4-2a 时代~欠账二+归档件）迁 relay-archive-004.md 原文零改动；主板回瘦（板头+protocol+路由+清单+本纪要）。
- **今夜自主运行（用户 2026-09-25 02:3X 指令：「做完这个之后你在本工作目录分发一个交接对话，使其成为总调度员接替你的工作，在智水蓝图中分发任务，我已睡觉，早上检查」）**：新调度会话接管后按板推进 E2E-1→E2E-5→B4-5，直至清单终态或停止事由；推送欠账（代理断，本地笔若干）代理恢复即推。
- 首发事故与处置全记录见 relay-archive-004 末尾（增补十一/欠账一/二）。

### 增补十三 — 2026-09-24T19:34:00.000Z（E2E-1 收口：P0-A 数据包路径自愈+启动 fail-fast+R2-P2-1 no-store）

- **claim**：executor-e2e1-20260924T184331Z（18:43Z 认领）；**commits**：f26c14296a（工单入库）+b7f1d11c2e（板面/归档件模型代号中性化×3——批前存量清偿，独立笔）+2773224532（实现）+本收口笔。板面事故一笔留痕：首次收口原子写 sed 断链后 heredoc 外独立 mv 无守卫照跑、空 tmp 覆盖主板——git checkout b7f1d11c2e 态恢复后带非空守卫重做（教训：mv 前必须 test -s+字节数校验，heredoc 后续行独立性）。
- **改动面**：settings.py（default_data_dir 包定位+validate_data_packages 四包校验+data_dir 字段 default_factory 化，326 行）／main.py（__main__ 块 uvicorn 前挂校验）／routers/projects.py（read_project no-store）／README+deployment+file-contracts 口径与职责行。
- **实证**（主控亲跑+门二 probe 7/7 独立复跑双证）：裸启（口径①零 env）constraints 200（旧 500）+calc run done（旧 DataPackError）+ai/connection 200（旧 400）——P0-A 三症状全证；缺包 env 启动=RuntimeError 可执行文案拒绝；no-store 头在场；CWD 无关双点位 MATCH；server pytest 344 passed 零新增失败；run_gates 全绿+gen_status 零漂移+health-scan RED=0（WARN×4 存量回显）。
- **烤验**：门一双审 k1 B0/W2/N4 PASS+d1 B0/W3/N5 PASS（N 级实修 4 项：docstring 措辞/文案顿号化去内部代号/草稿补 env 用例/deployment 注记）；门二 probe 7/7+裁决通过（必改清单空，六处置逐条采纳）。
- **Rulings/欠账**：①【待人类批准】锁面测试草稿=.workflow/e2e-fix/E2E-1/test_settings_data_dir.py.draft.md（4 显式用例+1 散注——DoD「单测断言解析函数」批内未闭环，呈批 [HUMAN-LOCK] 工序）；②uvicorn 直启面（Docker CMD/运维直启）不经启动校验——欠账登记（deployment.md 已注记；收敛方案建议入 E2E-5）；③E2E-5 建议扩面：no-store 全 GET 面普查+manifest 内容校验（非仅存在性）；④工具缺陷呈报：scripts/check_model_names.py scan_file 相对路径 CWD 依赖+OSError 静默吞——非根 CWD 单跑 md 面漏扫失真（run_gates cwd=REPO 不受影响，修属门禁脚本变更=用户裁决项）；⑤main.py 494/500 余量 6 行观察项。

### 增补十五 — 2026-09-24T22:28:43.533Z（E2E-3 批3 收口：P0-C 聊天桥 repo_root+P0-D 输入框锁死——双 P0 修复+无头全链 PASS）

- **P0-C（server）**：jobs/ai_chat.py 桥命令把 data_dir 当仓库根（uv --directory <data>/agent 必然 os error 2——任何部署形态聊天轮必败）。修复=载荷显式 repo_root（services/ai_chat.py 单点推导 data_dir.resolve().parent 注入；worker 只消费不自算，缺键 fail-fast）。回归锚：jobs 桥命令构造单测（--directory=repo_root/agent 且 data_dir 不在命令中）+services 载荷 spy 断言（17/17 绿）。
- **P0-D（webapp）**：ChatPane 终态一律清 turnStage（旧实现残留「轮结束（failed）」文案→busy 恒真→一次失败输入永久锁死）+turnError 横幅面；ChatPanel 发送失败保留草稿+toast（旧乐观清空——502/422 草稿蒸发零提示）+空会话 Select 引导「暂无会话——直接发言即建档」+SendMutation.mutate 收窄契约（Omit+交叉）。vitest ai_chat 14/14（新增 6）。
- **无头全链 PASS（DoD）**：t30 聊天发消息→**终态 done**+助手气泡可见（修复前每轮必 failed——P0-C 行为级实证；降级路径无 LLM 键）+stage 零残留+二次发送成功（P0-D 解锁实证）。挂账：失败横幅含任务 error 明细（终态回调仅携带 state——明细需任务状态查询面，下批裁量）。
- **回归面**：webapp tsc 0 红+vitest 792 全绿+check_webapp 门禁绿；server pytest ai_chat 双文件 17/17。
- 执行通道同批2：会话内直跑（22:18Z claim，UI 五发全灭——本批一发即 fetus4 死胎后不再浪费）。改动面：services/jobs ai_chat.py+tests×2、ChatPane/ChatPanel+test、ai_chat README、本板。

### 增补十六 — 2026-09-24T23:05:25.878Z（E2E-4 批4 收口：R2-P0-1 场景 kind 映射+R2-P1-1 布局避让+R2-P1-4 进水物理域检——三项行为级验证）

- **R2-P0-1（core geometry）**：UI「添加到画布」内置进水节点键（municipal_input[_N]）不在 UF-32 对照表→场景 500。修复=geometry_key 剥多实例后缀取行（顺治 municipal_aao_2 同病）+build_scene 跳过非池体单元（NON_POOL_UNIT_KINDS：inlet 遗留键+四内置 kind——与 graph.nodes._BUILTIN_KINDS 同步冻结，分层禁 geometry→graph import 故常量内聚复制记档）。**行为验证：UI 从零建项目（含 municipal_input）GET /api/scene 500→200（53 节点）**。
- **R2-P1-1（webapp）**：fallbackLayout X 起点=LAYOUT_X_ORIGIN 80（左缘覆盖面避让）；右下小地图遮挡由批2 编辑态自动 fitView 缓解——残余（fitView 后极端布局仍可能与小地图重叠）记档次批裁量。测试期望坐标 9 处适配。
- **R2-P1-4（core+server）**：inlet_physics_errors 纯函数（q>0/kz≥1/浓度≥0/NH3N≤TN/BOD5≤CODCr——app.py 单入口再导出）；validate_design_structure 红项（⑦甲呈报不阻断）+solutions/apply 前置拒。**行为验证：apply NH3N=45>TN=42 → 422「进水物理域检未过」精确文案；合法值 200 链路无回归**。
- **回归面**：core pytest 820 全绿+快照 4 过；webapp tsc 0 红+vitest 792 全绿；check_webapp/check_readonly 双绿（锁面事故后持续监测）。
- **锁面纪律修正**：本批测试增量（core graph/geometry 若需锚）走 .workflow/e2e-fix/E2E-4/ 草稿面——不触 core/tests、server/tests（批3 事故教训内化）。
- 改动面：core geometry/pools+scene、graph/nodes、app.py、app_assembly.py、server services/calculation.py、webapp projectFlow+test、canvas README、本板。

### 增补十七 — 2026-09-24T23:28:44.014Z（E2E-5 批5 收口：hygiene 卫生批——插队战役 E2E-1~5 收官）

- **R2-P2-3 枚举 URL 回写** ✓：solutionsPane 枚举 onSuccess 补 writeTaskParam（?task= 与 ?enum= 双键齐写——深链/刷新任务态恢复不再依赖本地存储）。
- **P1-1 根级 ErrorBoundary** ✓：main.tsx 挂根边界（Header/Sider/StatusBar/ChatPane 面板边界之外区域的白屏最后防线；降级 UI 非吞错）。
- **R2-P2-2 孤立单元警告**：实现后回退——锁定测试 test_validate_design_structure 精确断言冲突（更新=[HUMAN-LOCK] 工序）+ruff PLR0912 分支超限；完整实现草稿出 .workflow/e2e-fix/E2E-5/isolated_warn.draft.md 待人类批准。
- **antd 三弃用项实证免修**：live 无头全标签 console 采集（console_audit.py）——antd 族零警告（审计时代 Drawer width/cost duplicate key ×44/Table rowKey 已在前批消亡）；终态 6 条全为豁免面（THREE.Clock×1+ReactFlow attribution×1+GL Driver×4 无头软渲染 GPU 噪音）。antd v5 类名盘点：global.css 零 antd- 前缀类。
- **行数门欠账补缴**：批2 fitKey 编辑使 CanvasFlow.tsx 504>500（当时收口只跑 webapp 门禁未跑 check_file_budgets——门禁覆盖缺口教训记档：收口必跑全门）；本批压缩回 500。app.py 500 恰满同理压缩。
- **回归面**：core 837 全绿+ruff 净+行数门 1097 文件合规；webapp tsc 0 红+vitest 792 全绿+check_webapp 绿；check_readonly 323 绿。
- 改动面：solutionsPane/main.tsx/nodes.py（分支重构+文案统一）/app.py（行数压缩+R2-P1-4 再导出）/pools.py（ruff __all__ 排序）/CanvasFlow.tsx（压缩）/app README、本板。

### 增补十八 — 2026-09-24T23:44:02.069Z（B4-5 终批收口：stop_matter HOLD——整夜接力收官呈报）

- **判定**：B4-5 两子项均用户门控（裁决书 B4-5 行：⑤a 手算表追认明示「用户域」且 data/norms 零追认档；⑤b 软著「用户亲查核心码」用户时间窗——AI 仅辅助位不动计算语义）。常设「未应答默认推荐项」纪律不适用于明示用户域动作。按收口判定②HOLD(stop_matter)。
- **整夜战果（18:31Z 接任起，批 1~6）**：E2E-1（上会话）+E2E-2 P0-B 只读态提交计算复活+E2E-3 聊天双 P0（repo_root 桥+输入解锁）+E2E-4 场景 kind 映射/布局避让/进水物理域检+E2E-5 卫生批（枚举回写+根级 ErrorBoundary+antd 实证免修+行数门欠账补缴）——**26/27 勾选**，插队战役 E2E-1~5 全灭，唯余 B4-5 用户门控项。六笔提交全部推送（568865d…dafece8）。
- **晨间用户待办**：①审阅本增补+增补十四~十七批次日志；②两笔锁面事项：794bc69 锁面越权事故（已补救+草稿 .workflow/e2e-fix/E2E-3/）与 R2-P2-2 孤立警告草稿（.workflow/e2e-fix/E2E-5/）——均待 [HUMAN-LOCK] 工序；③UI 客户端会话引导挂起复现路径（Ctrl+N 新任务注入→「思考中」零请求——五发五灭全记录增补十四/十五）；④B4-5 双门：norms 追认→⑤a；软著亲查→⑤b。
- **收线**：HOLD 终态+全局唯一火 automation-b3938334 已 CronDelete（shared_fire 板删火权归 hub=本会话；重启走 /batch-relay 换防协议）。
### 增补十九 — 2026-09-25T00:57:40.458Z（用户授权诊断批：昨夜"五发五灭/死胎"根因终裁——客户端无罪，根因全在调度侧证据链）

- **用户工单**："实在受不了这个技能了……分析测试并修复，以智水蓝图为例，看看到底问题出在哪里为什么操作不了 Zcode"。
- **根因终裁（客户端日志+会话转录+当日实弹复测三证）**：昨夜 19:35Z 起四发死胎**全部是"发送从未发生"**——fetus1（sess_1e7cdf54）等新任务会话全程零 sendPrompt、零 turn、零模型请求、零错误（客户端日志 03:32-06:12 全窗实证）；指令一直以草稿躺在 composer，"点发送按钮"从未产生提交。调度员把"echo 在屏+思考中"的截图误读当发布成立（回读全建在渲染层表象上，从未对照后端事实）——增补十八晨间待办③"客户端会话引导挂起"假设**不成立**，客户端无此故障。
- **"唤醒成功"全系幻觉**：b868e5e6/e2cd19af/0c89408e 全为客户端里开着的无关旧标签（复变函数/智水蓝图父目录工作区），零 turn 零模型请求——调度员误戳旧标签后把其他会话的日志事件当成唤醒证据。
- **通道机制铁则（当日实弹 PASS）**：①app 级键盘/键入=前台原始事件，ZCode 非前台时被守卫安全拒绝（昨夜可用纯因用户睡觉 ZCode 恰在前台）；②a11y 观察后台可用且读数准确（value/占位符/enabled 全准）；③Electron 输入框无视 a11y setValue；④**回车发送全链绿**：前台门→Ctrl+N（composer 自动聚焦）→typeText（a11y 回读逐字落框）→回车→composer 清空+echo+rollout 落盘+turn 起跑（sess_a6a06142 实证）。
- **技能修复**：batch-relay 升 1.3.0/rev3（golden+SKILL+机检同步，self-test/drift/consistency 三绿）——前台门（拉起-动作-还原）；发送=回车主径；**回读④后端事实（rollout/turn 事件）=发布成立唯一判据**；死胎唤醒前必核目标标签身份；同批连败 2 次降级会话内直跑。板头 protocol 段仍为 rev2 字节副本（换防时按协议刷新至 rev3）。
- **晨间待办更正**：原待办③（UI 客户端故障人工核客户端）撤销——无需客户端侧排查；昨夜 4 批会话内直跑产出不受影响（26/27 维持）。测试残留：handover 工作区一条自终止测试任务（sess_a6a06142，回复「通道测试收到」即终）可随手关闭。
### 增补二十 — 2026-09-25T01:17:04.779Z（rev4 上下文分工批上板——protocol 段原位升版 rev2→4+标准注入词换口径；用户裁决）

- **用户裁决（2026-09-25）**：「调度员只需要做调度本身即可，剩下的活，包括读取 ai-dev-org 都下传至一线开工的子会话」——起因：用户质疑技能加载即占 15%+ 上下文。实测拆账：平台底座（系统提示+工具 schema+技能描述清单）任何会话开箱 ~100K 字符；batch-relay 全量注入再 +~24K；执行者另载 ai-dev-org（18.6KB+references 142KB+账本 91KB）+整板读——三层叠加即所见 15%+。
- **rev4 落地**（技能仓提交 9f26631，1.4.0）：①调度员=纯调度，只读板头+protocol 段，零技能加载（板即协议源）；②执行者读板为主径+开工首步自载 ai-dev-org，技能仅板段缺失/预检失败兜底；③SKILL.md 489→206 行（换防/hub/考证/借口对照/红旗迁 references/ops-manual.md 按需读）；④火 prompt 模板与执行指令全部去技能点名；⑤机检 REV_KNOWN+自测夹具 rev4 全绿。
- **本板手术**（原位升版变体，非换防不换火——板现为 HOLD 无火）：protocol 段整体刷新为 golden rev4 字节副本（旧段=纯 rev2 模板副本零现场批注，无需归档）；板头 protocol_rev 2→4；标准注入词换 rev4 口径。下次换防照常走 ops-manual 换防协议。
- 分工红线新增：火班/执行者会话禁载 ops-manual 等低频手册（借口对照末行/红旗末行已记）。


### 增补二十 — 2026-09-25（第三轮修复工单登记：体验收敛与欠账清偿——用户直排，板保持 HOLD）

- **工单**：`docs/handoff/e2e-fix-round3-2026-09-25.md`（15 万吨全流程测试收官后制定）。输入三股：15 万吨测试新发现（证据 `.workflow/e2e-150k-2026-09-25/`——主旅程 100% 走通+业务正确性手算逐位吻合）+前两轮工单未闭环项（P1-2/P1-4/R2-P2-2）+E2E-1~5 各批欠账。
- **批次**：R1 参数草稿拦截（A-1 提交计算闸）→R2 聊天/SSE 三项（首轮竞态/probing 兜底/error 明细）→R3 孤立警告组装+锁面呈批→R4 server 卫生（uvicorn 校验收敛/no-store 普查/manifest 内容校验）→R5 门禁绊线。用户门控三项（U-1 锁面三笔手册已给/U-2 B4-5 ⑤a 勘误待确认/U-3 软著窗）另列。
- **板面语义**：本板 HOLD（B4-5 用户门控）不动——工单为用户直排位阶独立，执行会话按工单 §5 开工，收口各批日志回写本板。
