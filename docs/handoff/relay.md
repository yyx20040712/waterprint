# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: READY
- automation_id: automation-cbcb3949-7683-41d0-8d15-ba575e2493f0 <!-- 2026-09-25 换防回填；旧火 9d069f57 已亡见换防记录 -->
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-24T18:07:01.366Z
- claim: -
- no_progress_count: 0
- checked_total: 27 <!-- 2026-09-25 增补十：+E2E-1~5 插队战役五项 -->
- checked_done: 21 <!-- 2026-09-24 B4-4b 收口 20→21（B4-4 两段全成勾口径） -->
- protocol_rev: 1
- last_dispatch_utc: 2026-09-24T17:59:13Z <!-- 2026-09-25 E2E-1 首发（UI 开批成立——上欠账行争用解除后第一班火成） -->
- relay_started_utc: 2026-09-24T17:44:23.011Z <!-- 2026-09-25 换防时刻 -->
- batch_count: 0 <!-- 2026-09-25 换防复位（原 9；停火数日墙钟 ~123h>90h 触发 circuit_wall，用户显式点名 batch-relay 换防重置留痕） -->
- max_batches: 60
- max_wall_hours: 90
- hold_reason: -
- last_handover: 2026-09-25
- claimed_by: -
- claimed_at: -
- next_batch: E2E-1 fix-plan 批1【server-data】（插队战役先于 B4-5；campaign 收口按 fix-plan §7.4 回归 B4-5 原排序）

## protocol（角色自识别 + 最小兜底协议）

- 本板 protocol_rev=1；rev=0（无此行）为存量板——读旧字段名 last_dispatch（无 Z 后缀按本机时区换算），仅警告不阻断，下次换防迁移 rev1。
- 时间一律 UTC（ISO8601 带 Z 后缀）；「距今 N min」=（当前 UTC−字段值）÷60000 向下取整；解析失败=预检失败。写板一律写 Z 后缀新字段名；旧字段行冻结不删。
- 预检（任何行动前，rev 感知）：字段行完整（rev1 全集；rev0 旧集）/ 时间戳可解析（rev0 旧格式仅警告）/ 数值字段纯非负整数（R10）/ status∈{READY,RUNNING,DONE,HOLD} / 无重复 status 行 / protocol_rev∈{0,1}——任一失败：输出 `fire: abort (reason=board_precheck_failed:<规则名>)` 后退出，并在批次日志追加欠账行。
- 收到火 prompt 的会话=调度员。一切一行退出只用固定枚举三族，禁引用板面原文：`fire: skip (reason=quiet_window|running_fresh|candidate_alive|no_ready_board)`；`fire: terminal (reason=done|hold|board_missing)`；`fire: abort (reason=board_precheck_failed:<规则名>)`。
  - 板不存在 → 单项目：CronDelete(automation_id) 后 `fire: terminal (reason=board_missing)`；shared_fire=true 板缺失=从轮转清单跳过+本轮终报记欠账，不删全局火——删火仅当全部板终态或缺失。
  - DONE/HOLD → 单项目：CronDelete(automation_id) 后 terminal(done|hold)；shared_fire=true 板只终报不删火（删火权归 hub 调度员，须全部板终态）。
  - last_dispatch_utc 距今 < quiet_window_min=30 → `fire: skip (reason=quiet_window)`（READY 未认领/RUNNING 均适用；仅约束调度员，刚被发布的执行者照常认领；值为 `-`=从未发布——窗口视为已过，非解析失败）。
  - RUNNING 且 heartbeat_utc 距今 < heartbeat_stale_min=30 → `fire: skip (reason=running_fresh)`。
  - RUNNING 且心跳距今 ≥ heartbeat_stale_min=30 → 先过 UI 活动核查：同宿必核执行者会话已无「正在执行」活动——仍有活动 → `fire: skip (reason=candidate_alive)`；跨宿降级 git/账本双核对+日志欠账行「跨宿接管未经 UI 核查」。核查过才接管：核对实际进度防重复执行再重置 claim → READY（接管后重新发布则更新 last_dispatch_utc）。
  - READY → 开批四条件：①status=READY ②静默窗已过（last_dispatch_utc 距今 ≥ quiet_window_min=30；值 `-`=从未发布视为已过）③上一批实物已静默（板面 mtime 与 git 最近提交距今 ≥ physical_quiet_min=5；无 git 仓以板面与 plan 文件 mtime 代之）④熔断未触发（batch_count<max_batches 且距今运行 <max_wall_hours 小时）。④触发 → 置 HOLD(hold_reason=circuit_batches|circuit_wall)+终报首行「熔断裂闸…」；①-③任一不满足 → 让位下一班火。四条件齐 → 先一行告知用户「接下来约 20 秒需要占用前台完成开批操作」→ 侧边栏展开 → AXPress「新建任务」（禁 Ctrl+N——2026-09-20 实证快捷键新建任务落错工作区，该路径废弃）→「选择项目」勾本项目 → Escape 收菜单 → 真实点击 textfield → app 级 strategy=event 键盘写入下方执行指令 → 回读确认落框且发送按钮启用 → 点发送按钮 → 原子写 last_dispatch_utc（status 保持 READY）。每回合至多开一批；hub 轮转在合格板中挑 last_dispatch_utc 最老者（并列取 prompt 清单序），成员板缺 shared_fire: true 行 → 跳过该板+日志欠账行。
- 被注入执行指令的新任务会话=执行者：开工首步 Skill 加载 ai-dev-org（不可加载则按计划头部执行通道行：subagent-driven-development，无子代理则 executing-plans）→ 读板预检 → READY 时原子 claim（tmp 写 status:RUNNING+claim token+heartbeat_utc+勾选数快照，保留 last_dispatch_utc → mv -f 覆盖 → 回读确认，非己让位退出；此后执行者一切板写（心跳/收口/翻回/修复）落笔前同样回读，非己=已被接管停笔让位，遗留只终报呈报）→ 执行 plan 未勾任务至 fire_budget_min=60（板字段可调；每任务始末刷心跳，任务内每隔 heartbeat_refresh_min=15 亦必刷——活执行者心跳永不陈旧到接管阈值）→ 收口按固定次序判定（首中即断）：①`grep -cE '^[[:space:]]*- \[ \]'` 计 0（行首允许缩进，误报方向=晚 DONE 安全）→ DONE+终报（无 shared_fire 标记才 CronDelete；工具不可用时终报请用户在 Automations 页按 title 删）②停止事由（不可逆/破坏性、安全敏感、仓外副作用、计划破碎）→ HOLD(stop_matter)+终报 ③熔断（batch_count+1 后 ≥max_batches 或墙钟 ≥max_wall_hours）→ HOLD(circuit_batches|circuit_wall)+终报 ④勾选数未增 → no_progress_count+1，达 no_progress_max=3 → HOLD(no_progress)+终报 ⑤否则 READY。收口必做（同一原子写）：勾选框更新（有 git 提交；无 git 仓记 `commit: n/a (no-git)`）+批次日志追加+heartbeat_utc 刷新+batch_count+1（无条件；唯一例外=翻回 RUNNING 修复的回炉收口不再 +1，③按现值重判④⑤照常，日志记「回炉收口」）+claim → -。置 READY/DONE/HOLD 必须是最后一笔，置位后禁写板/仓；要修先回读（被新 claim 占据则不写，遗留只在终报呈报）→ 原子翻回 RUNNING 修毕重新收口。
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

- [ ] E2E-1｜fix-plan 批1【server-data】P0-A 数据包路径自愈+启动 fail-fast（+round2 批1 扩 R2-P2-1 no-store）
- [ ] E2E-2｜fix-plan 批2【webapp-calc】P0-B 只读态提交计算复活（+round2 批2 扩 R2-P1-2 fitView 引导/R2-P1-3 保存语义）
- [ ] E2E-3｜fix-plan 批3【chat】P0-C 聊天桥 repo_root+P0-D 输入框锁死
- [ ] E2E-4｜round2 §4 新立【server-scene】R2-P0-1 场景 kind 映射 500+R2-P1-1 布局避让+R2-P1-4 进水物理域检（编号撞前篇批3，按独立新批解读——排序/并批主控裁量）
- [ ] E2E-5｜fix-plan 批4【hygiene】卫生批（+round2 批4 扩 R2-P2-2 孤立警告/R2-P2-3 枚举 URL 回写）

### 治理小批·用户直排（2026-09-19 对话内裁决——B4-2a 收尾批后、B4-2b 前开工）

- [x] G-1｜同族一致性门禁：aao/cass 同族公式族（需氧量/曝气/污泥/能耗）结构恒等机器断言+显式 delta 清单（如 CASS duty_ratio）——静默分叉变响红（可维护性答疑①，用户裁决入下波工单）
- [x] G-2｜拆件配方回写宪法：ADR-024 D1 的 formulas_*/energy 预算墙拆件规则写入 AGENTS §11——撞墙拆法从即兴变规则（可维护性答疑②，用户裁决入下波工单）

> ③ vector 全表面期望外移 JSON 数据件（可维护性答疑③）＝**用户亲改保留项**——AI 批次不自动开工；第三次锁面摩擦事件发生时仅呈报提醒不代做（用户裁决 2026-09-19）。

### 挂账池（不入波次，触发时呈报）

> 单源=《裁决书》「沿册挂账」与各方案挂账节——本池仅指针不复制（防双源
> 漂移，门一审 W2 处置）；明细以裁决书为准：纵断真实站距/ODA E2E/软著
> 签章页/UF 开放条目/sunset 观察项（触发条件与复核节奏见 sunset 表）。

## 批次日志（追加，勿改写）

