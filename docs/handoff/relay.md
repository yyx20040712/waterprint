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

- status: RUNNING <!-- 2026-09-25 批2d claim（executor-b2d-20260925T143536Z）；前值 READY（R4 收口置位）-->
- automation_id: automation-a9cfbf66-f084-4d7d-afd9-207ce6877db2 <!-- 2026-09-25 rev4 换防迁火：CronList 证实旧火 b3938334 已删（HOLD 收线笔），新火由 handover 薄调度会话布；字段行锚定+计数守卫=1 回填 -->
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-25T14:35:36.000Z <!-- 批2d claim 刷新 -->
- claim: executor-b2d-20260925T143536Z <!-- 2026-09-25 批2d 认领；勾选快照 checked 29/38 -->
- no_progress_count: 0 <!-- 2026-09-25 新排程重置（原 1=B4-5 用户门控非系统性卡死） -->
- checked_total: 38 <!-- 2026-09-25 增补二十五：27−1（B4-5 拆分）+12（第五波 R3/批2b/R4/批2d/R5/批3.5/批5/⑤a/批2c/批3a/批3b/⑤b） -->
- checked_done: 29 <!-- 2026-09-25 R4 收口 28→29（第五波 2/12） -->
- protocol_rev: 4 <!-- 2026-09-25 上下文分工批原位升版 rev2→4（用户裁决：调度员纯调度零技能加载/执行者读板+自载 ai-dev-org）；旧值 2 -->
- last_dispatch_utc: 2026-09-25T14:35:39.984Z <!-- 2026-09-25 第四班发布成立（回读④：sess_b606debd ~50s 落盘；env 块工作区=E:\class\handover——绑定偏差见增补三十三）；旧值 2026-09-25T12:07:25.336Z（第三班 R4） -->
- relay_started_utc: 2026-09-25T09:46:25.615Z <!-- 2026-09-25 rev4 换防重置（熔断墙钟基准）；旧值 2026-09-24T17:44:23.011Z -->
- batch_count: 9 <!-- R4 收口 +1（上限 60） -->
- max_batches: 60
- max_wall_hours: 90
- hold_reason: - <!-- 2026-09-25 解锁：原 stop_matter（B4-5 双子项用户门控）——⑤a 勘误排程+⑤b 转清单终态项 -->
- last_handover: 2026-09-25
- claimed_by: -
- claimed_at: -
- next_batch: 批2d 方案比选可视化三图+picker 修复（backend-calc-complete 批2d——帕累托前沿/平行坐标/龙卷风 echarts 6.1；含 webapp constraintPicker 2-kind 锁死 vs kb 实发 4 类修复+真目录形状用例〔批2a 裁决部 C4〕；联合枚举 UI R-B44b-4 并案裁量）

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
- [ ] 批2d｜方案比选可视化三图+picker 修复（backend-calc-complete 批2d——帕累托前沿/平行坐标/龙卷风 echarts 6.1；**含** webapp constraintPicker 2-kind 锁死 vs kb 实发 4 类修复+真目录形状用例〔批2a 裁决部 C4〕；联合枚举 UI R-B44b-4 并案裁量）
- [ ] R5｜门禁绊线+定版脚本（e2e-fix-round3 批5——C-4 check_model_names 两处〔OSError 计数+目录漂移绊线〕+D-1 15 万吨定版脚本沉淀 p150k_final.py+React 重复 key 警告定位顺手〔healthcheck 挂账〕）
- [ ] 批3.5｜范围一补全·调研先行（backend-calc-complete——ganhua 燃料因子权威源检索：有源则起草立键标注待追认/无源登记挂账；xiaohua 消化 MCF 分档〔IPCC 2019 Refinement Table 6.3 消化档〕）
- [ ] 批5｜低优先堆（backend-calc-complete——NaN 可行口径统一/timeout 诊断维度/severity 执法统一/裁决档勘误两处〔W2:549→548 与 34760.46→34760.70〕/beam.py 拆件结构债/app.py 500 贴墙欠账/main.py 余量观察项）
- [ ] ⑤a｜矿井水污泥线新单元（B4-5 拆项——wp new-unit 脚手架+四件套实现批；前置勘误已确认 2026-09-25〔增补二十五〕）
- [ ] 批2c｜gwp_ch4 27.0 呈批件制备（backend-calc-complete——factors.yaml 改值 diff+golden 五工况期望值重算草案+锁面工序 README；**制备批不实装不提交**——golden 重录涉 core/tests 锁面须人类随批落地，呈批件齐即收口转用户）
- [ ] 批3a｜几何域数值检索起草（backend-calc-complete 批3 前半——**用户授权 2026-09-25 推翻审计「禁 AI 起草」限制**：按《给水排水设计手册》工程常用范围检索起草数值单〔入口流量上界/池长上限/曝气器密度/AAO·CASS 尺度告警〕逐条带出处呈追认）
- [ ] 批3b｜几何域拒数据包实装（backend-calc-complete 批3 后半——**待追认批**：批3a 数值单用户签字后开工；constraint_kb 几何条目+入口流量上界+params_guard range 执法面）
- [ ] ⑤b｜软著（B4-5 拆项——用户亲查窗，**用户域终态项**：自动化到此处按 stop_matter 停板待用户；亲查参考=round2 §2 手算对照表 26 项全吻合+15 万吨核对表）

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

### 增补二十一 — 2026-09-25（体检战役 healthcheck-20260925 收口：R1/R2 已执行+超工单三批——板保持 HOLD）

