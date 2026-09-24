# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

> **标准注入词（2026-09-25 上板——新窗口+简单提示词即可正确分发）**：
> - 执行者窗口（项目=智水蓝图）：「（引用技能 batch-relay）基于 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 交接文档继续开发——开工首步先加载技能 ai-dev-org，再按接力火协议认领并执行本批（工作区根 E:\class\智水蓝图\waterprint，相对路径以此为基）」
> - 调度员窗口（迁火/接任用，工作区不限）：「（引用技能 batch-relay）接任交接：你是 E:\class\智水蓝图\waterprint\docs\handoff\relay.md 的当班 hub 总调度员——读板头+protocol 段（rev2）→ 按技能换防协议布火并回填 automation_id → 提交推送 → 随即按 protocol 段开批通道（Ctrl+N+三回读）发布执行者并原子写 last_dispatch_utc → 此后每班火只调度禁执行禁重活」

- status: READY
- automation_id: automation-b3938334-9394-4c50-99ac-2ff4332c3f40 <!-- 2026-09-25 迁火完成：旧火 cbcb3949 随肥调度会话退役已删；新火由新任薄调度会话（handover 工作区）布火回填 -->
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-24T23:05:25.878Z <!-- E2E-4 批4 收口 -->
- claim: -
- no_progress_count: 0
- checked_total: 27 <!-- 2026-09-25 增补十：+E2E-1~5 插队战役五项 -->
- checked_done: 25 <!-- 2026-09-24 E2E-4 收口 24→25（三项全落+行为级三验证） -->
- protocol_rev: 2 <!-- 2026-09-25 调度健壮化批升版：Ctrl+N 主径+三回读+模型跟随；薄调度员铁律；读板卫生 -->
- last_dispatch_utc: 2026-09-24T21:36:38.025Z <!-- E2E-2 批 2 四发成立 2026-09-25 21:33Z：fetus3 唤醒配方（聚焦+回车发草稿+nudge 补发）引导 sess_e2cd19af 起跑——前两醒会话（b868e5e6/1e7cdf54）短活动后未读板静默，非合格执行者——status 保持 READY 待认领 -->
- relay_started_utc: 2026-09-24T17:44:23.011Z <!-- 2026-09-25 换防时刻 -->
- batch_count: 4 <!-- 2026-09-24 E2E-4 批4（会话内直跑） -->
- max_batches: 60
- max_wall_hours: 90
- hold_reason: -
- last_handover: 2026-09-25
- claimed_by: -
- claimed_at: -
- next_batch: E2E-5 fix-plan 批4【hygiene】卫生批（+round2 批4 扩 R2-P2-2 孤立警告/R2-P2-3 枚举 URL 回写）——插队战役收官批，收口后回归 B4-5 原排序

## protocol（角色自识别 + 最小兜底协议）

- 本板 protocol_rev=2；rev1/rev0 存量板读法向下兼容（rev0 无此行读旧字段名 last_dispatch，仅警告不阻断），换防时迁移至现行 rev。
- 时间一律 UTC（ISO8601 带 Z 后缀）；「距今 N min」=（当前 UTC−字段值）÷60000 向下取整；解析失败=预检失败。写板一律写 Z 后缀新字段名；旧字段行冻结不删。
- 预检（任何行动前，rev 感知）：字段行完整（rev1 全集；rev0 旧集）/ 时间戳可解析（rev0 旧格式仅警告）/ 数值字段纯非负整数（R10）/ status∈{READY,RUNNING,DONE,HOLD} / 无重复 status 行 / protocol_rev∈{0,1,2}——任一失败：输出 `fire: abort (reason=board_precheck_failed:<规则名>)` 后退出，并在批次日志追加欠账行。
- 收到火 prompt 的会话=调度员。一切一行退出只用固定枚举三族，禁引用板面原文：`fire: skip (reason=quiet_window|running_fresh|candidate_alive|no_ready_board)`；`fire: terminal (reason=done|hold|board_missing)`；`fire: abort (reason=board_precheck_failed:<规则名>)`。
  - 板不存在 → 单项目：CronDelete(automation_id) 后 `fire: terminal (reason=board_missing)`；shared_fire=true 板缺失=从轮转清单跳过+本轮终报记欠账，不删全局火——删火仅当全部板终态或缺失。
  - DONE/HOLD → 单项目：CronDelete(automation_id) 后 terminal(done|hold)；shared_fire=true 板只终报不删火（删火权归 hub 调度员，须全部板终态）。
  - last_dispatch_utc 距今 < quiet_window_min=30 → `fire: skip (reason=quiet_window)`（READY 未认领/RUNNING 均适用；仅约束调度员，刚被发布的执行者照常认领；值为 `-`=从未发布——窗口视为已过，非解析失败）。
  - RUNNING 且 heartbeat_utc 距今 < heartbeat_stale_min=30 → `fire: skip (reason=running_fresh)`。
  - RUNNING 且心跳距今 ≥ heartbeat_stale_min=30 → 先过 UI 活动核查：同宿必核执行者会话已无「正在执行」活动——仍有活动 → `fire: skip (reason=candidate_alive)`；跨宿降级 git/账本双核对+日志欠账行「跨宿接管未经 UI 核查」。核查过才接管：核对实际进度防重复执行再重置 claim → READY（接管后重新发布则更新 last_dispatch_utc）。
  - READY → 开批四条件：①status=READY ②静默窗已过（last_dispatch_utc 距今 ≥ quiet_window_min=30；值 `-`=从未发布视为已过）③上一批实物已静默（板面 mtime 与 git 最近提交距今 ≥ physical_quiet_min=5；无 git 仓以板面与 plan 文件 mtime 代之）④熔断未触发（batch_count<max_batches 且距今运行 <max_wall_hours 小时）。④触发 → 置 HOLD(hold_reason=circuit_batches|circuit_wall)+终报首行「熔断裂闸…」；①-③任一不满足 → 让位下一班火。四条件齐 → 先一行告知用户「接下来约 20 秒需要占用前台完成开批操作」→ 开新任务（**Ctrl+N 主径**——2026-09-25 用户实证授权；旧「禁 Ctrl+N」条以「选择项目菜单在场+三回读」为前提废止；Ctrl+N 无效再走侧边栏「新建任务」按钮）→「选择项目」勾本项目 → **回读①：项目已绑定** → 模型选择器设为与当班会话一致 → **回读②：模型名一致** → Escape 收菜单 → 真实点击 textfield → app 级 strategy=event 键盘写入下方执行指令 → **回读③：指令落框且发送按钮启用** → 点发送按钮 → 回读 echo → 原子写 last_dispatch_utc（status 保持 READY）。三回读任一不符=发布未成立，让位重试禁盲发（2026-09-25 首发两缺陷教训：项目未绑定/模型未跟随）。每回合至多开一批；hub 轮转在合格板中挑 last_dispatch_utc 最老者（并列取 prompt 清单序），成员板缺 shared_fire: true 行 → 跳过该板+日志欠账行。