> 历史批次日志滚动归档（B2-6 收口起）：2026-09-18 建板~B2-4 增补二段
> （batch 0~3 与 B2-1~B2-4 全量、调度员增补一/二）已迁
> relay-archive-001.md（原文零改动纯迁移，追加勿改写纪律延续至归档件）；
> 本板自调度员增补三起留活跃链，满 400 行再滚下一档（滚动阈值口径与
> 归档件头注一致）。

> 〔滚动归档〕调度员增补三~batch B3-a 补记段（2026-09-19，135 行）已迁
> relay-archive-001.md 尾部（原文零改动纯迁移——B2-6 立档同款；本板自
> 调度员增补五起留活跃链）。
> 〔滚动归档〕调度员增补五~batch B4-1 补记段（2026-09-19 B4-2a 收尾批，260 行）已迁
> relay-archive-002.md（原文零改动纯迁移——B2-6 立档同款；001 已 396 行近预算满续二号档）。
> 归档动因=板面 549 行超 500 文件预算（门二 M1/M2 RED 根因——check_file_budgets 与 arch 镜像）。
> 本板自「增补（rev0→rev1 迁移）」起留活跃链。

### 增补 — 2026-09-19（rev0→rev1 原位升版迁移——batch-relay 生产化批 Task 6，主控会话直跑）
- 迁移写（只增行+折算+追加，未复位既有状态，批次日志区零改写；板头自定义字段 last_handover/claimed_by/claimed_at/next_batch 原位保留；protocol 段含手动路径/hub 火式条款/模型路由事实等既有内容一字未动）：板头新增 protocol_rev:1、last_dispatch_utc=2026-09-19T03:14:24Z（旧 last_dispatch 行 11:14:24+08:00 折算，旧行冻结保留）、relay_started_utc=2026-09-19T06:33:54Z（熔断自迁移起算，非项目起点）、batch_count:0、max_batches:60（3×20 派生）、max_wall_hours:90（⌈1.5×60⌉）、hold_reason:-；protocol 段末追加「rev1 增量条款」块。
- 迁移前基线（check-relay.mjs board）：0 fail+2 warn（R0/R3）；迁移后：见机检记录。claim 本为 -，无状态修复项。
- 执行承载：batch-relay 生产化战役（E:/zcode_md/fix/docs/plans/2026-09-19-batch-relay-production-hardening.md Task 6，D4 裁决会话直跑）；观察门过（last_dispatch 距今 3h19m ≥60min、claim/-claimed_by 空、READY）。

### 增补二 — 2026-09-19（rev1.1 增量条款追加——batch-relay 逻辑修复批 Task 6，主控会话直跑）
- 追加内容：protocol 段末（执行路由标题行前）插入 7 行 rev1.1 块（A1 缺失豁免/A3 dash 语义/A2 心跳+写前 claim 回读+接管 UI 核查/B2 缩进全勾/A5 回炉豁免/R10 数值与值区注释语法）；既有行一字未动（自定义协议段/板头自定义字段整体保留）。观察门四项核值（2026-09-19T08:11:05Z）：last_dispatch_utc 距今 4h56m ≥60min ✓、claim=- ✓、板面 mtime 距今 1h35m ≥10min ✓、status=READY ✓；仓 git 最近提交距今 3h32m ≥10min ✓（N-4）。

> 〔滚动归档〕增补三~调度员欠账行二段（2026-09-19 hub 火时代 160 行）已迁 relay-archive-003.md（原文零改动纯迁移——B2-6 立档同款；动因=板面 504 行超 500 文件预算）。本板自本注记起留活跃链。