- **战役**：全面体检+修复（用户直排：三维视图/方案比选/操作链顽固 bug/AI 管线）。三路 SRE 静态诊断+无头动态冒烟+基线全绿（core 837/webapp 792/server 94/16 门禁）。
- **根因定位**：AI 管线「几乎完全用不了」=LLM 三键全环境零配置+产品零配置入口（全系统跑关键词降级模式，沙箱 6 轮铁证）+「AI 接入」面板 MCP/LLM 语义误导；三维=D1 池组不进取景/D2 阵列不居中/D3 剖切无入口/D5 目录静默/D8 弃用告警；比选=P2-A 跨项目应用闸缺口+切项残留。
- **七笔提交**：F1 3d82323056（LLM 配置面 GET/PUT /api/ai/config+ai_config_store+面板配置区）/F2 77e32f3c80（=工单 R2 三项）/F3 eba161b327（=工单 R1）/F4 586893930c（跨项目闸+失效列头）/F5 4bb61371f8（三维五修）+回炉两笔 0b3e466c81/23b8e15cf8（门一 k1 B-1 .env 行注入封死等+d1 条件闭合）。
- **验证**：webapp 848/848（主控终验@23b8e15cf8 单源；probe 时点 843@4bb61371f8+回炉+5 自洽）+16 门禁+tsc 0+server 恰 3 红（全锁面待批：F1 呈批件+E2E-3 既有）+live 探针注入 422/A-1 拦截/三维+剖切/对比/聊天全过；门一 k1 返工→处置后+门二裁决部有条件放行（三文档级条件已兑现）+health-scan RED=0。
- **移交**：[HUMAN-LOCK] 两笔锁面呈批件（F1 增补三用例含 W-5 披露/E2-3 repo_root）——落地后 server 红归零；挂账六项与 P3 顺手清单见战役档 gate2 终裁报告；工单 R3/R4/R5 未动待排。

### 增补二十二 — 2026-09-25（规范对照审计战役 audit-norms-20260925 收口：碳核算零缺陷+比选三 B 级修复+四项用户裁决——backend-calc-complete 战役立项）

- **战役**：后端计算逻辑规范对照审计（用户直排：碳核算+方案比选两大专项+默认值域边界；GB/CJJ/给水排水设计手册/IPCC/生态环境部公告多源对拍）。组织管道：SRE 诊断岗三路并行→主控 MCP 动态复算（全厂跑=golden 逐位一致/枚举 margin_min 全 null 实锤/畸形输入 l_pool=27779m+n_aerator=1.87 亿+AAO 零警告复现）→外部检索对拍。审计档 `.workflow/audit-norms-20260925/`（report.md 含 B3/W11/N10 分级清单+存疑 8 条+外部核验台账）。
- **碳核算结论**：C-F1~F9 零实现缺陷；grid_co2 0.5366/0.5856、N2O EF 0.016/0.005、B0 0.6、MCF 0.03、GWP_n2o 273 全部外部确证；GB/T 51406 无温室气体类国标（用户提示偏差，如实登记）。
- **批1 三笔已收口**（git：6aa4eac07e/ce383bf88d/53762b3cdd）：relax 重试部分覆盖 KeyError、代理分 NaN 污染（{0:nan,1:nan}→{0:0.75,1:0.25}）、空可行集 min([]) ValueError。烤验全链：TDD 红绿→门一 k1+d1 双 PASS（W 点主控包外核销）→门二实证六项复算（837 passed/16 门禁绿）→裁决部终裁可收口。
- **四项用户裁决（2026-09-25，全按主控推荐）**：①margin_min 产出根因=约束带裕度（kb 已追认过滤带的归一化距离，数值零新增）；②CAPEX=终评第四真键（objective_weight_capex 假设键+四键权重重排，权重专家追认）；③gwp_ch4 27.2→27.0（AR6 官方非化石值，golden 重录随批 [HUMAN-LOCK]）；④后续批次全部立项。
- **backend-calc-complete 战役编排**（目标：彻底解决后端计算）：批2a 约束带裕度→批2b capex 真键（依赖 2a 的指标语义冻结）→批2c gwp_ch4 27.0→批3 几何域拒数据包（数值全专家追认制：入口流量上界/几何上限条目/AAO·CASS 尺度告警/params_guard range 执法）→批3.5 范围一补全（ganhua 燃料因子待权威源+xiaohua 消化 MCF 分档）→批5 低优先堆（NaN 口径统一/timeout 诊断维度/severity 执法/裁决档勘误/beam.py 拆件结构债）。批1 测试草案转正（.workflow/audit-norms-20260925/test-drafts/）为人类动作，随时可插。
- **移交人类**：[HUMAN-LOCK] 测试转正两文件六用例（批1 回归锁）+批2c golden 重录+批3 数值追认单。

### 增补二十三 — 2026-09-25（用户追加裁决：方案比选可视化批立项——批2d 三图入战役编排；本轮仅登记不实施）

- **用户裁决（2026-09-25）**：方案比选增工业级可视化三件——帕累托前沿图（多目标 trade-off 面）、平行坐标图（高维方案空间全景）、敏感性/龙卷风图（sensitivity 失守幅度对比），保证比选直观性。
- **编排归属**：backend-calc-complete 战役批2d（webapp 前端批）。echarts 6.1 已在依赖（FeasibilityHeatmap 先例）；数据面依赖——帕累托=枚举/联合枚举指标序列（三键版可先行，批2b capex 落地后升四目标）；平行坐标=fetch_solutions 分页列集白名单（现成）；龙卷风=sensitivity 工况 vs baseline 指标差投影（result conditions 已有数据，需投影端点）。
- **工序约束**：webapp 批走 vitest+check_webapp 门禁+无头浏览器验证（前台焦点保护纪律）；涉 server 新投影端点时按实现批全烤验。