- 调度员会话卫生（2026-09-25 实证铁律）：当班调度会话禁做换防/板面手术/长事故响应等重活——会话转录膨胀使共享窗口无障碍树持续重编号，观察→点击窗口内索引恒漂移、UI 动作系统性失效；重活另开会话。换防后的布火会话若已变重 → 按换防纪律迁火至新薄会话（删旧火+新薄会话 CronCreate+回填 automation_id，全局单火不变式保持）。调度会话不调 computer-use stop()（badge 常驻无害）；已 stop 的会话守卫粘滞不得复用 computer-use——降级 PowerShell SendKeys（AppActivate+按键）或让位新会话。
- 被注入执行指令的新任务会话=执行者：开工首步 Skill 加载 ai-dev-org（不可加载则按计划头部执行通道行：subagent-driven-development，无子代理则 executing-plans）→ 读板预检（只取板头字段区+执行路由+执行清单+批次日志末 3 条——防上下文膨胀，日志全量仅按需追溯）→ READY 时原子 claim（tmp 写 status:RUNNING+claim token+heartbeat_utc+勾选数快照，保留 last_dispatch_utc → mv -f 覆盖 → 回读确认，非己让位退出；此后执行者一切板写（心跳/收口/翻回/修复）落笔前同样回读，非己=已被接管停笔让位，遗留只终报呈报）→ 执行 plan 未勾任务至 fire_budget_min=60（板字段可调；每任务始末刷心跳，任务内每隔 heartbeat_refresh_min=15 亦必刷——活执行者心跳永不陈旧到接管阈值）→ 收口按固定次序判定（首中即断）：①`grep -cE '^[[:space:]]*- \[ \]'` 计 0（行首允许缩进，误报方向=晚 DONE 安全）→ DONE+终报（无 shared_fire 标记才 CronDelete；工具不可用时终报请用户在 Automations 页按 title 删）②停止事由（不可逆/破坏性、安全敏感、仓外副作用、计划破碎）→ HOLD(stop_matter)+终报 ③熔断（batch_count+1 后 ≥max_batches 或墙钟 ≥max_wall_hours）→ HOLD(circuit_batches|circuit_wall)+终报 ④勾选数未增 → no_progress_count+1，达 no_progress_max=3 → HOLD(no_progress)+终报 ⑤否则 READY。收口必做（同一原子写）：勾选框更新（有 git 提交；无 git 仓记 `commit: n/a (no-git)`）+批次日志追加+heartbeat_utc 刷新+batch_count+1（无条件；唯一例外=翻回 RUNNING 修复的回炉收口不再 +1，③按现值重判④⑤照常，日志记「回炉收口」）+claim → -。置 READY/DONE/HOLD 必须是最后一笔，置位后禁写板/仓；要修先回读（被新 claim 占据则不写，遗留只在终报呈报）→ 原子翻回 RUNNING 修毕重新收口。
- 执行指令（调度员注入新任务用）：「（引用技能 batch-relay）基于 <工作区绝对路径>\docs\handoff\relay.md 交接文档继续开发——开工首步先加载技能 ai-dev-org，再按接力火协议认领并执行本批（工作区根 <绝对路径>，相对路径以此为基）」
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
- [ ] E2E-5｜fix-plan 批4【hygiene】卫生批（+round2 批4 扩 R2-P2-2 孤立警告/R2-P2-3 枚举 URL 回写）

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