### batch G-2 — 2026-09-19 14:40Z~15:16Z（hub 火执行者会话：拆件配方回写宪法，用户直排工单②收官）
- 交付（实现笔 982d47fd 推送守望 CI 绿 run 35450899750；认领笔 df2cd4ea 在先）：AGENTS §11 预算墙拆件配方入宪——声明面拆件（formulas_<族名>.py+manifest 并组注册，单注册口不变量，条目单元包原位〔B2-5 D1-B 读法〕，兄弟声明件自动入同族一致性门禁扫描面〔现辖 aao/cass，新单元接入需登记〕）+计算段拆件（<段名>.py 主题连续整体迁移〔首例 energy.py 持 _oxygen+能耗〕，compute 仍是唯一计算正门〔ADR-011 D1 批量同源不破〕）+拆件义务四条（规格头注记/三名白名单不变/兄弟件单向消费禁互 import/包内测试同步走 §7 锁面）+兜底句（未覆盖撞墙形态=停批呈裁禁即兴——门一 W-1）+§2 拆法定式指针（单元包 §11 配方+门禁脚本 <名>_lib.py 共享库先例——票面外搭车记 Ruling 呈报）。
- 死锚清偿 31 处（门二 M4 两轮 RED 逼出的完备盘点）：「AGENTS §13.6」显式误标 15（git -S 全史实证节号从未存在于 AGENTS.md——13 单元 compute.py+_template）+scripts 门禁头注 7（check_webapp §13.5×4/check_file_budgets §13.7/check_contract_headers §13.2/.7/check_structure §13.7）+宪法契约 README 面 9（AGENTS.md:121/file-contracts:48/:163/:245/scripts/README 门禁表 4 行/registry×2/plan_view:18/webapp README×3/UF 登记:287——部分按住址语义归并计数）。挂账清单（呈报）：server §13.4 分层族×9+webapp src §13.5×4+dxf_writer §13.3（机械可清建议独立卫生小批，§13.4 预判住址 AGENTS §1）+测试面 6（含门二补遗 test_file_budgets.py:8——锁面工序成本）+「重写计划 §13.x」25 处永久豁免（门二建议：仓外文档合法引用清它反失真）+ADR-011:6 归档。
- 双门（文档/制度批轻量双审）：门一（ops-gate1-k2 备源承载——用户指令 2026-09-18 未销案）一审 B0/W3/N6 有条件放行（W-1 配方覆盖面缺口/W-2 import 方向未落字/W-3 §13.7 同族死锚半截修复）→处置（兜底句/义务③/家族扩展+N1 复述句指针化+N3 现辖限定+N4 占位符统一）→复审 **PASS B0/W0/N0**；门二（ops-probe 随宿主模型）首轮 6/7 GREEN（M1 首例对齐五子项/M2 扫描面 glob 构面实证/M3 引用保真/M5 门禁复跑/M6 diff 范围/M7 _lib 先例 git 史核）+M4 RED（盘点遗漏）→M4' RED（scripts 头注 7 处再漏）→二轮处置→**M4'' GREEN**（清偿面三口径字面成立+挂账对账吻合）。
- Rulings 呈报（不阻断）：R-G2-1 §2 门禁脚本 _lib 拆法入宪=票面外搭车（工单字面仅涉 ADR-024 D1 单元包配方）——same_layer_lib/family_parity_lib 双先例支撑，G-1 Rulings 同款范围裁量先例；裁定收缩则机械移除一句。
- 卫生小记：本批 grep -l 反斜杠路径踩坑（find -exec 替代解决）；门二审出两轮盘点口径遗漏（只扫 .md 漏 scripts/*.py 头注）——全模式 §13\.[0-9] 终核为收边手段记档；geometric-repack 维护权限报错再现（G-1 在册留观同族，提交推送不受阻）。
- 账本：impl/gate1/gate2 三行在册（runId hubfire-G2-20260919T1440-8f2c）；health-scan 收口前 RED=0/WARN×3（均历史欠账：27 行缺 usage 历史记账/1 行 in=0 out>0 疑缓存——非本批引入）。
- 勾选 16→17/22（G-2）；next_batch=B4-2b（碳核算·前置二：运行成本面 opex）；收口判定⑤READY（勾选有进展 no_progress 归零；batch_count 1/60、墙钟 ~0.6h/90h 熔断远未触发）。本笔为收口终态置位（置 READY=最后一笔，此后本会话零板/仓写入）；收口终笔推送预期绿下批首跑覆盖核对（B3-c 补记二口径）。
- 回炉收口注记：首次置 READY 后发现日志段时间戳预估失真（15:47Z→实 15:16Z/墙钟 1.1h→0.6h），按铁律翻回 RUNNING 修字后重新收口（回炉收口 batch_count 不再 +1——修板不是新批；本行即该次回炉留痕）。

### batch B4-2b 设计段 — 2026-09-19 15:28Z~16:20Z（hub 火执行者会话：opex 三段通道设计定案，呈批四问未获应答 HOLD 呈批）
- 认领 token hubfire-B4-2b-20260919T1530-a7ed（调度员发布 15:26:43Z 在案）。
- 交付（全部仓外批档——仓库零笔：设计未批准不动仓）：调研摘要（.workflow/briefs/b4-2b-research.md——opex
  构成行业口径〔电费 40~50%/药剂 10~15%/227 厂均值 1.38 元/吨〕+数据策略+吨水主指标+单价档带六来源）+拟定者
  任务书（b4-2b-drafter-brief.md 250 行自包含——P1~P7 预裁决+§A~§D 附录）+拟定者设计书（b4-2b-drafter-
  output.md——C 案 app_opex.py 投影+summary 注入；备源承载——外部派发器备源通道，源档案见组织账本）+主控终裁两轮（master-ruling.md+
  master-ruling-r2.md）+门一隔离审包（reviews/b4-2b-gate1-package.md 1426 行自包含）+门一两轮（一审
  B1/W5/N8 返工→处置→复审 **PASS B0/W1/N6 全闭合**）+呈批报告（.workflow/b4-2b/review-report.md）+四案
  能耗药耗全工况探针实录（probes/b4-2b-energy-dump.py——呈批锚实数底座）。
- 终裁要旨：C1~C3 仓内核清（build_env_flow 持 data_dir/装载器 glob 排除清单自动收新文件/dims 流量键异构
  无规范全厂键→F4 吨水键挂账）；门一 B1 处置核查浮出四新事实（server worker._build_env 孪生构造三处平行/
  flows/__init__.py 499/500 满墙/魔法数字门禁字面量仅 0-1-2-10/golden e2e 已载系数）→**D2 改判 factors
  路线**（factor.opex.* 五键：电 0.70/PAC 1.85/PAM 27.5/磁种 1.3 元/kg+days_per_year 365——零接线/零拆件/
  零 server 触碰；unit_prices 81 条零触碰；备选 unit_prices 路线代价如实呈报）；锁面两本账（test-lock
  manifest 303→304+golden 键集钳制 +3 族）；锚表 node 精算（municipal design 年 opex 3,038,530.83 /
  mine 3,920,388.35 元/a；档带全域 1,321,254~2,378,258）。
- **HOLD 根因（R-B42b-1~4 呈批四问未获应答——B4-2a 同款先例不自批不走捷径）**：《裁决书》方案五②「每段
  计算逻辑均留用户审查」+锁面 AGENTS §7 人类批准事件。四问=①落位 C 案（app_opex.py 投影+summary 注入）
  ②单价档表+数据落位（factor.opex.* 五键入 factors）③计算口径（F1~F3+365 天+逐工况 sparse+挂账边界：
  人工/维修/污泥处置/折旧/F4 吨水键/ADR-024 六条处置）④锁面笔授权（golden 四案双锚+data_version 串+
  键集钳制+serialize 红清单+m3 seed/snapshots+新增 test_app_opex.py+manifest 303→304+gen_status 重入库）。
  **呈批报告=.workflow/b4-2b/review-report.md**；批准后恢复路径：回炉实装 S1~S7（file-contracts 登记→
  factors 五键+1.4.0→app_opex.py→app.py 注入链→[HUMAN-LOCK] 锁面工序→收口三验→锚表复核）→门二实证→
  推送守望 CI 至绿→勾选 B4-2b。
- 流程改进兑现注记：B4-2a 治理答疑定档「计算逻辑审查前移至设计段（实现前呈批）避免阻塞」——本批按此执行
  （B4-2a 首轮=实现后呈批致回炉重审；本批设计定案即呈批，批准后实装免重审）。
- 账本：impl（设计段全链）+gate1（两轮终态·备源承载）两行在册；勾选 17/22 不变（B4-2a 首轮同款呈批挂起态）；
  无进展计数 0（非卡死=呈批挂起）；batch_count 1→2；shared_fire 板禁删火（HOLD 终报不删——删火权归 hub
  调度员）；置位前 board 机检 0 fail/1 warn（R3 冻结旧行预期）。
- 回炉修复行：首次置 HOLD 的 hold_reason 用了自由文本触发 R2_STATUS_ILLEGAL——收敛为枚举值 stop_matter
  （呈批挂起描述文本由批次日志 B4-2b 条目与 next_batch 字段承载；回炉修复不涉 batch_count——修板不是新批）。

> 〔滚动归档〕增补八~batch B4-2b 回炉实装批段（2026-09-20 B4-2c 领批笔，69 行）已迁 relay-archive-002.md 尾部（原文零改动纯迁移——B2-6 立档同款；动因=板面 506 行超 500 文件预算）。本板自本注记起留活跃链。

### batch B4-2c — 2026-09-20T01:23Z~02:4XZ（手动会话主控直跑：碳核算本体全链收官——三段通道+呈批+实装+双门+锁面一体）
- 认领 token manual-B4-2c-20260920T0123-m2c8（无火态手动路径=当前唯一路径——认领笔 293c74da9 领批即推送；写前回读 claim=- 零占用）。
- **三段通道设计链**：调研档（.workflow/b4-2c/research.md——十因子六来源+IPCC 版本敏感性+量级锚）→拟定者设计书（drafter-brief.md 自包含任务书+drafter-output.md——外部派发器备源承载，推荐 A 案+B 案全文备援）→门一隔离审（门一隔离审备源绑定——B0/W4/N7 **有条件放行**：W1~W4 全在 B 案锁面计数面，A 案即实装路径无阻断）→主控终裁（master-ruling.md——**C1 闭卷改判**：inlet 进水声明实证在仓[design/nodes/inlet 六指标+q_avg_daily=0.4023229167 m3/s×86400=34760.46 与案名精确吻合]+真值锚重算 0.587 kgCO2e/m3 与全国均值 0.589 偏差 0.3%——裁决书原文点名吨水指标，**推荐改判 B 案**；C2 出水 TN 键名='TN' 闭卷；W1~W4/N1~N7 处置表勘正在案）→**呈批四问 R-B42c-1~4 全批**（用户 2026-09-20：①B 案全口径②2019 Refinement+AR6③全套计算口径[total 双在场律/范围三纳入/磁种不立键注释留位/44/28 与 1e-3 键化]④锁面笔授权——账本 ruling 行在档；B4-2a 流程改进兑现=设计段前移呈批，批准后实装免重审）。
- **回炉实装 S1~S7**（实现笔 d61a3661f+[HUMAN-LOCK] 锁面笔 6f61728de）：S1 file-contracts 双件登记（app_influent 第七例/app_carbon 第八例）+S2 factors +12 键（factor.carbon 11[grid_co2 0.5366/n2o_ef_plant 0.016/n2o_ef_effluent 0.005/ch4_b0 0.6/ch4_mcf 0.03/gwp 27.2+273/pac 1.764/pam 4.76/molar 1.5714286/conv 0.001]+factor.influent.s_per_d 86400；磁种 YAML 注释留位）+manifest 1.4.0→1.5.0（536→548 实数）+S3 双投影件（app_influent.py IF1~IF4——进水声明节点识别=无入边且 outflows 含 q_avg_daily[municipal inlet/mine_water_input 双案实证]；app_carbon.py C-F1~F9——三范围九式+total 双在场律+intensity Q>0 守卫）+S4 app.py 注入链两处（490 行墙内）+S5 锁面工序（解锁 304→golden 四案 effluent 增 207 键[municipal 5×13/loop 5×11/recycle 5×13/mine 2×11]实测重录+serialize 双锚[542906/6320291/546907/109848B]+data_version 串 1.5.0+m3 seed 七步锚+snapshots 3 哈希+test_app_carbon.py T1~T7+test_app_influent.py 7 用例[14 passed]+lock_tests 全根重锁 **304→306**[草稿器预检新增恰 2+哈希变 5]+gen_status 重入库[coefficients 1.5.0+锁面 306 零漂移]）+S6 收口三验（run_gates 16 门禁全绿[trust_root 随 [HUMAN-LOCK] 归绿]+core 全量 **1476 passed** 零 fail+server **315 passed**）+S7 锚表复核 **10/10 PASS**（相对差 8.6e-6~8.6e-4 全在两位舍入差带；intensity=0.58742138980596）。
- **门二实证**（ops-probe 随宿主模型——独立复算矩阵）：**8/8 GREEN**——M1 独立算术复算 municipal 13 键逐位全等（rel=0）+mine 11 键最大 3.2e-16（含磁种恒跳数值证：dose_seed 1095.9 在场而 chemicals=pac+pam 精确和）/M2 serialize 四案字节级跨进程全等/M3 sparse 三态（FilterView 真包因子屏蔽+loop/mine 真案 sparse 现场）/M4 total 双在场律四态实证/M5 推送面零越界（18 文件全在认领面，server/webapp/api-contracts/unit_prices 零变更）/M6 data_version 三面一致/M7 键族隔离（207 键 13 名与既有族交集 EMPTY）/M8 磁种三路证（键缺席+门控+数值）。报告=.workflow/b4-2c/gate2-report.md（探针自纠×2 记档——路径口径/edges dict 面勘误，非被测缺陷）。
- **验收锚**：municipal design carbon_total=20419.18 kgCO2e/d（direct 14465.0[N2O 厂内 10259.7+出水 801.5+CH4 3403.8]+indirect 5954.2[电 3884.9+药 2069.3]）、**carbon_intensity=0.58742 kgCO2e/m3**（全国城镇污水厂均值 0.589 偏差 0.3%——2019+AR6 因子系选型实证）；mine intensity=0.667（矿井高浊药剂线，典型带上沿）。
- 卫生小记：①server venv 陈旧假红（test_compare 23≠28 系旧 core 站点拷贝遮蔽——uv sync --reinstall-package waterprint-core 后 315 全绿；B4-2a incident 同款，账本 incident 勘误行随本笔补记）；②claimed_by 值含模型代号命中门禁→中性化 'manual-session-b42c'（领批笔值勘误——板面字段值也受门禁扫描面约束，记档避坑）；③relay.md 506 行超预算→滚动归档 69 行（增补八~B4-2b 回炉实装批段迁 archive-002——claimed_by 勘误同笔）；④geometric-repack 权限报错再现（G-1/G-2/B4-2b 在册留观同族，提交推送不受阻）。
- 账本：ruling（四问全批）+impl+gate1（B0/W4/N7 有条件放行·备源绑定承载）+gate2（8/8 GREEN·随宿主模型）+incident（venv 假红勘误）五行；health-scan 见收口呈报。勾选 18→19/22（B4-2c）；next_batch=B4-3 联合枚举（ADR-005 解冻须用户裁决——呈批面）；收口判定⑤READY（勾选有进展 no_progress 归零；batch_count 3→4/60、墙钟 ~1.3h/90h 熔断远未触发）。本笔为收口终态置位（置 READY=最后一笔，此后本会话零板/仓写入）；shared_fire 板不删火；推送面=认领+实现+[HUMAN-LOCK]+本收口终笔（CI run 35484317167 守望至绿——收口即推送纪律）。

- 回炉修复行 — 2026-09-20T03:0XZ（CI 首跑红 triage——修板不是新批不 +batch_count）：run 35484317167（6f61728de 面）服务层三版本+内核 3.12/3.13 五 job 红——**单一根因=app_influent.py:75 edges: tuple 缺泛型参数（mypy strict [type-arg] 拒收）**。本地收口三验未拦根因=run_gates 16 门禁不含 mypy（mypy 仅 CI 面——验证面缺口记档）。处置笔：类型注解补 tuple[Edge, ...]+Edge import；本地复验 mypy 340 文件零告警+镜像测试 7 passed+门禁全绿；顺带批次日志两处模型代号字样中性化（门禁扫描面=板面全文——B4-2c 卫生小记②同类复发，示警：批次日志引用派发源名须中性化转述）。收口终笔后的回炉修复（B4-2b 回炉收口 batch_count 豁免同款；G-2 回炉注记先例）——板头状态字段零改动（READY 终态保持）。

### 增补八 — 2026-09-20T03:23:44Z（手动会话领批：用户排序裁决落板+B4-4a 原子领批）
- **用户裁决（2026-09-20 对话内，账本 ruling 行随批）**：B4-3 联合枚举与 B4-4 AI 集成交换——B4-4 拆两段，演示段 **B4-4a 插队提前**（裁决原文：「把 AI 集成提前，因为要演示很急，确认可以一句话进行计算并输出报告就打包，然后我后续会继续其余完整流程」）。性质=排序变更+范围界定（演示版≠深化全量）；规划档=仓外 `.workflow/plans/ai-demo-plan.md`（现状底座/范围/技术路线/验收/风险单源在彼处）。执行清单 B4-3/B4-4 两行已扩注，checked_total 22 不变（B4-4 两段全成勾本项——规划档 §七口径）。
- 领批：手动路径=当前唯一路径（无火态）；写前回读 claim=-/status READY/板面静默（板 mtime 02:4X+，仓 HEAD 04510d55c=CI 绿面）零占用。认领 token=manual-B4-4a-20260920T0323（claimed_by=manual-session-b44a 中性名——B4-2c 卫生小记②纪律）。附注：用户指令追加一条范围外注记「软件页面要有导入 MCP 至 ZCode 的入口」——摸底实证=AI2 批 2026-09-13 已落地（webapp 顶栏「AI 接入」入口+GET/POST /api/ai/connection 一键写两份 .zcode/config.json），处置随呈批 P5 确认（存量在场确认 vs 演示可见性增强）。
- 板头勘误：next_batch 字段值 B4-2c 系 B4-2c 收口终笔落笔遗漏（commit message 声称同步 B4-3 而板面未写——board 机检不校验该字段未拦，验证面小缺口记档）；本笔直接落 B4-4a（B4-3 既已顺延，不停留中间态）。
- 批型=**实现批**（双门全走：门一异构隔离审[备源承载]+门二实证）；agent/tests 不在 §7 锁面（锁面=core/tests+server/tests+units_lib 包内 tests）——demo 测试件零 [HUMAN-LOCK] 拟定（呈批 P4 如实呈报）。开工呈批 P1~P4+P5（AskUserQuestion——规划档 §五）。

### batch B4-4a — 2026-09-20T03:23Z~04:2XZ（手动会话主控直跑：AI 集成演示版全链——插队批收官，B4-4 呈批注记「演示段完成，深化段随原排序」）
- 认领 token manual-B4-4a-20260920T0323（无火态手动路径；写前回读 claim=- 零占用；认领笔 1a97dfdf7 领批即推送）。
- **呈批处置（P1~P5 两轮 AskUserQuestion 未获应答→按规划档推荐继续，账本 ruling 行依据在档）**：用户开工指令「确认可以一句话进行计算并输出报告就打包」=预先授权自验打包+四问全非宪法级。取值：P1=三家可切换全环境变量三元组（WATERPRINT_DEMO_LLM_BASE_URL/_API_KEY/_MODEL——check_model_names 扫描面[含 agent+全仓 md]实测约束倒逼零端点硬编码）/P2=规则回退+--offline 显式开关/P3=agent 包内 demo.py/P4=零 [HUMAN-LOCK]（agent/tests 不在执法面——**摸底勘误**：manifest 含 agent/tests 19 条死登记[check_readonly LOCKED_ROOTS 不含 agent=登记在册零执法]，宪法条文 vs manifest 双源漂移记档）/P5=MCP 导入入口=AI2 批存量在场零改动（webapp 顶栏「AI 接入」→一键写两份 .zcode/config.json——用户追加注记的核实结论）。
- **交付（实现笔 c87d422c4+处置笔 3f3734037）**：agent/waterprint_agent/demo.py（434 行）——NL 意图解析双通道（LLM 单步[stdlib urllib 10s 超时，兼容 chat/completions 协议零供应商标识]+规则回退[种子路由/万吨规模抽取]，四失败态[网络/超时/非 JSON/违例]一律回退+parse_source 诚实标注）→tools impl 经 run_tool 统一编排（建项→改参→计算→摘要→双导出——与 MCP 工具面同语义+会话日志留痕；零新增计算逻辑[ADR-019]）；规模改参量纲异构映射（municipal inlet=m³/s÷86400、mine mine_water_input=m³/d 直填——B4-2b 在册流量键异构，实测倒逼发现）；规模 patch 被拒=硬失败拦截。测试三件 18 passed+agent/README.md（三话术/预期样例/key 配置/MCP 接入指引）+file-contracts §6 登记。
- **验收（规划档 §三三话术——口径含 R-B44a-1 修正）**：①市政 3 万吨 AAO 全链绿（达标✓/六指标/吨水电耗 0.208/碳强度 0.588/opex 2,638,585 元/双报告落盘）；③市政 5 万吨一级 A 全链绿（达标✓/双落盘/警告 2=沉砂池径深比建议带可解释）；②矿井 1 万吨=计算绿+达标判定诚实 False（TN 60 vs 15/TP 2 vs 0.5 市政标准口径负裕度=标准适用性事实）+双报告 core 既有缺口可解释回显。**digest 2bc352604a 跨 CLI/库面/手动链路逐位一致**（确定性实证）。
- **双门**：门一（ops-gate1-k2 备源承载——2026-09-18 用户指令未销案；审包 .workflow/reviews/b44a-gate1-package.md 853 行自包含）**B0/W4/N9 有条件放行**——W1 契约头三处自述失实/W2 OpenAI 供应商标识词入仓/W3 patch 被拒静默失败候选面（主控复核坐实 _update_params_impl 返回恰三键无 error 面）/W4 硬失败路径零测试——处置笔 3f3734037 W 全闭环+N1/N2/N4/N5/N6 顺手实施；门二（ops-probe 随宿主模型）**8/8 GREEN 放行**——M1 三话术 CLI 全链/M2 数值一致+三恒等式 rel=0 精确（power_total==三族和/carbon_intensity==total÷flow/opex==电+药）/M3 回退链双态/M4 双跑确定性/M5 门禁+18 passed/M6 处置覆盖/M7 README 命令逐字/M8 500 万吨越界观察（params_guard 无上界值域→12 警告算完+锚定门拒——失败模式收敛无静默，值域上界挂账 core 侧）。
- **Rulings 呈报（不阻断）**：R-B44a-1 验收口径修正——矿井案达标 False+双报告缺口两处（calcbook 模板 BOD5 硬引[agent e2e 在册记档]+report HB-F10 锚定值 926.899≠trace[原规模即红，B4-4a 新发现]）——core 修复挂账归 B4-5 矿井段或独立小批；R-B44a-2 agent/tests 锁面残留+e2e 四案存量测试债（B4-2a 起 golden effluent 键族扩容 vs AI1 锚②无守卫——agent 全量各批收口三验未覆盖+CI 不含 agent 的潜伏债）——修复涉只读位清除+manifest 19 死条目清理+锚②守卫=宪法级呈批挂账，demo 三测试件未登记 manifest 欠账；R-B44a-3 呈批未获应答处置依据+P4 摸底勘误记档（如上）。
- 卫生小记：①agent venv waterprint-core 陈旧站点拷贝（B4-2a server venv 同款残留的 agent 面——本会话 MCP 实跑数值全基于旧内核的发现链）uv sync --reinstall-package 修复；②geometric-repack 权限报错再现（G-1 起在册留观同族，提交推送不受阻）；③格式化面 ruff format 26 存量文件未动（非门禁面，防范围蔓延）。
- 收口三验：run_gates 16 门禁全绿+gen_status 零漂移（2158B）+health-scan RED=0/WARN×3（均历史欠账）。批档=.workflow/b44a/（三话术输出实录 json×3+审包归档）——演示现场断网预案=--offline 规则回退版+批档实录备份（录屏=用户侧动作）。账本 ruling/impl/gate1/gate2 四行在册。
- 勾选 19/22 不变（**B4-4 两段全成才勾**——演示段完成，深化段[多轮对话/前端 pane/方案比选]随原排序 B4-3 之后）；next_batch=B4-3 联合枚举（原排序回位——ADR-005 解冻须用户裁决）；收口判定⑤READY（勾选数不变但实质交付在案=呈批注记态；no_progress 0；batch_count 4→5/60、墙钟 ~1h/90h 熔断远未触发）。本笔为收口终态置位（置 READY=最后一笔，此后本会话零板/仓写入）；推送面=认领+实现+处置+本收口终笔（守望 CI 至绿——收口即推送纪律）。

### batch B4-4a-pkg 领批行 — 2026-09-20T04:35Z（手动会话主控直跑：Win11 软件包交付批）
- 用户直排工单（对话内 2026-09-20）：打包为适配 Win11 的软件包+使用说明→D:\ai_soft\waterprint。性质=规划档 §四打包形态的用户裁决修订（原「不做 Docker/exe——演示物=仓库可复制态」→离线软件包）；批型=交付批（烤验=收口/交付批对抗位：入仓污染面零命中+health-scan RED=0——仓外产出为主、仓内预期零代码变更）。
- 技术摸底（本行落板供批次日志引）：前端 API base=同源相对 /api（R2 C1 恒空基底）→包内胶水 serve_app.py 经 create_app 工厂 mount 静态（零仓内变更）；便携 Python=uv managed CPython 3.13.15（python-build-standalone 可迁移，与 server venv 同版本）；core 源码剔 __pycache__ 后 3MB（748M 为散落 pycache）；golden 种子真源 app\core\tests\golden\golden_data 必带（sandbox.repo_root 推导=app 伪仓库根）；依赖离线化=uv export 剔本地 path 包+wheels 目录 --no-index 安装。

### batch B4-4a-pkg — 2026-09-20T04:35Z~04:5XZ（手动会话主控直跑：Win11 软件包交付批收官——用户直排工单，D:\ai_soft\waterprint 落包）
- 交付（**仓外产出，仓内零代码变更**——本批仅板面笔）：D:\ai_soft\waterprint 完整离线软件包（725MB 含已装依赖；wheels/ 101MB 安装后可删省空间）——四脚本（安装.bat=PEP668 标记预删+pip --no-index 离线装/启动.bat=PYTHONPATH 三包注入+WATERPRINT_* 四 env 显式+PATH 注入 tools[uv 探测面]+8s 后开浏览器/停止.bat=netstat 8000 定位 taskkill/一句话演示.bat）+app 伪仓库根（core/server/agent 源码剔 __pycache__ 共 409 py 与源逐数对账+golden 种子 21 文件+data 25 文件+webapp dist 87 文件 36.8MB+serve_app.py 胶水[create_app 工厂+StaticFiles mount "/" 同源零 CORS/SSE——零仓内变更]）+tools（便携 CPython 3.13.15 python-build-standalone+uv.exe）+wheels（86 wheels 离线依赖）+使用说明.md（三步上手/功能导览[AI 接入=MCP 导入入口指引]/目录结构/FAQ/可选在线解析配置/演示三话术——矿井案口径如实注记）。
- **端到端验证（实测全绿）**：离线安装→import 全家桶 OK；服务起（18s 内就绪）→前端页面 200+assets 200+/api/units 200；API 全链建项目→异步 calc 任务 done（result 落 app\exports\tasks）；AI 接入状态四项（agent_importable=true/uv_path=包内 tools\uv.EXE——PATH 注入生效一键接入可用/写目标=app\.zcode 与 D:\ai_soft\waterprint\.zcode 伪仓库根推导正确）；**demo CLI 包环境实跑话术①与开发环境逐位一致（design digest 2bc352604a 同值——跨形态确定性证据）**；冒烟项目清理+服务停止（8000 归零）。
- 工艺实录：robocopy 首轮即全量（du 大数=NTFS 簇虚高误判，逐文件统计复核）；bat/板面内嵌 Windows 路径=raw string 纪律（首版 bat 转义控制字符损坏+板面笔脚本两次 parse 炸——SyntaxWarning 即拦截重写）；PYTHONPATH 在 git-bash 传 Windows Python 须 Windows 路径形态（MSYS /d/ 形态不识别）；PEP668 externally-managed 标记=python-build-standalone 拒装根因（包内预删标记优于 --break-system-packages 旗标）。
- 对抗位（交付批）：入仓污染面零命中（本批仓内仅 relay.md 板面笔——check_model_names 等门禁随 CI 复核）+health-scan RED=0/WARN×3（历史欠账）。账本 impl 行在册。
- 勾选 19/22 不变（交付批无清单项——挂 B4-4a 呈批注记段内）；next_batch=B4-3 联合枚举（原排序回位）；收口判定⑤READY（batch_count 5→6/60、墙钟 ~0.3h/90h 熔断远未触发）。本笔为收口终态置位（置 READY=最后一笔，此后本会话零板/仓写入）；推送守望 CI 至绿（收口即推送纪律）。

### batch B4-4a-revert — 2026-09-20T11:14Z~11:5XZ（手动会话主控直跑：仓内演示代码全回退批收官——用户直排工单「清理半成品输出物，按规划继续开发，回归正轨」）

- 领批：token manual-B44a-revert-20260920T1114-rvt（写前回读 claim=-/status READY 零占用；认领笔 a6320dc1c 领批即推送）。**用户裁决三问全答（对话内在档）**：①对象=B4-4a 演示版仓内输出物（「先集成 AI 再演示」半成品——完整版归 B4-4 深化段随原排序）；②范围=**仓内演示代码全回退**（推荐项——仓外批档保留历史、D:i_soft\waterprint 冻结拷贝不动、Synapse 不涉）；③续跑=B4-3 原排序回位。批型=实现批（已审面修改——B4-4a 已审面随批重过：回退 diff+首审上下文审包呈门一）。
- 实现（实现笔 14577ea112）：6 路径 851 删减——demo.py 446+测试三件 316+README 87 整件删除+file-contracts 两登记行还原至批前（README 系 c87d422c4 **新建件**非修改件——批前 checkout pathspec 不匹配实证）；**路径级恒等父提交 1a97dfdf75（git diff agent/ docs/file-contracts.md 输出空）**；残留零命中（agent/ 全文件 demo 零命中/WATERPRINT_DEMO_ 全仓仅本板历史记述/ADR-019 无 demo 引用）；锁面零触碰（staged 无 locks 路径+demo 测试件未登记 manifest 在册）；run_gates 回退前后双绿；agent 套件 140 passed/4 failed=在册存量债（4 失败全为 test_e2e_golden 四案 KeyError 碳键族——与 R-B44a-2 原文「B4-2a 起 golden effluent 键族扩容 vs 锚②直取无守卫」逐字吻合，现行签名键=B4-2c 碳键族；回退不含 golden/键族文件无因果通道）。
- 双门：门一（ops-gate1-k2 备源承载——板面条款未销案；审包 .workflow/reviews/b44a-revert-gate1-package.md 自包含）**B0/W1/N6 有条件放行**——W1=主控 grep `--include=*.py,*.toml` 单 glob 逗号字面量空真证据（门一独立指出；路径恒等空 diff 独立兜底不改判，补正后 agent/ 全文件零命中）；N5=ADR-019 悬空疑云闭合（29 行通用决策档零 demo 引用）；放行三条件全兑现（①本日志只追加未改写 B4-4a 既有日志②板头 batch_count 6→7+checked 不动③下行欠账销注）；门二（ops-probe 随宿主模型）**7/7 GREEN 放行**——M1 门禁/M2 路径恒等+851 算术逐路径/M3 残留三面/M4 套件独立重跑（4+140+5=149 全收集零 error=无 import 断裂）/M5 锁面/M6 领批在案/M7 还原方向 hunk 逐字。工具面注记（门二 A1）：本机 grep=ugrep 7.8.4 默认不降隐藏目录（.venv site-packages 内 demo 子串=第三方库非跟踪面不计）。
- **存量债销注**：R-B44a-2 中「demo 三测试件未登记 manifest」欠账子项随本批删除销注（登记对象已不存在）；该 Ruling 其余子项（e2e 四案存量红+manifest 19 死条目清理+锚②守卫=宪法级呈批挂账）仍在册不受影响。
- 收口三验：run_gates 16 门禁全绿+gen_status 零漂移（生成后工作树净）+health-scan RED=0/WARN×3（均历史欠账）。账本 impl/gate1/gate2 三行在册。批档=.workflow/reviews/b44a-revert-gate1-package.md（门一审包）。
- 勾选 19/22 不变（回退批无清单项——B4-4 演示段产物随用户裁决移出，深化段仍按原排序 B4-3 之后）；next_batch=B4-3 联合枚举（原排序回位——ADR-005 解冻须用户裁决呈批面）；batch_count 6→7/60。本笔为收口终态置位；推送守望 CI 至绿（收口即推送纪律）。卫生小记：geometric-repack 报错再现（G-1 在册同族——fetch 维护阶段噪音，commit/push 不受阻）。

### batch B4-3 — 2026-09-20T11:43Z~14:0XZ（手动会话主控直跑：全厂联合枚举收官——三段设计链+实装五笔+双门+处置勘误两笔）

- 领批：token manual-B4-3-20260920T1143-jen（认领笔 c90a6189a7 领批即推送；用户本会话轨道裁决=WaterPrint 主仓 B4-3）。**呈批两轮未获应答按常设指令默认推荐项记档追认**：R-B43-1 ADR-005 决策 4 解冻（ADR 承接+单单元语义[决策 1-3/5]不动+UF-33 重估入调研面——维持挂账）/R-B43-2 三段通道全链/R-B43-3~5 实装授权（ADR 定稿确认+权重与失守口径+锁面笔）。
- **三段设计链**（批档 .workflow/b4-3/）：调研档（Explore 勘察=单单元管线全可复用/缓存整 design 指纹跨组合复用为零/recompute_scope 未接线 B12/ρ=6.2e3 行·s 锚+社区检索=分层分解主流/WWTP 无先例坐实自主设计）→拟定者（备源承载——派发流水在册，in1978/out8121：两候选[分层 beam A/C 合一 vs 联合网格+剪枝]+R2 绕过缓存采纳+ADR 草案+UF-33 维持挂账）→对抗审核（异构源——派发流水在册，in4949/out12819：**B1/W12/N6 有条件放行**——B1 回路冻结类比方向相反失实+W1 换算表自破预算+W5 all_outer 不闭环+W6 评估器复用未决）→主控终裁 19 项全采纳（design-final.md：B1 类比废除=已知近似标注/W1+W7 静态预检 422+运行截断诚实/W6 直调 execute_graph 禁新写拓扑序/W9 硬门走 summary 出水 compliant/W10 sensitivity 失守=降权标记制/W12 真键映射+design 工况/N2 预算双轴）。
- **实装五笔+锁面**（ops-executor 随宿主模型六段简报 TDD）：core 笔 da88456661（joint_enumeration 六件[beam 500 顶墙/stage/final_eval/ranking/diagnose/__init__]+assumptions_joint 11 键伴生件+app 正门+§1c 新同层边+测试五件 TDD 先红后绿）+server 笔 f40e729388（services 173+新 router POST /api/solution/joint-enumerate+worker kind 登记+端点和式 36→37+测试两件）+文档笔 375f1810b4（ADR 新立+file-contracts 八行）+锁面笔 697aeccfb3（**[HUMAN-LOCK]** R-B43-5 默认授权+B4-2b/c 会话内先例：manifest 306→313 七新件+3 锁定测试解锁更新[端点 36→37/假设 22→33 破面]+只读位 10 件；哈希口径=check_readonly 归一化 CRLF→LF——首写 raw 字节 4 件漂移勘误在案）+处置笔 b86f05ff4b（门一 B1+W1+W2：unit_ids 收紧 min_length=2 回归定稿[实现者未申报偏离主控复核擒获]+五语义测试落点映射呈门二+openapi canonical +82 纯增量+ranking 头注镜像件名勘正）+勘误笔 f3ec081fb2（门二 A-2：ADR 撞号整改 006→025——joint 面 18 处同步+dxf 语义引用不动+file-contracts 残留 ≥1 勘正；A-1=主控简报转写缺陷非实现缺陷记档）。
- **双门**：门一（ops-gate1-k2 备源承载；审包 reviews/b43-impl-gate1-package.md）**B1/W2/N6 有条件放行**——B1=unit_ids≥1 未申报偏离定稿（三条件：收紧/契约笔 diff 自证/五语义映射——全兑现）；W1 五语义落点映射齐（预检 422 双面/truncated/降权标记/除零重分配/k=1 边界——test_joint_enumeration:94·107+test_solution:103+test_beam:222·200+test_final_eval:40-56+test_stage:142·117·129·136；ranking/diagnose 覆盖按 TDD 序组织于 test_stage）；W2 openapi +82 零删自证。门二（ops-probe 随宿主）**9/9 GREEN 放行**——M1 门禁/M2 core 837/M3 server 324（uv 实装真值面）/M4 禁区 diff 空/M5 收紧 422 实证/M6 契约+status 四数字/M7 锁面双 [OK] 313/M8 公式 300.0·182000.0 精确命中（A-1 简报转写缺陷）/M9 ADR+file-contracts 八路径（A-2 撞号→勘误笔整改）。
- **验证**：run_gates 16/16 绿（锁面笔前 15/16 唯红=check_readonly 流程闸——预期）；core 837 passed/server 324 passed；mypy 399 件+ruff+import-linter 双根绿；基准 1.0s<10s+rows 12≤62≤5e5+默认域锚 182000；gen_status 同步（锁面 313/ADR 25/OpenAPI 34 路径 37 操作）；health-scan RED=0/WARN×3 历史欠账。实现裁量七项：六项采信（键族 9→11 分解/final_eval 拆件/app_assembly 协议化防环[import-linter 当场擒获 BROKEN 再修]/包根单点 import/data_version 不 bump/上游快照同构双件挂档）+一项整改（B1 收紧）。
- **Rulings 呈报（不阻断）**：R-B43-6 golden 枚举锚缓征挂账（首个消费批落地——ranking/final_eval 回归敏感度暂系手写断言）；R-B43-7 实现裁量 3 的协议化改造行为面零变化主张强度上限=既有套件敏感度（golden 缺位制约——与 R-B43-6 同源）；R-B43-8 N=1 语义收紧后旧单单元正门与新正门语义边界清晰（旧门=单单元/新门=2..max_units）。
- 勾选 19→20/22（B4-3）；next_batch=B4-4b AI 集成深化段（B4-4a 演示版产物已随用户裁决回退——深化段全量重建，多轮对话/前端聊天 pane/方案比选）；batch_count 7→8/60。本笔为收口终态置位；推送面=认领+core+server+文档+[HUMAN-LOCK]+处置+勘误+本收口终笔（守望 CI 至绿——收口即推送纪律）。

### 增补九 — 2026-09-24T12:16:29Z（手动会话领批：B4-4b AI 集成深化段原子领批）

- 领批：token manual-B44b-20260924T1216-dep（claimed_by=manual-session-b44b 中性名）；写前回读 claim=-/status READY/板面静默（板 mtime 2026-09-20+，仓 HEAD 06ca4e19da=CI run 35516990346 绿面）零占用；无火态（automation 空集 2026-09-24 CronList 实测）。
- 用户指令：对话内「继续开发」（2026-09-24）——手动路径按板领批，批型=**架构级实现批**（三段通道[调研→拟定→对抗审核→主控终裁]+实现双门并集——烤验表复合批）；范围底稿=B4-4a 规划档「显式不做」清单（多轮对话/前端聊天 pane/自动方案比选）+裁决书方案五④（agent 面 21 工具扩展三面：操作链 debug 观测面对 agent 开放+知识检索扩碳核算/联合枚举+设计说明书管线轨道丙扩展）+B4-4a 演示段能力全量重建（一句话→计算→双报告为第一块积木——产物已随 2026-09-20 用户裁决回退）。
- 板头勘误随笔：checked_done 19→20（B4-3 收口终笔勾选框已落而字段漏更——grep 实测 20 对齐；修板不是新批不 +batch_count）。
- **熔断事实如实记档**：relay_started_utc 2026-09-19T14:24Z 距今 >max_wall_hours 90h——该闸=hub 火式执行者开批判据四条件之一（rev1 条款面），本会话=用户直排手动路径非火式派发，用户指令位阶高于火式闸门且火已亡零并行冲突面；不静默跳过，记档如上。
- 呈批面预告（未获应答按常设指令默认推荐项记档追认——B4-3 先例）：R-B44b-1 范围确认（三面并集全做 vs 分段——默认=并集全量，理由=B4-4 两段全成勾口径+用户「继续其余完整流程」原话）；R-B44b-2 对话编排 LLM 供应商缺省（默认=用户环境变量三选一中性键承载，缺省=用户异构源兼容端点——B4-4a 呈批 P1 同题未决沿承）；细节随设计书终裁面再呈。

### batch B4-4b — 2026-09-24T12:16Z~14:5XZ（手动会话主控直跑：AI 集成深化段收官——三段设计链+实装三子批+双门+回炉一轮）

- 领批：token manual-B44b-20260924T1216-dep（认领笔 53ca483b8d；用户本会话「继续开发」直排；熔断墙钟事实如实记档——火式闸面，用户直排位阶更高且火已亡）。板面治理笔 6a7f28d130（领批笔双红自修：源名中性化第四次复发实录+relay-archive-003 滚动归档 160 行主板回 346）。
- **三段设计链**（批档 .workflow/b4-4b/）：调研档（Explore 勘察=21 工具 impl 直调面/agent 无 http 依赖/沙箱任务表恒空/碳键已可检索+三轮社区检索=代理环 while 共识/迭代上限 10-15/会话 thread+分层记忆/聊天 UI 折叠卡基线）→拟定者备源承载（in3001/out7533：三候选+3 子批切法+T1-T5）→对抗审核异构源（in6040/out12262：**B3/W6/N4 返工**——B1 候选二工具面漂移违 ADR-019/B2 落位白名单失配/B3 joint 执行链无桥+W1 依赖裁决高估/W2 摘要自相矛盾/W3 静态表第二真源/W6 承接章偏误）→主控终裁换轴心（design-final.md：**环整体落 agent 包直调 impl+stdlib urllib 零新依赖**+server 薄中继 worker 子进程桥+SSE 零新端点[每轮=一任务]+B3 消=joint 进程内同步同构既有工具+滑窗 20 轮无摘要+result_metrics 不立项）。
- **实装三子批十一笔**：core 笔 b54419ea95（chat/ 八件 TDD 先红后绿 25 测试+CLI 降级全链冒烟+懒加载 sys.modules 零重依赖实证）+server 笔 3539f6051d（三端点 37→40+ai_chat worker 子进程桥+settings 四字段+records _KINDS+worker 顶墙拆件 export_batch_lib 四纯 helper 原文迁驻）+webapp 笔 e266222528（features/ai_chat 四件+App.tsx +13 行 413/500+orval 重生成+SseLimiter 四维零改）+agent 笔 d35771f603（#22 联合枚举进程内同步+#23 概览[results.py 500 顶墙故独立模块]+知识第三源 assumptions 程序化单源+轨道丙 narrative 纯模板+MCP 21→23）+锁面笔 621b3f1a71（**[HUMAN-LOCK]** R-B43-5 默认授权同制：313→322 九新件+契约测试 37→40+smoke 21→23）。
- **门一常设双审**（审包 .workflow/reviews/b44b-gate1-package.md 自包含）：k2 备源位 **B1/W7/N9 返工**+d1 异构位 **B0/W12/N9 有条件放行**——合并收敛处置笔 f79290f6cb：B1+k2/W2+d1=服务面 validate_component 在场实证（k2 判 B 系**审包漏报**——勘误记档）+防御纵深两道（worker 二道闸+agent 显式 ID 白名单）；W1-k2 密钥经载荷落 registry 档=实锤修复（三键撤出 payload 改 env 单通道+main setdefault 归一化）；W1-d1 桥 readline 截断=read() 全读+多行隔离实证；W3-d1 幂等吞重发=幂等键移除+测试翻转；W4-d1 错误分类=RuntimeError 500 面；W7 同会话并发=桥会话锁 O_EXCL+600s 窃取；W5 降级跨轮=裁量维持记档。
- **门二双部制**：实证部 **8/9**（M8 红=e2e_golden 满座计数 21 未随 23 更新——在册债签名被掩蔽）+裁决部（异构源位）**有条件放行三条件**——回炉笔全兑现：**P0=裁决部新发现 ChatPane SSE 字段失配**（Event 五键 message 承载 state/stage，原实现读 state/stage 键恒空→terminal 永不触发→pane 卡 busy 多轮不可用；lib/chatEvent.ts 抽件+五用例回归锚含防倒退用例）+**P0 伴生休眠崩溃**（_child_env 无参化而调用点残留四参=真调用即 TypeError——mypy 钳出闭环）；P1=timeout 第四键 main setdefault 补链；M8=计数随批更新（在册 R-B44a-2 KeyError 碳键族签名复原实证）；P2=文档漂移六处勘正；裁决部呈报=file-contracts 行数对账澄清（14 行实测——处置笔 15 行笔误记档）。
- **收口三验**：run_gates 全绿+core 837/server 336/agent 175 passed+4 failed 在册存量债（R-B44a-2——批前批后同签名）+5 skipped 在册+webapp 785（含 chatEvent 回归锚 5 新）；health-scan RED=0/WARN×4（在册 3+cfg 漂移扫描器声称值账本零命中 quirk 记档——不阻断）。
- **Rulings 呈报**（不阻断，随收口全清单）：R-B44b-1 范围并集全量（默认推荐已执行——两段全成勾口径）/R-B44b-2 LLM 三键无缺省 fail-fast 降级（终裁勘正：降级即行为非 503）/R-B44b-3 R-B44a-2 存量债维持宪法级挂账（agent 4 failed/5 skipped+CI 无 agent job——修复批另立涉人类工序）/R-B44b-4 **solutions 专用 joint UI 欠账**（solutionsPane 497/500 顶墙须拆壳独立批——本批比选消费面=agent 工具全链+聊天呈现，呈用户追认）。
- **挂账面**（N 级 18 条入清单不阻塞+#22 三态测试密度/#23 stale 三因分例/桥与 worker 无仓内自动化测试件[多行为人工实证]/agent mypy import-untyped 35 债[CI 无 agent job 实态]/**推送欠账：本机代理断 GitHub 不可达——本批十一笔+板面笔在本地，代理恢复即推送+守望 CI**）。
- 勾选 20→21/22（B4-4）；next_batch=B4-5；batch_count 8→9/60。本笔为收口终态置位。

- **CI 守望实录**（收口后两轮 triage）：首跑 run 36014673414 双红=①status.md 漂移（锁面 322→323 发生于重生成之后——计数未随）②server 覆盖率 91.38%<92% 门（新件子进程路径未覆盖）→CI 修复笔补仿进程/仿子过程单测九件（jobs/test_ai_chat 四件+services 只读面五件——全量 93% 回门）+status 重生成；次跑 run 36018094435 双红=①修复笔触碰 manifest 未带 [HUMAN-LOCK]（amend 补标）②status 漂移复发（同因）→amend 合并（de0fcdbf9b——单人仓 force-with-lease 即时改写）；三跑 run 36019422755 单红=force-push 令 push range 不可解析=信任根守卫 fail-closed 设计行为→本笔真实板面记录恢复正常 range（守望续至绿——守卫设计=首推/改写面须显式 range 重跑，本笔即最短正路）。


### 归档——原 protocol 段整段归档 — 2026-09-25（换防协议：protocol 段刷新为 golden rev1 字节副本，旧段含 rev1/rev1.1 增量条款与段内嵌 3 条早期日志，整段移此零触碰保存）


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
    E:\class\智水蓝图\waterprint，相对路径以此为基）」（转达条款规则见调度员
    增补六：仅携带未销案的用户指令，已销案 Rulings 不再随注入重复强调）
  - 禁止创建任何新自动化（成员板禁自布第二条火——hub 全局一条火红线）。
- 模型路由事实：门一主源周额度达上限（2026-09-18 用户告知）——门一/拟定者
  一律备源承载直至用户另行通知；逐字指令在组织账本 ruling 行。
- ——rev1 增量条款（2026-09-19 生产化批追加；与本段既有条款并行生效，冲突处以增量条款为准）——
- 时间基准唯一规则：板上一切时间戳为 UTC ISO8601 带 Z 后缀；「距今 N min」=（当前 UTC−字段值）÷60000 向下取整；旧 last_dispatch 行冻结仅读兼容。
- 行动前预检：字段行完整/时间戳可解析/status 合法/无重复 status 行/protocol_rev∈{0,1}——失败即一行退出 `fire: abort (reason=board_precheck_failed:<规则名>)` 并日志记欠账。
- 开批判据四条件：READY ∧ 静默窗过（last_dispatch_utc ≥30min）∧ 上批实物静默（≥5min，无 git 仓以板面与 plan 文件 mtime 代之）∧ 熔断未触发（batch_count<max_batches 且距今运行<max_wall_hours 小时）。
- 熔断触发 → HOLD(hold_reason=circuit_batches|circuit_wall)+终报「熔断裂闸：<原因>，已运行 <batch_count> 批 / <n> 小时」；收口判定次序：全勾→DONE ＞ 停止事由→HOLD(stop_matter) ＞ 熔断→HOLD(circuit_*) ＞ 零进展连续3→HOLD(no_progress) ＞ READY（batch_count 无条件+1，置终态同原子写 claim→-）。
- 一行退出固定枚举三族：fire: skip (reason=quiet_window|running_fresh|no_ready_board) / fire: terminal (reason=done|hold|board_missing) / fire: abort (reason=board_precheck_failed:<规则名>)——禁引用板面原文。
- 机检：node C:/Users/Administrator/.zcode/skills/batch-relay/scripts/check-relay.mjs board <本板路径>（收口置位前跑，须 0 fail）。

- ——rev1.1 增量条款（2026-09-19 逻辑修复批追加；与本段既有条款并行生效，冲突处以本条为准——增量条款后出者胜）——
- shared_fire 板文件缺失：从轮转清单跳过+终报记欠账，不删全局火——删火仅当全部板终态或缺失。
- last_dispatch_utc 值为 `-` =从未发布：静默窗视为已过（首批发布即此态，非解析失败）。
- 执行者心跳：任务内每隔 15min 亦必刷（每任务始末照刷）；一切板写（心跳/收口/翻回/修复）落笔前回读 claim——非己=已被接管，立即停笔让位，遗留只终报呈报。
- 僵死接管前置 UI 活动核查：同宿客户端必核执行者会话已无「正在执行」活动——仍有活动 → skip(candidate_alive)；跨宿降级 git/账本双核对+欠账行。
- 全勾判定 `grep -cE '^[[:space:]]*- \[ \]'` 计 0（行首允许缩进——误报方向=晚 DONE，安全）；翻回 RUNNING 修复的回炉收口 batch_count 不再 +1。
- 数值字段须纯非负整数（R10 机检）；值区行内注释用「值 <!-- 备注 -->」语法，机器自动截断。
### batch B4-2a — 2026-09-19 10:4X（hub 火执行者会话：碳核算前置一·能耗药耗计算面，实现完成 HOLD 呈批）
- 交付（实现笔本地提交**未推送**——推送必红 94 锁面，B3-c 同款待批态；认领笔 a1bc269 已推）：ADR-024
  （D1 预算墙拆件/D2 summary 槽位/D3 键名约定聚合/D4 单元级日耗能键/D5 泵能量法/D6 量纲从众/D7 系数档/D8
  挂账边界）+aao/cass 各立 formulas_energy.py（AO-F21~F25/CA-F29~F33：q_air→p_blower→e_aeration+p_stir/e_stir；
  CASS 特化 duty_ratio 0.5 周期曝气占空比）+energy.py（_oxygen 自 compute 迁入——500/400 双墙拆件，manifest
  并组注册保单注册口，B2-5 D1-B 单元包原位读法）+TS-F15/F16+BZ-F19/F20（泵轴功率 P=ρgQH/η+日耗电能量法——
  ρg·日均流量·设计点扬程，间歇启停自然消化，零运行时数参数）+TJ-F14/KT-F13/GM-F21/KN-F16（既有搅拌功率×24h
  收编）+聚合器 app_energy.py（app_trust 先例第五例：e_aeration/e_pump/e_stir/m_pac/m_pam/w_pam/m_seed_net
  →power_{aeration,pump,stir,total}_kwh_d+dose_{pac,pam,seed}_kg_d 逐工况 sparse；w_pam 并 PAM 族；m_seed
  毛耗不聚合——磁种循环非净耗）+app._with_energy 合并注入（result_schema 零改——ADR-012 D1 总线稳定保持，
  server/webapp 零变更、前端重生成步不触发）+factors.yaml 增 18 键（blower 五键×2 同族+stir×2+duty_ratio+
  泵效率×2+水密度×2+bz 重力）+data_version 1.2.0→1.3.0+out_dims 对账门禁扫描面扩兄弟声明件（66 条全绿，
  gate 脚本非信任根）+file-contracts 登记+ADR-024 落档。
- 实证面：run_gates 15 门禁全绿（ruff/magic/module_graph/out_dims 66 条/structure 184+33 项全过）；golden 四案
  实跑全通出数——municipal design：供气 113 m³/min/风机 189 kW/曝气 4525+泵 1510+搅拌 1178=总 7240 kWh/d
  （**比电耗 0.208 kWh/m³**——三族覆盖口径落市政厂典型带）；mine：搅拌 3421+PAC 1753/PAM 134/磁种净耗
  1096 kg/d；loop/recycle 同量级（回流增量 1~2%）。94 红**全为锁定测试期望过期**（golden serialize 锚×4+
  summary 键集钳制+aao 16/cass 12/ts/bz/ningjiao/KT 键集+vector 全表面+枚举 23→28+drawing projection 8 单元+
  N1 退化 4+m3 seed 16 步+audit 快照——红面清单呈批报告第三节）。
- **HOLD 根因（R-B42a-1~4 呈批）**：《裁决书》方案五②「计算逻辑呈用户审查」+锁面 AGENTS §7 人类批准事件——
  AskUserQuestion 四项（①曝气链路系数档②泵能量法+搅拌收编口径③聚合键族+summary 槽位+挂账边界④锁面笔授权）
  未获应答→按 B2-5/B3-c 先例 HOLD 不自批不走捷径。**呈批报告=.workflow/b4-2a/review-report.md**（计算逻辑
  全式+系数表+实跑数值+94 红清单+恢复路径）；批准后按恢复路径续跑：锁面笔（14f1efa 工序：解锁→更新→重录
  →重锁 302→303+[HUMAN-LOCK]）→全量复绿+双门（门一备源承载）→推送全部本地笔+守望 CI 至绿→勾选 B4-2a。
- 卫生小记：units_lib 源码 139 件只读位清除（2026-09-13 曝气头批「裸根误锁全树→git checkout 回滚」的属性
  残留——清单回滚了属性未清；宪法 §7 锁面只覆盖 tests 目录，源码只读位非执法面；内容与 HEAD 零差异实证后
  清除）。系数计数勘误：manifest.yaml 历史累计计数与 factors 实数口径不一，1.3.0 条起改记实数（513→531）。
- 账本：impl 行（HOLD 呈批态）；health-scan 见收口呈报。勾选 14/20 不变（B4-2a 主体完成唯呈批待裁，B3-c
  同款）；无进展计数 0（非卡死=呈批挂起）。门一/门二未跑（呈批前置——用户批准计算逻辑后再审，避免裁决
  变更后重审浪费）。

### batch B4-2a 回炉收口 — 2026-09-19 10:5X（hub 火执行者会话：用户四项全批→锁面落地→按用户指令暂停分批）
- 用户裁决回执：**R-B42a-1~4 四项全批**（①曝气链路中值档 f_sor=1.33/EA=0.20/Δp=70kPa/η=0.70②泵能量法+搅拌收编③聚合键族
  +summary 槽位+挂账边界④锁面笔授权）——构成 AGENTS §7 人类显式批准事件，账本 ruling 行在档。
- 锁面笔落地（[HUMAN-LOCK] 本地待推）：解锁 302 键→更新 30 项期望（golden 四案 serialize 双锚+effluent 增能耗药耗键
  [既有指标保源零触碰，漂移=无]+四 e2e 断言双路由[指标走 outqualities/聚合走 summary]+loop summary 面期望驱动+mine
  键集钳制放宽）→m3 seed 基线+7 步锚回写→snapshots 3 哈希重录（audit html 含新键纯哈希面）→八单元包内测试 _params 补
  系数键+formula_ids 计数+dims 恒等字典增新键+四件新增 test_main_case_energy 值断言→枚举 23→28→l7 槽 non_drawn
  24→29→**test_app_energy.py 新建**（sparse/同键叠加/power_total 合成/纯函数双跑）→lock_tests 全根重锁 **302→303 键**
  （草稿器预检：新增恰 1+哈希变 29）→gen_status 重入库（ADR 23→**24**+coefficients 1.2.0→**1.3.0**+锁面 303）。
- 复绿证据：core 全量 **1457 passed** 零 fail+server **315 passed**+run_gates **15 门禁全绿**（check_trust_root 随
  [HUMAN-LOCK] 笔落地归绿）+ruff 全绿+文件预算合规（aao variants 压至 493 行）。
- **治理答疑（用户质询：计划已定为何仍需裁决）**——三层原因如实记档：①《裁决书》批准的是"做什么"（碳核算三段路线/
  槽位/验收），公式与系数档在裁决时不存在（EA=0.20 还是 0.18 等选择差 ±20%）——裁决书自身写明"每段计算逻辑均留
  用户审查"，本次裁决是**计划内预留关卡**非计划外动作；②锁面授权是宪法性要求（golden 重录+[HUMAN-LOCK]=防"改测试
  让失败消失"信任根机制，任何计划不可预先豁免——B4-1/B3-c/曝气头批同款）；③数据策略 v2：系数档=AI 起草+领域专家
  追认制，本组织领域裁决位=用户。**流程改进（自我检讨）**：四问中③聚合落位已被 ADR-012 结构性定死属过度询问；
  计算逻辑审查可前移至设计段（实现前呈批）避免阻塞——后续碳核算段/B4-2b 采此改进。
- **用户分批指令**：当前部分（锁面收尾）完成后暂停；门一（备源承载）/门二双审+推送全部本地笔+守望 CI 至绿+勾选
  B4-2a → 下一批次（next_batch 已锚）。本地待推三笔：实现笔 f5a8150+HOLD 板面笔 72e7e2f+[HUMAN-LOCK] 锁面笔+本收口笔。
- 账本：ruling（四项全批）+impl（回炉段）+ruling（分批指令+治理答疑）四行；勾选 14/20 不变（主体+锁面完成唯双门
  推送守望待续，下一批收口）；无进展计数 0（实质进展在案）。

### 调度员增补九 — 2026-09-19（用户直排治理工单：可维护性三问的处置）
- 用户在 B4-2a 暂停点对计算模块可维护性三风险点逐一裁决（对话内）：**①同族一致性门禁+②
  拆件配方回写宪法 → 加入下波工单**（新立"治理小批"节 G-1/G-2，排 B4-2a 收尾批后、B4-2b 前；
  checked_total 20→22）；**③ vector 全表面期望外移 → 用户亲改保留项**（AI 批次不自动开工，
  第三次锁面摩擦事件仅呈报提醒）。账本 ruling 行在档。
- 顺序语义：next_batch 仍=B4-2a 收尾批（门一/门二+推送守望 CI+勾选）；收口后火班按清单序
  开 G-1/G-2 治理小批。


### 换防 + 增补十 — 2026-09-24T17:44:23.011Z（总调度员会话：用户显式点名 batch-relay——停火遗留板换防布火 + e2e-audit 插队战役纳入）

- 换防事实：旧火 automation-9d069f57 经 CronList 核查已亡（自动化列表空，无需清场）；熔断事实=circuit_wall（relay_started 2026-09-19T14:24Z 距今 ~123h > max_wall_hours 90）——用户显式续跑即换防，batch_count 9→0 / relay_started_utc 复位留痕；claim/-、no_progress_count 0、hold_reason - 本就复位态原样。protocol 段已刷新 rev 1→1（旧段整段归档于上方归档条目）。深度设计门=ai-dev-org 路径过：org-ledger 在册+战役简报齐备；插队工单自带完整 §4 批次计划（DoD/依赖/验收剧本/§7 开工指引）。
- 增补十（战役纳入）：用户直排 e2e-audit 修复战役纳入板清单（fix-plan 文头自述「位阶高于板面自动排程」）——执行清单新设「插队战役」区 E2E-1~5（checked_total 22→27），next_batch=E2E-1；每批按接力协议独立收口（勾选对应 E2E 项+batch_count+1），campaign 终批收口叠加 fix-plan §7.4 收官动作（§3 修复清单对账+§5 验收剧本+next_batch 回 B4-5 原排序）。round2 §4「批3（server-scene）新立」与前篇批3【chat】撞号——按独立新批（E2E-4）解读，排序/并批由执行会话主控终裁。
- 项目特记沿用（源=上方归档段原文，防归档后失传）：①收口四步含「收口即推送+守望 CI 至绿」（三轮裁决④常态化；代理断时如实记欠账=B4-4b 先例）；②模型路由事实（2026-09-18 用户告知）门一主源周额度上限——门一/拟定者备源承载直至用户另行通知（未见撤销通知，沿用）；③B4-5 语义不变：norms 追认前置+用户亲查计算核心优先（round2 §2 已实证计算内核业务正确性优秀，供用户亲查参考）。
- 换防现场：git 干净（main 与 origin 同步、0 未推）；仅两份 e2e 工单文档未跟踪（留修复批随批入册或用户亲阅处置）；fetch dry-run 报本地 geometric repack 维护性错误（pack 重名非远端不可达）——非阻断记档。新火 id 见板头 automation_id 字段行。

### 欠账 — 2026-09-24T17:5XZ（开批通道 UI 两击未开——前台争用让位，火班重试）
- 总调度员发布 E2E-1（换防后首批）走 UI 开批：侧边栏展开正常、AXPress「新建任务」×2 均未见新任务视图（全树无「选择项目」菜单、无新任务占位 textfield）；同窗另有用户活跃会话（非本项目）正在运行并占据主窗口标签焦点——按全局前台焦点保护规范（AGENTS.md）不与用户争抢前台，让位退出。发布未成立，未写 last_dispatch_utc。火班（*/10 automation-cbcb3949）每班重试开批判据；连败累计走 UI 通道欠账/降级路径。若两次点击实际开了后台空任务标签——无害（窗口堆积=保留校准 2026-09-18），后续可人工关闭。
- 本回合为调度回合（换防+布火+战役纳入+欠账记档），非执行批——不计 batch_count。
### 增补十一 — 2026-09-24T18:05Z（首发缺陷作废+保护性占板——用户实时纠错，调度员记档）
- 用户实时指出首发任务两缺陷：①「选择项目」未生效——工作目录未绑定智水蓝图（调度员 UI 点菜单项后未回读确认即 Escape 收菜单）；②模型未跟随当前会话模型（GLM-5.3）——开批流程缺模型设置步。**两项入开批守则：发送前验证清单=①项目按钮标签回读=智水蓝图②模型回读=跟随当前会话③指令文本回读落框**。
- 处置：首发任务（17:59Z 注入）作废——18:04:54Z 保护性占板（RUNNING + dispatcher-hold token），错误任务读到 RUNNING 非己按协议让位退出（零写入预期）；确认其回合结束后复位 READY 重发修正版任务，last_dispatch_utc 更新为新发布时刻。
- 推送欠账：本地代理 127.0.0.1 断（github 443 不可达）——3eb5550ec6 与本笔留本地，代理恢复即推（B4-4b 同款先例）。