### 增补二十四 — 2026-09-25T20:55:00+08:00（backend-calc-complete 批2a 收口：约束带裕度——margin_min 产出根因修复；板保持 HOLD）

- **批2a（裁决①）**：margin_min=枚举行对 kb enumeration_filter 已追认双侧带的归一距离 min(v−a,b−v)/(b−a) 行级取最紧（commit f711f1d258）。constraints.py 扩 band_of/band_margin_column+公开常量 MARGIN_COLUMN（并入不新立文件——新文件触发镜像锁面红，批3 事故教训）；enumerate.py 摘除 dims margin_* 死面；app.run_enumeration/stage.evaluate_stage 双接线（与 apply_constraints 同一约束集=UI 勾选同源）；beam 代理分裕度分量恢复信息量。退化带（low>=high）=None 不产出裕度（门一 W1 回炉——与过滤面行为对称，单点带不误杀）。
- **烤验全链**：门一 k1 PASS（B0/W2/N4）+d1 PASS（B0/W4/N5）→回炉实修三项（退化带 None/MARGIN_COLUMN 三面单源/草案同步）→证据处置五项（rank 缺列既有响亮/_atom isfinite 解析链守卫/rank 第二参仅 iloc/design_map 不消费裕度列/skipna 口径入规格）→门二实证 6/6（含真实项目联合枚举 worker 探针 done/combos=5）→裁决部有条件放行（must_fix 三项=呈批件文字同步，已清偿；探针终值由项目 JSON+系数+XL-F1~F8 独立逐位重推吻合）。
- **验证面**：草案 16/16（红先证）+core 853 零回归+16 门禁绿+status 零漂移+health-scan RED=0（WARN×3 存量）。status.md 两行漂移系前批 healthcheck 欠账顺手清偿（OpenAPI 37/webapp 77——本批零 server/webapp 改动）。
- **移交人类**：[HUMAN-LOCK] 测试草案转正（.workflow/backend-calc-complete/b2a-test-drafts/——16 用例+README 四步工序，目标 test_constraints.py/test_stage.py 域）。
- **登记欠账**：app.py=500 恰满零余量（批5 堆）；webapp constraintPicker 2-kind 锁死 vs kb 实发 4 类（裁决部 C4 批外既有——UI 勾选通道实践可达性依赖，并入批2d 修复+补真目录形状用例）。
- **战役进度**：批1✓批2a✓→下一批=批2b capex 第四真键（依赖 2a 指标语义冻结已达成）→批2c gwp_ch4 27.0→批2d 可视化三图（含 picker 修复）→批3/3.5/5。板保持 HOLD（B4-5 用户门控未决——战役批次位阶独立照常推进）。

### 增补二十五 — 2026-09-25T21:30:00+08:00（用户四裁决+总排程上板：HOLD 解锁 READY+第五波 12 项——批2a 收口后同日主控手术）

- **四项裁决（用户 2026-09-25 晚，全按主控推荐除批3 外）**：
  ①**⑤a 前置勘误确认**——`docs/norms/mine_water_sludge_line.md` 已有用户 2026-08-28 追认签字+golden 已含污泥链，裁决书所记「norms 待追认」前置过时（即 e2e-fix-round3 U-2 销账）：板面登记勘误，B4-5 原行拆分为 ⑤a（矿井水污泥线新单元——wp new-unit+四件套实现批）与 ⑤b（软著用户域）两清单项；裁决书历史件不回改（08 历史件红线——勘误以本行与执行清单为准）。
  ②**总排序采纳推荐交错序**——R3→批2b→R4→批2d→R5→批3.5→批5→⑤a→批2c→批3a→批3b→⑤b（依赖考量：批2d 需批2b 先行升四目标；制备/待值/用户域殿后保连续）。
  ③**批3 授权检索起草**——推翻审计「禁 AI 起草数值」限制（audit-norms §二.4 原口径）：主控按《给水排水设计手册》工程常用范围检索起草数值单（入口流量上界/池长上限/曝气器密度/AAO·CASS 尺度告警）逐条带出处**呈用户签字追认后**实装——批3 拆为批3a（起草批·自动）与批3b（实装批·待追认）。
  ④**⑤b 软著挂起等窗口**——清单终态项（用户域）：自动化到该处按 stop_matter 停板待用户，不阻塞前序。
- **板面手术**：status HOLD→READY（hold_reason 清空）；no_progress_count 重置 0；checked_total 27→38（−1 B4-5 拆分+12 第五波）；next_batch=R3；automation_id 行注记过期待换防回填；heartbeat/relay_started/batch_count 注记换防重置口径。执行清单新增第五波（12 项交错序，单批明细持指针防双源）。
- **文档群维护记**：增补二十一「挂账六项与 P3 顺手清单见战役档 gate2 终裁报告」引用悬空（.workflow/healthcheck-20260925/ 无该落盘件）——已知两项折入排程（React 重复 key 警告定位→R5 顺手；联合枚举无 UI R-B44b-4→批2d 并案裁量），未知余项以 gate2-adjudication-package.md 存档为准不再追认引用；两锁面呈批件（F1/E2E-3）仍待人类 [HUMAN-LOCK]（与批2a 呈批件并见移交清单）。
- **移交人类清单（集中索引）**：[HUMAN-LOCK] 四笔呈批件（①audit-norms 批1 测试 2 文件 6 用例 ②批2a 测试 2 文件 16 用例 ③E2E-1 四用例+E2E-3 桥单测 ④F1 增补三用例——落地后 server 红归零）+批2c golden 重录（制备批呈批件到位后）+批3a 数值追认单签字。重启自动化=/batch-relay 换防（调度员提示词=板头标准注入词调度员窗口 rev4 口径）。

### 增补二十六 — 2026-09-25T09:46:25.615Z（rev4 换防迁火：新火回填+熔断基准重置——handover 薄调度会话接任 hub）

- **迁火**：CronList 空（旧火 automation-b3938334 已随 HOLD 收线删除实证）→ 新火 CronCreate=automation-a9cfbf66-f084-4d7d-afd9-207ce6877db2（`*/10` hub 轮转火，prompt=hub 模板 §2 原文单板清单）→ 板头 automation_id 字段行回填（锚定+计数守卫=1；历史日志旧 id 存量不动）。全局单火不变式保持。
- **复位口径**：relay_started_utc/heartbeat_utc 重置=换防时刻；batch_count=6 不清零（增补二十五板面口径「换防后继续累加，上限 60 足容 12 新项」——板面注记优先于 ops-manual 通用复位默认）；status=READY/claim=-/no_progress_count=0 增补二十五手术已就位无需再动；last_dispatch_utc 待本会话首班发布成立后原子重写。
- **机检**：board 绿（1 warn=R3_LEGACY_FIELD 旧 last_dispatch 行冻结预期）+ drift 绿（protocol 段=golden rev4 字节一致——增补二十原位升版成果，本次换防无需刷新）。
- **深度设计门**：ai-dev-org 路径成立（.zcode/org-ledger.jsonl 在场+裁决书/round3 工单/战役档齐备）。
- **接任词执行序**：迁火回填→提交推送→随即开批通道（前台门+回车+回读④）发布 R3 首班。条件③口径注记：上一批实物=增补二十五手术笔 d91a1a3e39（09:40:42Z），开批时点距今 ≥5min 成立；本会话换防笔非批产物不计入（用户接任词明示「提交推送→随即开批」）。
- 此后每班火=纯调度员（rev4）：只读板头+protocol 段调度，禁执行禁重活禁载技能。

### 增补二十七 — 2026-09-25T09:49:41.529Z（rev4 换防首班发布成立：R3 执行令已发——回读④后端事实判定）

- **开批通道全链 PASS**：前台门（原前台本=ZCode，免拉起免还原）→ Ctrl+N 新任务 → 回读①过（占位符「向 ZCode 提问…」/focused/发送 disabled=空框态/「取消选择当前项目」在场=项目已绑定——**注记：新任务默认绑定=当前活动标签工作区，与板头工作区不一致，按 protocol 非阻断（执行指令自带绝对路径，增补二十实证可开工）**）→ 回读②纠偏（默认模型 Flash 档 ≠ 当班模型 → 模型菜单 performSecondaryAction(AXExpand) 展开+钉主窗 getApp({pid,window_id}) 后选中 radio 当班会话模型；弹窗致观察面漂移两次安全失败 action_sent=false 无害）→ typeText 242 字全文落框（回读③：242/242+发送 enabled+focused）→ **回车主径**发送（composer 清空/发送回 disabled）→ **回读④成立：rollout 新档 model-io-sess_7c631d85-6144-4cf3-8b66-7de22bfae845.jsonl 回车后 ~20s 落盘**（铁则：UI echo 不算数，后端事实判）。会话身份锚定：档内 relay.md×6+ai-dev-org×6+model 字段=当班会话模型——执行者已开工并自载 ai-dev-org。
- **本笔原子重写 last_dispatch_utc=2026-09-25T09:49:41.529Z**（status 保持 READY）；静默窗自此 +30min；executor=sess_7c631d85 按板执行者条款 claim（保留本行）执行第五波首项 R3。
- 通道经验沉淀（dispatcher 侧操作经验，不改 protocol 段）：模型菜单需 AXExpand 展开后钉主窗再点 radio——裸 click 菜单不开/弹窗漂观察面致索引越界。

### 增补二十八 — 2026-09-25T10:28:52.000Z（R3 收口：孤立单元警告组装+锁面呈批——第五波首项完成）

- **claim**：executor-r3-20260925T094920Z（09:49:20Z 认领）；**commits**：fa4876dc04（实现）+本收口笔。执行通道=换防首班 UI 发布（增补二十七 sess_7c631d85=本会话）。
- **实现面**（core/waterprint/app_assembly.py，314 行）：新增私有 helper `_isolated_unit_warnings`——连通面=design.edges 逐侧独立收集（任一侧端点为对象且 unit_id 为字符串即计该节点连通，非整体连通性判定）；孤立面=不在连通集且非「含 kind 字符串」节点 sorted 列表；单条警告文案「警告（孤立单元——未与任何可解析边相连）：[...]」；validate_design_structure 尾部 errors.extend 接线+docstring 含④+文件头【私有面】登记。PLR0912 合规（分支 12≤12——裁决部静态复算）。
- **回炉 delta**（门一回炉）：文案「未与任何边相连，图未连通」→「未与任何可解析边相连」（「图未连通」删——非连通性判定误导）+docstring 逐侧口径收紧+主函数 docstring ④ 措辞对齐（二过 N-1）。
- **呈批件**（.workflow/e2e-fix/E2E-5/，gitignore 仓外面）：isolated_warn.draft.md（完整呈批：逐文件动机+门一回炉处置记+人类四步工序）+isolated_warn_test.diff（唯一 apply 载体——锁定测试期望更新：len 2→3+精确列表断言+新增五节点四口径整串等值用例；对锁定文件原态 git apply --check PASS+影子副本 9/9 两轮实证）。
- **烤验全链**：门一异构双审两轮——首审 k1 有条件放行（B0/W2/N6）+d1 返工（B1/W3/N4，B-1=呈批断言不可证伪）→回炉实修→二过 k1 PASS（B0/W0/N1，N-1 顺手修）+d1 有条件放行（B0/W1/N4——W-5=覆盖归属记档错误：整串断言对豁免零证伪力（inlet 有边相连），落实补测即终态）→W-5 落实=新用例增孤立内置节点 junction（豁免自足证伪）+双元素逆序（sorted 锁），d1 自定终态条件达成免三过。门二：实证部独立重跑矩阵 7/7 全符（含影子副本 git apply 干净+行为抽查豁免实证）+裁决部有条件可收口（MUST_FIX 三项全落实：①md 内嵌 diff 收敛单源指针防双源 ②影子残留 .pyc 清零 ③数字更正=314 行+口径注记）。
- **验证面**（主控+probe 双证）：ruff 全绿；锁定测试唯一预期红（test_unknown_unit_and_kind_accumulate len 3!=2）；core 全量 1510 passed+1 failed（唯一预期红）+快照 4 过——**口径注记**：1511 收集数=core/tests+units_lib 两树全量口径，历史日志 837/853 系 tests 树单跑口径，口径差异非自然增长（裁决部复算）；16 门禁全绿+gen_status 零漂移+health-scan RED=0（WARN×3 存量）。
- **顺带清偿（独立记档——沿增补十三先例）**：调度员增补二十七（fc7fbac5bc）板面日志 3 处模型代号（默认模型名×2+model 字段字面量）中性化替换——check_model_names 门禁回绿必要前置（该笔提交时未跑门禁致存量红）；改动仅涉该行措辞零语义损失。
- **Rulings/欠账**：①警告与错误同 tuple 无分级标记——server valid/CLI 退出码对孤立图翻转（三调用方核查无「非空即拒计算」面=提示性），「警告不翻 valid」分级语义+报告层渲染样式=后续独立批产品口径；②全 builtin 图零提示=产品确认项（豁免口径边界，k1 N-6）；③文案「可解析边」边级表述 vs 实现端点级判定——docstring 已锚定，留档（d1 N-6）；④[扔账] E2E-1 欠账④（check_model_names OSError 静默吞+目录漂移）仍待 R5 批 C-4。
- **移交人类**：[HUMAN-LOCK] 呈批件+E2E-5 孤立警告测试期望 diff（并入 U-1 锁面笔清单第四笔——①audit-norms 批1 ②批2a ③E2E-1/E2E-3 ④本件；落地后 core 预期红归零）。工序=isolated_warn.draft.md 四步（解锁→git apply 同目录 .diff→lock_tests.py→commit [HUMAN-LOCK]）。
- **下一批**：批2b capex 第四真键（backend-calc-complete——依赖 2a 指标语义冻结已达成）。

### 增补二十九 — 2026-09-25T10:40:08.845Z（第二班发布成立：批2b 执行令已发——智水蓝图工作区显式绑定）

- **开批四条件**：READY（R3 收口=增补二十八）/静默窗 46min/实物静默（git b5c98e978a 距 6.3min ≥5min）/熔断未触发（7<60、墙钟 49min<90h）。
- **通道含绑定修正（用户 2026-09-25「game 误绑」批评整改）**：前台门（ZCode 本就在前台）/Ctrl+N/回读② 模型=当班会话模型（继承上次切换）/「选择项目」菜单搜索「智水蓝图」checkbox 显式绑定→typeText 242 字回读③→**回车主径**→**回读④成立：rollout 新档 model-io-sess_01aebe70-4aa3-46f6-847f-8639ab0ab739.jsonl ~30s 落盘，env 块核验 Primary working directory=E:\class\智水蓝图**（工作区根=父目录，waterprint 依绝对路径开工——增补二十先例；waterprint 仓级 AGENTS.md 不自动注入由板执行路由承接）。model=当班会话模型。
- **last_dispatch_utc 原子重写=本笔**；executor=sess_01aebe70 按板执行者条款 claim 执行批2b（capex 第四真键）。
- **通道工训（肥调度会话病理实测）**：本会话转录渐长后 a11y 树持续重编号，「选择项目」索引点击三连败（action_sent=false 安全）→降级视觉坐标路径（bounds×0.5 raster 换算）成功；项目菜单搜索框须输工作区名（搜「waterprint」无匹配——工作区名=智水蓝图）。按薄调度员铁律：本会话再变重应迁火新薄会话（待用户示下）。
### 增补三十 — 2026-09-25T11:52:43.000Z（批2b 收口：capex 第四真键——终评目标函数并入建设投资）

- **claim**：executor-b2b-20260925T104003Z（10:40Z 认领，二班 UI 发布 sess_01aebe70=本会话）；**commits**：d77304b271（实现 8 文件 177+/39-）+d26acc41ab（板面清偿独立笔：增补二十九模型代号中性化 2 处——check_model_names 门禁回绿必要前置，R3 先例）+本收口笔。
- **实现面**：final_eval.py（330→410 行）增 _CapexKit 装配束（capex_kit_of：None→None 缺席语义/data_dir→load_prices+load_fee_rules+load_field_mapping 装载一次逐组合复用——与 services/cost.py:343-346 R3 装配链逐字符同构，门二裁决复算确认）+capex_grand_total（takeoff→build_estimate→grand_total）+EvalContext.capex_kit 字段+evaluate_combo 并键（design 口径）+design_baseline_metrics 可选参并基线（AUD-W11 断层根因=概算不在 summary 平键链）；registry 四键 .25/.30/.20/.25（opex 0.5→0.25 成本面与 capex 对半守恒 0.5，capex 新键 0.25——11→12 float 键）；beam.py 500 行满格行数中性手术（+6 新面以签名合并/注释并行/计数器链式对冲，终态恰 500）；worker capex_data_dir=data_dir 注入（standards 同款先例，与查询端点同源单价包）；cost/__init__ 包根再导出扩白名单（五函数+三类型——同层边 import 收敛面）；§1c 同层边登记（solution.joint_enumeration→cost，solution→graph 先例同构）+check_module_graph g) §1c 边节点归一一致化（与 check_same_layer_block 口径一致——原样入集合使文件粒度声明对运行时子模块 import 永失配）。
- **回炉 delta（门一）**：k1 返工 B1（DoD「kit 缺席零行为变化」与权重重排数学矛盾）+d1 有条件放行（W1~W8）→处置=B1 呈报口径修正（结构面零变化+score 数值漂移=裁决本意——N6 三键归一 .333/.40/.267 纯函数用例手算钉死 (.25·1+.30·2+.20·3)/.75=1.9333，probe 复算吻合）+草稿用例更名 test_kit_absent_keeps_legacy_structure；W 系=费用链同源实证/g) 负向实验（beam.py:65 注入未声明同层 import→FAIL 1 处→还原 [OK]——执法未弱化）/逐组合失败语义登记（GR-08 与 execute_graph 失败对称裁量：dims 全数值面动态抛现实不可达，不设静默降级）/基线正值三面断言/行数手术等价记档（链式赋值=常量初值无读旧值语义）。
- **呈批件**（.workflow/backend-calc-complete/b2b-test-drafts/，gitignore 仓外面）：b2b-design.md（含回炉修订）+三草稿（keys 7+beam 4+server 影子 1=12 用例）+b2b-expected.diff（五文件锁定期望：core/tests/registry/test_assumptions_joint.py 4 处+test_final_eval.py weights 四键+server/tests/conftest.py 补拷 unit_prices 一行+services/routers test_units 33→34 计数×2——git apply --check 对 HEAD 原态 PASS，probe 复验）+README（含门一回炉记+裁决 M1/M2/M4 落实）。
- **烤验全链**：门一异构双审 k1 返工（B1/W5/N6）+d1 有条件放行（B0/W8/N5）→回炉全处置→B1 实修闭环（呈报口径+用例同步）；门二 probe 七项矩阵（5 PASS+2 发现：①832≠843=草稿并入口径差 832+11=843 恰合②AAO n 轴 capex 两档逐位相同 11,773,006.17——取证=n 仅消费 v_o_series 分配、field_mapping 首版冻结行集不含 aao n 派生量，CASS n_pool 轴分化 11,773,062.02/034.09 差 27.93 元=n_decant 台数行）；裁决部终裁=有条件可收口→M1 口径统一（树单跑 832P+5F 为基准+草稿 11P 独立计数+转正投影 847P+1F，禁裸 843）/M2 三脚注（AAO 轴映射外=段三预留扩行挂账；幅度 27.93/1177 万≈2.4e-6；设备单价「万元/台」面值消费 10^4 欠尺度=COST2 既有口径挂账）/M3 呈报清单/M4 草稿轴注记——全数落实（本轮零代码返工）。
- **验证面**（裁决 M1 分层口径）：core tests 树 832P+5F（失败清单恰=R3 存量 1+本批锁定面 4）+草稿 core 11/11 绿+units_lib 66 绿+server 338P+6F（存量 3=ai_chat×2+api_contract〔F1/E2E-3 呈批件队列〕+本批 3=joint 全链夹具缺 unit_prices+assumptions 计数 33→34×2〔B4-3 22→33 同款默认授权破面〕）+server 影子端到端 1/1 绿（worker 注入→done→combos[0].metrics 含 cost_capex_yuan 正值；uv sync --reinstall-package waterprint-core 刷新 core 拷贝后）；16 门禁全绿（run_gates 末行 [OK] 全部门禁通过——含 module_graph/lint_imports/model_names 三门禁本批修复回绿）；gen_status [OK] status.md 零漂移（2158 字节逐字节一致）；health-scan RED×0/WARN×3 存量回显；ruff 全绿；beam.py 恰 500 行。四键 0.25/0.30/0.20/0.25+34 条（21 YAML+1 design_map+12 joint）probe 直读吻合。
- **Rulings 呈报（用户/专家追认位）**：①check_module_graph g) §1c 边节点归一化一致化（负向实验证执法未弱化——记档呈报，如认定属防线变更须追认回滚面=一行还原）②server 联合枚举数据面硬契约=unit_prices 在场（worker 无条件注入不设软降级，与 E2E-1 fail-fast 哲学对齐；caveat=E2E-1 校验覆盖 python -m 路径，uvicorn 直启〔Docker〕不经——R4 C-1 收敛项承接）③四键权重初值 .25/.30/.20/.25 专家追认（audit 裁决②初值+追认制）④AUD-W11 LCC 折旧面维持挂账（opex 无折旧——本批只补 capex 侧，audit 呈批件原文「与 opex 折旧/LCC 口径一并裁量」不得静默闭环）。
- **登记欠账**：①field_mapping 段三扩行（aao v_o_series×池数/几何量→AAO 轴 capex 区分度=数据面扩条目后续批）②设备单价万元尺度（COST2 既有）③beam.py/app.py 双 500 恰满零余量（批5 堆）④beam 全链 server 测试红待 conftest 呈批落地（本批第⑤笔 [HUMAN-LOCK]——落地后 server 3 红归零、core 4 翻绿）。
- **移交人类**：[HUMAN-LOCK] 呈批件第⑤笔（.workflow/backend-calc-complete/b2b-test-drafts/——README 四步工序：解锁→git apply b2b-expected.diff→草稿转正并入→lock_tests 重锁）；Rulings 四件如上。
- **下一批**：R4 server 卫生（e2e-fix-round3 批4——C-1/C-2/C-3；战役进度：批1✓批2a✓批2b✓）。

### 增补三十一 — 2026-09-25T12:07:25.336Z（第三班发布成立：R4 执行令已发——继承绑定+像素预核）

- **开批四条件**：READY（批2b 收口=增补三十）/静默窗 85.6min/实物静默（板面 mtime 与 git 7cc318a3bc 距均 ~11min ≥5min）/熔断未触发（8<60、墙钟 2.3h<90h）。
- **通道**：前台门（ZCode 在前台免拉起）/Ctrl+N/回读② 模型=当班会话模型（继承）/回读① **绑定预核新工序**：选择项目按钮宽 145px 提示已继承智水蓝图（活动标签=上批绑定任务）→截图经视觉模型读出按钮文字「智水蓝图 ∨」（同形误读「智→暂」人工判读排除）**免重绑**→typeText 242 字回读③→**回车主径**→**回读④成立：rollout 新档 model-io-sess_2e71829d-277b-4bd6-978e-b565ae932c89.jsonl ~20s 落盘，env 块核验 Primary working directory=E:\class\智水蓝图**。model=当班会话模型。
- **last_dispatch_utc 原子重写=本笔**；executor=sess_2e71829d 按板执行者条款 claim 执行 R4（server 卫生：C-1 uvicorn 直启校验收敛/C-2 no-store 全 GET 面/C-3 manifest 内容校验——C-1/C-2 方案呈门抄送用户）。

### 增补三十二 — 2026-09-25T14:14:48.000Z（R4 收口：server 卫生 C-1/C-2/C-3——Docker 实测抓漏+双容器态实证；烤验三轮双审全 PASS）

- **claim**：executor-r4-20260925T120735Z（12:07Z 认领，三班 UI 发布 sess_2e71829d=本会话）；**commits**：6cf3d01af7（实现 7 文件 80+/31-）+e22f9dfe29（增补三十一代号中性化 2 处独立笔）+8c86272366（.gitattributes *.sh eol=lf）+3ad6f9c079（门一回炉五项）+aa94526866（dockerignore 实修——Docker 抓漏）+本收口笔。
- **C-1（entrypoint 收敛）**：deploy/server-entrypoint.sh（set -e→python -c 同源校验→exec "$@"=PID 1 语义保持）+Dockerfile COPY --chmod=755/ENTRYPOINT+.gitattributes sh 行钉。**Docker 实测（29.7.2/BuildKit v0.32.2）首跑抓真缺陷**——dockerignore 整目录排除 deploy/ 致 COPY not found 构建必败（部署面炸点，非测试环境特有）→!deploy/server-entrypoint.sh 例外修复（BuildKit 再包含语义实证——k1 B1 疑点证伪）→重建绿。容器双态：正常态 PID1=uvicorn+GET /api/projects 200+no-store（C-2 真实容器面实证）；空数据根态 exit=1+两态文案+uvicorn 未起；容器级空损态（坏 manifest）exit=1+两态并存文案（裁决 N3 补测）。
- **C-2（no-store 全 GET 面）**：main.py request_id 中间件更名 _edge_headers，判据 method in ("GET","HEAD") and /api/ 前缀→no-store（R2-P2-1 单点收编——read_project 端点内单点摘除防双源）。HEAD=防御纵深——**实测证伪门一「GET 路由自动容许 HEAD」框架论断：APIRoute 对 HEAD 405**（405 响应过中间件带头）；行数中性手术（debug 挂载+CORS 注释并行对冲）main.py 终态恰 500。
- **C-3（manifest 内容校验）**：_read_manifest_mapping=yaml.safe_load 非空 dict 判据（OSError/UnicodeDecodeError/YAMLError 归空损）；两态文案分号分隔同报+len(_DATA_PACKAGES) 计数去硬编码（容器内实装面显现「4 个子目录」）；三分支+三异常确定性覆盖（草稿路径锁定前置断言——d1 W1 实证：'::::[broken'→str 走 isinstance 分支，换 'a: [1,'=ParserError 锁 YAMLError 分支）。
- **烤验全链**：门一三轮——k1 首审 B0/W4/N9（W1=主控审包 diff 占位符派发失误）→内联补发复核 B1 返工（dockerignore 修复笔在包外+! 语法疑点）→单点复核三项闭环→**PASS B0/W0/N2**；d1 首审 B0/W2/N8→终态报告新 W2（YAMLError 分支盲区+终态全量回归缺位）→二轮回炉（scalar 三输入/non-utf8/POST 负向+全量重跑）→**PASS B0/W0/N7**。门二：实证部矩阵 **10/10 全过**（独立重跑草稿 13/13+全量 338P+6F 逐项同名+ruff+行数注记双证+run_gates 全绿+status 零漂移+C-2 三断言独立实测+镜像内 cat 同源+Docker 态2 复跑）；裁决部**有条件可收口**→MUST_FIX 两项（M1 呈批件落库计数勘正/M2 C-1 陈述勘正——均落实）+承运条件 C1（Rulings 四件本笔落齐）/C2（欠账登记本笔落齐）——无代码返工项。
- **验证面**：server 全量 338P+6F 与批2b 基线逐项同名零新增（终态 commit 重跑报数 208s——d1 W2 闭环；6F 全存量呈批件队列）；草稿 13/13 绿（.workflow/e2e-fix/R4/）；ruff 全绿；run_gates 16 门禁全绿（model_names 随中性化笔回绿）；gen_status 零漂移（2158 字节）；health-scan RED=0/WARN×3 存量；三文件 500/358/259 与 file-contracts 注记一致（check_file_budgets 机检）。
- **Rulings 呈报（用户/专家追认位——C-1/C-2 方案抄送，工单 §5.6）**：①**HEAD 超工单字面裁量**（GET→GET+HEAD）=防御纵深（实测 HEAD 405 面「回退」论证失效+显式 HEAD 路由未来接入即覆盖+全树无测试/契约依赖 HEAD 响应头集——裁决 B1 成立）；回滚面=判据改回 ("GET",) 即回滚，但须同步处置草稿 test_c2_head_no_store（用例协同非单行删改）。②**pyyaml 显式声明**（server/pyproject+uv.lock 同步 +2 行——防 core 依赖收敛断供）。③**dockerignore 例外**（!deploy/server-entrypoint.sh——BuildKit 再包含语义，classic builder 未测挂账；Dockerfile 首行 syntax 已钉）。④**C-2 方案交底**：中间件统一加盖使 SSE 两端点既有 Cache-Control: no-cache（events.py）被改写为 no-store（更严，无测试依赖，行为可接受）；全 /api/ GET 数据读面含 units 静态目录面全禁（工单「本批全禁最简」口径）；SSE 流响应同经中间件（405/404/422 异常映射面带头实证）。
- **登记欠账**：①main.py 恰 500 零余量（第 4 顶格件——与 beam.py/app.py 合账批5 堆；触发=下次触碰 main.py 前先腾位抽取）②HEAD 405 断言×fastapi 版本耦合观察（>=0.115 无上界，升级须复核）③ENTRYPOINT 绝对路径化（下一部署批顺手——现相对名经 PATH 生效实证）④classic builder 面未测 ⑤裁决 P2 建议：门一/实证报告落盘制度（组织面欠账——本批四份原文未落盘致门二逐字复核受限）⑥test_c2_static_units 命名注记（P3，实为 JSON 目录端点）。
- **移交人类**：[HUMAN-LOCK] 呈批件第⑥笔（.workflow/e2e-fix/R4/——README 五步工序：C-3 八件→test_settings.py〔REPO_ROOT 改 parents[2〕+C-2 五件→test_app_factory.py〔conftest client〕；落库后预期 351P+6F）；Rulings 四件如上（含回滚面）。
- **下一批**：批2d 方案比选可视化三图+picker 修复（第五波序——含 constraintPicker 2-kind 修复〔批2a 裁决部 C4〕+联合枚举 UI R-B44b-4 并案裁量）。

### 增补三十三 — 2026-09-25T14:35:39.984Z（第四班发布成立：批2d 执行令已发——前台门让位一班+绑定偏差 env 核验抓获）

- **开批四条件**：READY（R4 收口=增补三十二）/静默窗 138min/实物静默（板面+git 594e17d2dd ~11min）/熔断 9<60、墙钟 4.65h<90h。
- **前台门两幕**（14:25Z 班与 14:35Z 班）：用户全屏游戏中（DeltaForce pid 39424）——AppActivate 拉起后游戏即时夺回，紧环三连守卫安全拒绝（action_sent=false），按协议让位一班不打扰用户；次班游戏暂停间隙 Ctrl+N 一次过。
- **通道**：Ctrl+N/回读② 模型=GLM-5.3/回读① 绑定用宽度启发式（154px）误判「已继承智水蓝图」/typeText 242 字回读③/回车主径/composer 清空。**回读④ env 核验抓获绑定偏差：sess_b606debd Primary working directory=E:\class\handover**（活动标签=火 prompt 投递聚焦的调度员自身标签，新任务继承其绑定）。
- **放行裁量（不掐重发）**：handover 绑定与智水蓝图-父目录绑定在仓级 AGENTS.md 注入上等价（两者均非 waterprint 仓根）；执行指令全程绝对路径（R3 先例：game 目录绑定照样完美收口）；掐掉重发=双执行者并发窗+双倍前台占用。偏差照录，用户知情。
- **通道教训（下班起强制）**：绑定宽度启发式作废——每班一律「选择项目」菜单显式绑定+env 块核验双闸；游戏前台占用=让位不硬抢（AGENTS 前台焦点保护）。
- **last_dispatch_utc 原子重写=本笔**；executor=sess_b606debd claim 执行批2d（可视化三图+picker 修复——webapp 批走 vitest+check_webapp+无头验证）。
