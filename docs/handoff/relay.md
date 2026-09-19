# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: RUNNING
- automation_id: automation-3776af0e-7217-406a-802c-870cb88b6533
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-19T12:33:44.104Z
- claim: hubfire-B4-2a-final-20260919T1215-16b0
- no_progress_count: 0
- checked_total: 22
- checked_done: 14
- protocol_rev: 1
- last_dispatch_utc: 2026-09-19T12:14:47Z
- relay_started_utc: 2026-09-19T11:58:59Z
- batch_count: 0
- max_batches: 60
- max_wall_hours: 90
- hold_reason: -
- last_handover: 2026-09-19
- claimed_by: hub 火执行者会话（B4-2a 收尾批）
- claimed_at: 2026-09-19T12:16:02.303Z
- next_batch: B4-2a 收尾批（用户裁决四项 R-B42a-1~4 已全批+锁面笔已落地——本地三笔待推：实现笔 f5a8150+HOLD 板面笔 72e7e2f+[HUMAN-LOCK] 锁面笔；剩余=门一备源承载异构审+门二实证终审→推送全部本地笔+守望 CI 至绿→勾选 B4-2a；用户指令 2026-09-19：当前部分完成后暂停，此为下一批次）

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
- [ ] B4-2a｜碳核算·前置一：能耗药耗计算面（**计算逻辑呈用户审查**）
- [ ] B4-2b｜碳核算·前置二：运行成本面（opex）
- [ ] B4-2c｜碳核算本体（先详细调研再立项——三轮裁决④）
- [ ] B4-3｜联合枚举（ADR-005 解冻须用户裁决）
- [ ] B4-4｜AI 集成深化
- [ ] B4-5｜矿井水段二（norms 追认前置）+软著（用户亲查计算核心优先）

### 治理小批·用户直排（2026-09-19 对话内裁决——B4-2a 收尾批后、B4-2b 前开工）

- [ ] G-1｜同族一致性门禁：aao/cass 同族公式族（需氧量/曝气/污泥/能耗）结构恒等机器断言+显式 delta 清单（如 CASS duty_ratio）——静默分叉变响红（可维护性答疑①，用户裁决入下波工单）
- [ ] G-2｜拆件配方回写宪法：ADR-024 D1 的 formulas_*/energy 预算墙拆件规则写入 AGENTS §11——撞墙拆法从即兴变规则（可维护性答疑②，用户裁决入下波工单）

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
### 调度员增补五 — 2026-09-19T03:57+08:00（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——增补四删火对象 automation-9d2ab6a4-… 确认已亡，零清场
  动作；新火布防后 CronList 复核全局恰一条，无双火。
- 深度设计门（换防重走）：过——`.zcode/org-ledger.jsonl` 活跃（末笔=manual-b25-ruling
  R-B2-5-1 用户裁决销案行 @09-19 02:55，文件 mtime 03:30:36）、《裁决书》占位符
  grep 零命中、执行清单机检 9 勾+11 开=20 与板头计数一致。
- 板面处置：字段对照当前技能模板零缺失（无增行）；在途 B2-6 判活=心跳 09-19
  03:47:43 新鲜+实物在途（认领提交 a3787e3 @03:47:54+ci.yml 吞日志搭车修法与
  scripts/draft_lock_manifest.py 扫描根修复均在工作树修改中+core/server 测试缓存
  mtime 新）——claim hubfire-B2-6-20260919T0347-c31f9 未动，status 维持 RUNNING；
  本条尾部纯追加；板头 automation_id 字段行已锚定替换为新火 id（锚定计数=1 守卫
  过；历史日志旧 id 存量 2 处叙述不动）。
- 新全局火=automation-4a8cb784-c14b-4941-89f3-ffe1b0cec6e5（新 hub 调度会话创建，
  全局唯一 */10 轮转，服务本板+Synapse 板）。B2-6 收口回写 READY 后，火班按轮转
  规则（READY ∧ last_dispatch 距今 ≥30min 最老优先）自然接续。
- UI 开批通道实测经验三条（前任调度会话 2026-09-19 实测，火回合开批时适用）：
  ①「新建任务」侧边栏按钮常不可寻址——Ctrl+N 快捷键实测有效；②新任务视图预置
  继承项目绑定（值不可读）——必须先按「取消选择当前项目」清空并确认清空后再
  搜索勾选目标项目，防「勾选已选项反致解绑」；③调度侧 Edit 改板遇「文件已改」
  护栏系执行者并发写入，重读后再落笔。
- 板头执行指令转达条款（B2-3 两项 Rulings——已由 B2-4 销案、原文留存照携）与
  备源承载事实继续随注入指令照原文携带。
### batch B2-6 — 2026-09-19 04:30（hub 火执行者会话：批 2 实装步③·验证型零动作步，完成）
- 主体验收达成（零文件动作）：check_out_dims_consistency 绿（56 条声明全为量纲
  真源镜像）+run_gates 15 门禁全量绿+pytest core/tests 776 passed——确认性验收：
  量纲真源单归 FormulaSpec.output_dim（GR-42）机器判定持续成立（D2-A 定案）；
  白名单三态兑现（量纲面新建无/修改无/禁改全仓）。批 2 三步实装（B2-4/5/6）
  全数完成。
- 搭车①（B2-4 增补一挂账兑现）：ci.yml core/server 两 pytest 步吞日志修法
  =set +e 收 rc→恒 cat→rc 非零保真退出→skip 门禁；benchmarks 步直跑不动。验证：
  bash -e 三向模拟（0 绿/skip 拦 1/rc=4 保真+cat 恒执行）+YAML 守卫机检。
- 搭车②（B2-2 补记挂账核销）：draft_lock_manifest.py 并集补扫（EXTRA_SCAN_
  ROOTS）消除 agent/tests 19 键假报「删除」+新增探测正例。**越权-回退全披露**：
  初版改 check_readonly.LOCKED_ROOTS 被自查拦截（该件=三信任根，[HUMAN-LOCK]
  面；挂账授权「该件非信任根」字面仅及草稿器）→git checkout 完全回退→改道
  草稿器面；门一审对此独立背书（纪律干净）。
- 新挂账两条：①check_readonly 补 agent/tests 根（真门禁强制面覆盖该段）须
  [HUMAN-LOCK] 人类批准，核销时同步摘除草稿器 EXTRA_SCAN_ROOTS（注释已写
  摘除条件）；②draft_universe() 无自动化回归测试（tests 面锁三信任根，本批
  不可自主加）。
- 门一（备源承载，审包 138 行自包含）B0/W1/N7 PASS——N1 授权链主控核对完毕
  （next_batch 行/B2-4 增补一/B2-2 补记三处原文与实施面吻合）；N3 批内处置；
  余 N 吸收挂账。门二（独立重跑）首跑 8/10——两 RED 同根因=relay.md 510 行
  超 500 全局预算（调度员增补四推过线）→归档滚动（下条）→复跑 15 门禁+776
  pytest+零漂移全绿闭环。
- 归档滚动（新机制，README 编年史迁档同款先例）：2026-09-18 建板~B2-4 增补二
  段 250 行迁 relay-archive-001.md（原文零改动纯迁移+指针块）；主板留活跃链
  （调度员增补三起），满 400 行再滚下一档——500 行全局预算与追加制长跑冲突
  的结构性处置。
- 板面事件吸收：调度员增补四（停火）+增补五（换防：新火已布、B2-6 收口
  READY 后火班自然接续）随收口笔提交。
- Rulings 回执核对（执行指令转达条款）：B2-3 两项（R-B2-3-1 追认/R-B2-3-2
  知悉）经核对**已由 B2-4 执行者销案**（batch B2-4 日志+调度员增补三在案），
  本批无重复销案动作，板头执行指令原文照存。本批新增 Rulings：无。
- 账本：gate1（findings B0/W1/N7）/probe/impl 三行；health-scan RED=0/WARN×3
  （历史欠账回显）。勾选 9→10/20；next_batch=B3-a。CI 守望：本批推送首跑即
  ci.yml 修法真实验证（门一 N6 闭卷条件），绿证随守望补记。
- 卫生小记：认领笔 claimed_by 字段值因脚本双重转码呈乱码（仅短暂态字段值，
  无消费面），收口归位即净；已推送笔不重写。教训：认领/收口脚本中文字面量
  直写，勿做转义序列再转码。
### batch B2-6 补记 — 2026-09-19 04:5X（CI 守望终态：绿——收口闭环）
- 收口笔 1e48799 run **35390317031 全绿**（success，10 job：架构门禁/内核质量
  ×3[3.12·3.13·3.14——Pytest 全量绿]/服务层×2[3.13·3.14]/前端构建/镜像构建/
  依赖审计/性能基准）——**ci.yml 吞日志修法首次真实 Actions 运行验证通过**
  （门一 N6 闭卷）；认领笔 a3787e3 run 35387941588 亦绿。
- 会话终态：B2-6 一批完成（勾选 9→10/20），READY，claim 归位；批 2 registry
  分性质改造（三段通道+三步实装 B2-4/5/6）全数收官；next_batch=B3-a（批 3
  同层晋升第一步：server 七份 _latest_calc_result 复制收敛，准入五条）。

### 调度员增补六 — 2026-09-19T04:23:24+08:00（用户裁决：已销案工单不再随注入重复强调）
- 用户对 hub 调度会话明示：「已经追认过的工单不用每次都在最后强调」——
  已销案/已追认的 Rulings 转达条款不再随执行指令逐批携带与核对。
- 处置：板头执行指令原文摘除 B2-3 两项 Rulings（R-B2-3-1 追认/R-B2-3-2 知悉）
  转达段——该两项 2026-09-18 23:31 用户裁决、B2-4 执行者已销案在案（批次日志
  batch B2-4+调度员增补三），此后 B2-5/B2-6/B3-a 连续三批重复核对属冗余，
  自下一班发布起不再携带。B3-a（04:21 已发布）注入文本含该段——执行者若再
  次核对销案照常无害，不算违规。
- 转达条款规则自此定型：执行指令只携带**未销案**的用户指令（销案或用户明示
  解除即摘除）；历史日志中已发生的携带记录不回改。
- 本板现存持续有效指令：门一/拟定者备源承载（直至用户另行通知）——继续携带。
### batch B3-b — 2026-09-19 05:55（hub 火执行者会话：批 3 第二步·webapp SSE+域色收敛，完成）
- 交付（commits 1279871+4545b74+本板面笔）：shared/api/useTaskEventSource 新建（全库唯一
  new EventSource 处）——useTaskEventSource 长订阅 hook（退避/慢探测恢复态机+onConnection
  三态，生命周期自 useTaskFeed 逐行搬家）+subscribeTaskEvents 命令面（一次性等待——onerror
  不自动 close 保浏览器内建重连）+TaskEventReading 解读协议（drop/event/terminal 三态——
  解析归约注入归消费方，内核零业务分支）；useTaskFeed 改归约薄壳（ConnectionState/重连
  纯函数族再导出保公开面——solutionsPane/TaskPanel/测试件 import 零改动）；useExportBatch.
  awaitTerminal 改接命令面（EventSource 自建删除——失败计数/超时/取代守卫留业务面，interpret
  先归零后解析口径保持=原双实现畸形面语义各自保真未强行同构）。域色面：semanticColors 增
  DOMAIN_COLORS 五字面+domain_* 五键（pipe 两键改引用灭文件内双写；29→34 键冻结锚同步）；
  unitGlyph 域色/流色/NEUTRAL_DOMAIN+CanvasFlow LEGEND_LINES 收编键引用（同值搬家零漂移）；
  global.css --wp-* 轴保留=UF-53 新立挂账（十四节入册——SVG 不能 var() 根因性债，裁决明示
  另立不强解）。契约同步：shared/api+shared/ui+solutions/drawings/canvas 五 README+status
  重入库（UF 53/webapp 测试 66）。
- 等价性证据（双门+机检）：vitest 66 文件 762 passed（基线 65/754+内核 8；门二双跑复核）+
  tsc 零错+vite build 绿+check_webapp 236 契约头+run_gates 全绿+gen_status 重入库零漂移
  （2158B）+残留双扫描（new EventSource 全库唯一=useTaskEventSource.ts；四域色 hex 在
  单源/CSS 轴/测试件外零命中）。门一（ops-gate1-k2 备源承载，审包 1224 行自包含——双 hook
  等价性审计最小必要面）**B0/W2/N4 PASS**：A1 SSE 逐路径等价全对账+两独立推演（onError
  闭包 TDZ+旧流误关新流竞态=WHATWG readyState 阻断派发定谳安全；awaitTerminal 终态四路
  竞态逐帧等价）；W2=F1（drop 鉴别用例非判别性——门一构造对照世界全断言同果证伪）+F2
  （taskId 切换路径零直测）→处置笔 4545b74 修 F1（可切换解读桩+退避梯实例计数钉死：drop
  不归零→2s 梯 vs 归零→1s 梯，+1s 处实例数分叉——两世界判别性成立）+F5（头注计数）；
  N 挂账三条：F2（React 桩依赖数组失灵系测试面局限，真实语义门一已推演等价）/F4
  （NEUTRAL_DOMAIN/LEGEND_LINES 字面量类型→string 漂移，运行时零影响）/F6（awaitTerminal
  detach 无条件结清 pendingFailRef 既往隐患随迁——原件同款非本批引入）。门二（ops-probe
  独立重跑未读主控结论）矩阵 **9/9 全 GREEN 零 RED**。
- **F3 更正（门一 N 项——D4 披露时序描述失实）**：审包 §8 D4 曾称「覆盖前收旧流原在 new
  EventSource 前」——实况原序=先构造后收旧（原件 574/577 行），新序=先收旧后构造；构造
  函数无同步副作用（事件派发恒异步），两序行为等价结论不受影响（门一裁定：依据失实、
  结论正当）。
- Rulings：本批无新增（实装与《裁决书》方案二 2b 字面吻合、准入五条全过、零未规划
  裁策项；范围外三处——PortHandle 非语义灰阶/图标 rgba 族/CSS 轴——门一 D5 裁定正当）。
- 账本：gate1（B0/W2/N4）/probe（9/9）/impl 三行；health-scan RED=0/WARN×3（历史欠账
  回显，非本批引入）。锁面零动作（webapp 测试不在 LOCKED_ROOTS=core/tests+server/tests；
  新增内核测试件 1+冻结锚更新 1 均无信任根触碰）。
- 勾选 11→12/20；next_batch=B3-c。CI 守望：本批推送（4545b74+板面笔）首跑绿证随守望
  补记（收口即推送+守望 CI 至绿——三轮裁决④）。
### batch B3-b 补记 — 2026-09-19 06:0X（CI 守望终态：绿——收口闭环）
- 收口笔 8d1b00a run **35397263162 全绿**（success，10 job 全过：架构门禁/内核质量
  ×3[3.12·3.13·3.14]/服务层×2[3.13·3.14]/前端构建[类型检查+vitest+构建]/镜像构建/
  依赖审计/性能基准）——B3-b「收口即推送+守望 CI 至绿」闭环（实现笔 1279871+处置笔
  4545b74+收口笔 8d1b00a 三笔同批推送面）。
- 会话终态：B3-b 一批完成（勾选 11→12/20），READY，claim 归位；批 3 第二步收官；
  next_batch=B3-c（批 3 第三步：core B4 双胞胎+异常表两份→§1c 同层边——架构级
  三段通道：社区调研→拟定→对抗审核→主控终裁）。

### batch B3-c — 2026-09-19 07:50（hub 火执行者会话：批 3 第三步·core B4 双胞胎+异常表收敛，代码面完成 HOLD 呈批）
- **HOLD 根因（R-B3c-2 呈批）**：镜像规则（test_mirror_rule）对新两源件（contracts/edge_parsing.py+
  domain_exceptions.py）机械触发镜像测试义务（全树文件名匹配）；新增测试=[HUMAN-LOCK] 三连锁
  （manifest 新键+只读位+镜像件）须用户批准（AGENTS §7）——与 B2-5 R-B2-5-1 同款交互，定案 §4 验收
  与 P9「锁面零动作」未预见此面（任务书事实包 §B-5 缺镜像规则条目=主控简报缺口，记教训）。
  AskUserQuestion 呈批未获应答→按 B2-5 先例 HOLD 不自批/不走 noqa/不改镜像规则。薄壳两件已双向验证
  （门二独立复跑：拷入=5 passed 全绿/移除=镜像规则复红/锁面 299 键零残留），草稿=.workflow/probes/b3c/
  mirror-tests-draft/。**批准后执行路径已锚 next_batch 行。**
- 三段通道全走（架构级纪律）：①社区调研（共享内核 vs 复制取舍+异常集中化两路线，9 源）→②拟定者
  备源派发（备源承载，154s，330 行设计书三候选全权衡——甲案推荐=全下沉 L0+组合路线+
  error 异常类注入）→③对抗审核备源（备源承载，B0/W3/N7 PASS——W-1 A-3 字面偏离呈报/W-2 registry
  落点缺候选/W-3 status 零漂无据断言）→④主控终裁（W/N 逐条处置+独立复核闭卷 J6：check_module_graph
  L427 同节点忽略实证；定案=docs/design/2026-09-19_b4-twins-convergence-design.md）。
- 交付（代码面 commits afd147c+c6082d1 本地待批随锁面笔推送）：contracts/edge_parsing.py 新建
  （endpoint_from/edges_from，error 异常类注入——批 3a not_found 先例同型；消息统一含「得到」版，
  app 侧文本零变=validate 汇总面零连带）+contracts/domain_exceptions.py 新建（DOMAIN_EXCEPTIONS_CORE
  四族单源，序=executor 现相对序）；executor_assembly/app_assembly 双胞胎改同名绑定件（私有名与定义位
  不动=镜像恒等钉零扰动；旧复制逻辑同批删除）——executor_assembly._endpoint 经门一 W1 裁定注记
  「镜像钉兼容壳（生产零消费）」；executor._DOMAIN_EXCEPTIONS=CORE+graph 三族（7 族恒等）、
  enumerate._ROW_DOMAIN_EXCEPTIONS=CORE+InvalidFormulaError（5 族恒等）——两份人工同步义务消灭；
  contracts/__init__ 聚合 3 名（白名单注记 13→15 同步）+file-contracts 两新行。结构面：零新增同层边
  零 §1c 零图谱改动（全既有向下边；§1a 包级节点/check_module_graph 同节点忽略双实证）。
- 等价性证据（双门+机检）：golden 4 绿+全量 pytest 775 passed（唯一红=镜像规则 R-B3c-2，两向验证
  因果闭合）+run_gates 15 绿（lint-imports 双根 core 5+server 2 kept 零破）+gen_status 2158B 零漂移
  （W-3 按实跑核验闭卷）+mypy/ruff 零错+恒等钉 6/6+元组 7/5 成员集恒等（门一独立复算+九族裸
  Exception 零交叉继承闭卷次序语义）+golden 快照零触碰（门二项 10）。门一（外部派发器承载：
  ops-gate1-k2 子代理通道认证失败→备源 403 额度尽→第三源兜底；审包 469 行自包含）
  **B0/W1/N5 PASS**——W1 批内修复（c6082d1）；门二（ops-probe 独立重跑未读主控结论）矩阵 **9/10
  GREEN**（唯一 RED=简报预期描述笔误非代码面，主控裁决：kernel 外三形态仅 incremental.py:229 批前
  既有异载体一处+第四形态 app_assembly.py:246 聚合面批前既有——零新增残留）。
- **Rulings 待用户（两项，随终报呈批）**：**R-B3c-1**=裁决书 A-3「承载位置=按 ADR-014 §1c 同层边申报」
  按意图读法执行（定案零新增同层边+共享件下沉 L0；§1c 申报机制在引入同层边时才触发——字面读法
  强制造同层边与裁决②「分层铁律不动」相悖）——涉裁决书字面释义呈追认（B2-3 D1 先例）；**R-B3c-2**=
  镜像测试两薄壳 [HUMAN-LOCK] 锁面笔批准（299→301+推送本地三笔+CI 守望至绿+勾选 B3-c）。
- 挂账：G1 latent 不对称（executor 不含 InvalidFormulaError，行为零变不修）/G2 _NullSink+_dims_of
  双胞胎（范围外）/G3 消息锚测试（薄壳已含注入语义冒烟，正式锚测试走锁面程序）+新增 G4=validate
  聚合面自有文案与 incremental.py 异载体文案两处批前既有近似文本（后续批次评估收编）。
- 账本：gate1（第三源兜底 B0/W1/N5）/probe（9/10）/impl-HOLD 两行+外部派发器自动行（drafter/
  auditor/gate1 各 attempt/ok）；通道事实：ops-gate1-k2 子代理认证失败（621ms）+备源五小时
  额度尽（403）——第三源兜底承载记档，源恢复后回备源。
- 勾选 12/20 不变（B3-c 主体完成唯锁面待批，批准后勾选）；无进展计数 0（非卡死=呈批挂起，B2-5 同款）。
  本批未推送（推送必红镜像规则——B2-5 实证；本地三笔待批随锁面笔一并推送，收口即推送纪律在批准
  后恢复）。


### 调度员增补七 — 2026-09-19T08:25:54+08:00（hub 停火：用户令删火）
- 用户在 hub 调度会话下达删火令：全局轮转火 automation-4a8cb784-c14b-4941-89f3-
  ffe1b0cec6e5 已 CronDelete（回执 deleted:true，CronList 空集复核）。本条为调度员
  尾部纯追加，claim/状态字段未动；板头 automation_id 字段行保留旧值仅为历史审计指向。
- 本火任内战果：B3-a（server 七份复制收敛）/B3-b（webapp SSE+域色双源收敛）两批完成
  （勾选 10→12/20）；B3-c 代码面完成唯镜像锁面待批（R-B3c-1/R-B3c-2 两项 Rulings
  呈批挂起，HOLD 态）。
- **B3-c 的 HOLD 呈批不受影响**——两项 Rulings 待用户裁决的终报已随批次日志在案，
  用户批准后按 B2-5 先例走锁面笔（[HUMAN-LOCK]+推送本地三笔+CI 守望至绿+勾选 B3-c），
  可由用户指定会话或重布防后的执行者执行。恢复两径同规：用户显式 /batch-relay 重布防
  （换防协议 hub 变体），或手动会话按本板清单领批/处理呈批。
- 调度员会话自本增补起不再开批、不再补派。
- 板头执行指令转达条款规则（增补六：仅携带未销案指令）与备源承载事实留存，重布防时
  随板面原文生效。

### batch B3-c 补记 — 2026-09-19 08:2X（用户裁决两项全批+锁面笔落地——B3-c 全绿收口）
- 用户裁决回执（对话内）：**两项全批**——R-B3c-1（A-3 §1c 意图读法）追认、R-B3c-2（镜像测试
  锁面笔）批准。批准构成 AGENTS §7 人类显式批准事件，[HUMAN-LOCK] commit bd1ff71 首行带标签+
  逐文件修改动机（3 文件：两薄壳+manifest）。
- 锁面执行细节：两薄壳拷入 core/tests/contracts/（N818 命名修正 _Carrier→_CarrierError 后
  ruff 零错）；lock_tests.py 全根清单重锁 299→**301 键**（新增恰 2 零删除，COST2 守卫经草稿器
  全根命令显式通过），只读位随脚本设置；gen_status 重入库（恰锁键行 299→301，2158B 不变——
  合法输入变化，B3-b 重入库先例）。
- 产出面纪律补丁随批：批次日志外部源代号中性化（08 §6——源细节住组织账本，仓内工件零代号；
  check_model_names 门禁复绿）+未推本地笔 message 同步重写（19538be/e94aa01 替换原两笔）。
- 复绿证据：全量 pytest **780 passed 全绿**（775+镜像规则修复 1+薄壳 4——数序吻合）+run_gates
  15 绿（check_trust_root=[HUMAN-LOCK] 首行标签过；check_model_names 复绿）+gen_status 2158B
  零漂移+锁面草稿器 301 键一致。
- 板面：HOLD→READY、B3-c 勾选（12→13/20）、claim 归位；Rulings 待用户：无（本批两项已销案）；
  next_batch=B4-1（第四波首批：操作链集中 debug 观测面）。CI 守望随终报（收口即推送+守望
  CI 至绿——三轮裁决④；本批推送面=认领笔 7c0365a+实现笔 afd147c+处置笔 19538be+[HUMAN-LOCK]
  锁面笔 bd1ff71+HOLD 板面笔 e94aa01+本收口笔）。

### batch B3-c 补记二 — 2026-09-19 08:4X（CI 守望终态：绿——收口闭环，批 3 收官）
- 收口笔 d1ff04e run **35410239876 全绿**（success，10 job 全过：架构门禁/内核质量×3
  [3.12·3.13·3.14——Pytest 全量含镜像规则复绿+两薄壳]/服务层×2/前端构建/镜像构建/依赖
  审计/性能基准）——首跑即绿零重跑，B3-c「收口即推送+守望 CI 至绿」闭环（推送面五笔：
  afd147c 实现+19538be 处置+bd1ff71 [HUMAN-LOCK] 锁面+e94aa01 HOLD 板面+d1ff04e 收口；
  认领笔 7c0365a run 35398883295 亦绿）。本笔为纯板面绿证登记（推送触发的后续 run 预期
  绿，由下批首跑覆盖核对——B2-5 补记三同款口径）。
- 会话终态：B3-c 一批完成（勾选 12→13/20，含 HOLD→用户两项全批→锁面落地复绿全程），
  READY，claim 归位；**批 3 同层晋升三步全数收官**；next_batch=B4-1（第四波首批：
  操作链集中 debug 观测面——复用 calc-diag artifact+事件流+trace 聚合，实现批双门）。

### 调度员增补八 — 2026-09-19T11:07:19+08:00（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——增补七删火对象 automation-4a8cb784-… 确认已亡，
  无双火风险，零清场动作。
- 深度设计门（换防重走）：过——`.zcode/org-ledger.jsonl` 活跃（mtime 09-19 08:41，
  末笔=R-B3c 两项用户裁决销案行）、《裁决书》占位符 grep 零命中、执行清单机检
  13 勾+7 开=20 与板头计数一致。
- 板面处置：字段对照当前技能模板零缺失（无增行）；用户换防指令所记停火时态快照
  「HOLD 待裁（R-B3c-1/R-B3c-2 等裁决）」已过时——两项 Rulings 已于 08:2X 用户
  对话内裁决全批（R-B3c-1 追认/R-B3c-2 锁面笔批准，账本销案行在档），锁面笔
  bd1ff71 落地、CI 全绿（run 35410239876）、板已 HOLD→READY 且 B3-c 勾选
  （12→13/20）、next_batch=B4-1——两项均销案在案，本次换防无转达/复位动作；
  status/claim/no_progress 均期望态零复位；本条尾部纯追加；板头 automation_id
  字段行已锚定替换为新火 id（锚定计数=1 守卫过；历史日志旧 id 存量不动）。
- 新全局火=automation-2988ca0b-9af5-4ae0-a8ed-319602ec2ddf（新 hub 调度会话创建，
  全局唯一 */10 轮转，服务本板+Synapse 板；首班 11:16 投递）。本板
  last_dispatch=09-19T05:49:54 早于姊妹板 08:20:24——首班有效火先轮本板
  （B4-1 操作链集中 debug 观测面——实现批双门）。
- 板上既有条款自动生效：执行指令只携带未销案的用户指令（增补六定型）；门一/
  拟定者备源承载直至用户另行通知，继续随注入携带；UI 开批通道经验（Ctrl+N
  先切回会话视图/「取消选择当前项目」清空再勾选防反致解绑/调度侧 Edit 遇
  「文件已改」重读再落笔/主输入框 a11y 写入不生效须前台激活后 app 级
  strategy=event 真实键盘写入，前台被游戏全屏锁定连败 2-3 次即记欠账退出勿硬抢）
  沿用历任实测累积。

### batch B4-1 — 2026-09-19 12:50（hub 火执行者会话：第四波首批·操作链集中 debug 观测面，完成）
- 交付（commits 9acca6a 实现+eb54362 [HUMAN-LOCK] 锁面+本收口笔）：server services/ops_debug.py 新建（292 行——任务时间线[manager 注册序=操作序+task_status 状态正门复用含 error_code 回填/实时 stale 比对+finished_at 公开投影]+latest done calc 三源深度聚合[latest_calc_result 共享件第七消费面=批 3a 槽位填槽；diag 读取降级同 trust ADR-012 R2 禁伪造；trace 三桶统计 by_condition/by_unit/by_formula 字典序确定性+守恒；无 done calc=内部哨兵异常注入共享件 not_found 槽→latest_calc 空块 200，与 trust 404 消费面语义分立]）+routers/debug.py 新建（61 行——GET /api/debug/ops-chain/{project_id} 端点计数 35→36 裁决书授权破面；asyncio.to_thread 承载大结果件反序列化[门一 W3 修复，FD PD6 先例]）+manager.finished_at 公开投影方法（WP4 内存值，重启恢复=恢复时刻新租约 docstring 注记）+main 装配。webapp 诊断 pane 第七例（trust 同构）：features/opsdebug 三件（lib 窄化门 13 键 13 叶子类型校验[门一 W1 修复]+api hook+components 时间线卡/三源聚合卡/降级蓝条）+opsDebugPane+App「诊断」标签+router 注册+TASK_EVENT 第七处监听+features README；orval 再生成（debug 域+模型 12 件）+openapi 快照再生成（36 端点）。
- 实证面：仓外探针矩阵 **43/43 全 PASS**（.workflow/probes/b4-1/ 留存）——P1 E2E 三源聚合（条目 13 键全+diag/警告/trace 三桶守恒）/P2 零任务空块/P3 删结果文件降级不炸时间线不丢/P4 404+error_type/P5 同状态双 GET 字节恒等/P6 哨兵路径（enumerate done 后 latest_calc=null）/P7 重启恢复矩阵（registry 档案→新 Manager 恢复→时间线不炸+缺档降级）；vitest 全量 774 passed（基线 762+本批 12）+tsc 零错+vite build 绿；run_gates 15 门禁全绿+gen_status 2158B 零漂移；server 全量 pytest **315 passed**（312+契约复绿+薄壳 2）。
- 门审：门一（ops-gate1-k2 备源承载，审包 795 行自包含）**B0/W3/N5 PASS**——W1 窄化门 13 键补全+类型校验 5→13 叶子（vitest 同步）；W2 重启缺档炸点=构造性一致论证（task_ids_for_project 与三查询同读 _tasks 单 dict+循环体零 await=无并发删除窗口）入规格头注记+探针 P7 实证；W3 to_thread 卸载。N1 降级 catch=trust 同制定谳（core 守卫族全收编 InvalidResultError）；N2 P6 补证；N4 生成件 queryKey 逐字一致复核；N5 悬浮注记引文闭卷；N3 幂等口径文案挂账。**处置回执经门一岗逐条认可无重审面**（子代理回执在档）。门二（ops-probe 绑定档案模型不可用[model-not-found，log-triage --health 归因非额度面]→general-purpose 会话内岗承载同矩阵，独立性=新会话无主控上下文；欠账行在账本）矩阵 **6/7 GREEN**——唯一 RED=test_openapi_endpoint_set 端点集期望 35 未含新端点（锁面文件预期红面，门二岗自判「属任务书预告已知面」）；自写等价性抽查 4/4（双端点 warning_counts/convergence_lines/task_id 三面对账同一+非空性交叉证据排除同源降级假阳性）。主控裁决：唯一 RED 根因=锁面期望集过期，经 R-B41-1 用户批准同步后复绿（315 passed）——实质全过。
- **Rulings 回执：R-B41-1 用户裁决销案**（对话内 AskUserQuestion：批准合并锁面笔）——构成 AGENTS §7 人类显式批准事件，[HUMAN-LOCK] commit eb54362 落地：test_api_contract.py 期望集 +1 行 35→36+薄壳 test_ops_debug.py 拷入（公开面+404 两用例）+lock_tests 全根重锁 301→302 键（COST2 经草稿器全根命令显式通过）。
- 挂账两条：①幂等命中「注册序≠操作序」面板文案提示（门一 N3——后续 UI 批）；②ops-probe 绑定档案声明的模型在本环境不可用（model-not-found——档案面漂移，技能侧修复位，本批 general-purpose 会话内岗承载记欠账）。
- 图谱零改动（routers→services/services→jobs 包级边既有覆盖+services 包内互调=同节点伴生边天然豁免 B7 笔①口径）；§2 调用链增 B4-1 行+file-contracts 三登记（routers/debug+services/ops_debug+manager 注记）+webapp README 双登记（features/opsdebug+app）。
- 归档滚动：主板 503 行超 500 预算（B2-6 同款）——调度员增补三~B3-a 补记段 135 行迁 relay-archive-001.md 尾部（原文零改动纯迁移+指针块），主板 372 行起。
- 账本：gate1（B0/W3/N5，处置回执全认可）/probe（6/7 GREEN 承载欠账）/impl/Ruling 销案四行；health-scan RED=0/WARN×3（历史欠账回显，非本批引入）。
- 勾选 13→14/20；next_batch=B4-2a。CI 守望：推送面=9acca6a+eb54362+收口笔，绿证随守望补记（收口即推送+守望 CI 至绿——三轮裁决④）。

### batch B4-1 补记 — 2026-09-19 12:5X（CI 守望终态：绿——收口闭环，首跑即绿）
- 推送面五笔（认领 c1ed59e+实现 9acca6a+[HUMAN-LOCK] 锁面 eb54362+收口 963bd4f+修复 6afd65f）run
  **35421500060 全绿**（success，首跑即绿约 4 分钟——10 job 全过，含内核质量×3 Pytest 全量与服务层×2
  [315 passed 契约复绿+薄壳]、前端构建[vitest 774+tsc+build]、镜像构建、依赖审计、性能基准、架构门禁）。
  B4-1「收口即推送+守望 CI 至绿」闭环。修复笔 6afd65f=锁面收尾两修（薄壳 RUF100+批次日志模型代号
  中性化[08 §6，B3-c 同款]）随 R-B41-1 授权链延续。
- 会话终态：B4-1 一批完成（勾选 13→14/20，含 R-B41-1 对话内裁决→锁面笔→CI 全绿全程），READY，
  claim 归位；第四波业务线首批收官；next_batch=B4-2a（碳核算前置一：能耗药耗计算面——计算逻辑呈
  用户审查）。

### 增补 — 2026-09-19（rev0→rev1 原位升版迁移——batch-relay 生产化批 Task 6，主控会话直跑）
- 迁移写（只增行+折算+追加，未复位既有状态，批次日志区零改写；板头自定义字段 last_handover/claimed_by/claimed_at/next_batch 原位保留；protocol 段含手动路径/hub 火式条款/模型路由事实等既有内容一字未动）：板头新增 protocol_rev:1、last_dispatch_utc=2026-09-19T03:14:24Z（旧 last_dispatch 行 11:14:24+08:00 折算，旧行冻结保留）、relay_started_utc=2026-09-19T06:33:54Z（熔断自迁移起算，非项目起点）、batch_count:0、max_batches:60（3×20 派生）、max_wall_hours:90（⌈1.5×60⌉）、hold_reason:-；protocol 段末追加「rev1 增量条款」块。
- 迁移前基线（check-relay.mjs board）：0 fail+2 warn（R0/R3）；迁移后：见机检记录。claim 本为 -，无状态修复项。
- 执行承载：batch-relay 生产化战役（E:/zcode_md/fix/docs/plans/2026-09-19-batch-relay-production-hardening.md Task 6，D4 裁决会话直跑）；观察门过（last_dispatch 距今 3h19m ≥60min、claim/-claimed_by 空、READY）。

### 增补二 — 2026-09-19（rev1.1 增量条款追加——batch-relay 逻辑修复批 Task 6，主控会话直跑）
- 追加内容：protocol 段末（执行路由标题行前）插入 7 行 rev1.1 块（A1 缺失豁免/A3 dash 语义/A2 心跳+写前 claim 回读+接管 UI 核查/B2 缩进全勾/A5 回炉豁免/R10 数值与值区注释语法）；既有行一字未动（自定义协议段/板头自定义字段整体保留）。观察门四项核值（2026-09-19T08:11:05Z）：last_dispatch_utc 距今 4h56m ≥60min ✓、claim=- ✓、板面 mtime 距今 1h35m ≥10min ✓、status=READY ✓；仓 git 最近提交距今 3h32m ≥10min ✓（N-4）。

### 增补三 — 2026-09-19T08:46:13Z（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——增补八布防对象 automation-2988ca0b-… 确认已亡，零清场
  动作；新火布防后 CronList 复核全局恰一条。
- 深度设计门（换防重走；用户布防指令口径同 Synapse 板=以板内 plan 字段指向的《裁决
  书》/自含清单为准）：过——《裁决书》占位符 grep 零命中、执行清单机检 14 勾+6 开=20
  与板头计数一致、org-ledger.jsonl 活跃（mtime 09-19 12:38）；check-relay plan 子命令
  照跑 exit=1：MISSING_SECTION 系自含清单非 writing-plans 模板预期态，无 PLACEHOLDER
  命中。
- 换防复位（板不重建）：relay_started_utc 重锚 2026-09-19T08:46:13Z（熔断复位留痕）；
  status READY/claim -/claimed_by -/no_progress 0/batch_count 0/hold_reason - 均期望
  态零改写；protocol 段 rev1+rev1.1 增量条款在册（增补/增补二所立），无需补齐；复位
  后 board 机检 0 fail（1 warn=冻结旧行 R3 预期）；本条尾部纯追加；板头 automation_id
  字段行已锚定替换为新火 id（锚定计数=1 守卫过；历史日志旧 id 叙述存量不动）。
- 新全局火=automation-aa40bf0e-0483-4ecb-9698-7f0cd533fce0（新 hub 调度会话创建，
  全局唯一 */10 轮转，服务本板+Synapse 板；首班 08:56Z 投递）。本板
  last_dispatch_utc=09-19T03:14:24Z 早于姊妹板 03:19:21Z——首班有效火先轮本板
  （next_batch=B4-2a 碳核算前置一：能耗药耗计算面——计算逻辑呈用户审查）。
- 板上既有条款自动生效：执行指令只携带未销案指令（增补六定型）、门一/拟定者备源承载
  直至用户另行通知、UI 开批通道经验沿用历任实测累积。

### 增补四 — 2026-09-19T10:38:30Z（hub 停火：用户令删火）
- 用户在 hub 调度会话下达删火令：全局轮转火 automation-aa40bf0e-0483-4ecb-9698-7f0cd533fce0
  已 CronDelete（回执 deleted:true，CronList 空集复核）。本条为调度员尾部纯追加，
  claim/状态字段未动；板头 automation_id 字段行保留旧值仅为历史审计指向。
- 本火任内战果：B4-2a 首轮执行（08:55:10Z 发布）HOLD 呈批（R-B42a-1~4 四项
  Rulings）→ 用户裁决 → **B4-2a-r1 回炉执行中**（10:15:58Z 新 claim
  hubfire-B4-2a-r1-20260919T1015-a51c，hold_reason 已清）。
- **在途 B4-2a-r1 不受影响——执行者独立于火，自行完成收口**。收口后本板停于
  READY 且无火接续——此为预期态非异常。恢复两径同规：用户显式 /batch-relay
  重布防（换防协议 hub 变体），或手动会话按本板清单领批/处理呈批。
- 调度员会话自本增补起不再开批、不再补派（含执行者中途死亡亦不接管——停火令优先）。
- 板头执行指令转达条款规则（增补六定型）与门一/拟定者备源承载事实留存，
  重布防时随板面原文生效。

### 增补五 — 2026-09-19T12:01:02Z（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——用户点名旧火 automation-2988ca0b-…（调度员增补八
  所布）与板头存量 automation-aa40bf0e-…（增补三所布、增补四删火在案）均已亡，
  零清场动作；新火布防后 CronList 复核全局恰一条。
- 深度设计门（换防重走；口径=板内 plan 字段指向的《裁决书》/自含清单）：过——
  《裁决书》占位符 grep 零命中、执行清单机检 14 勾+8 开=22 与板头计数一致
  （调度员增补九 G-1/G-2 入板后口径）、org-ledger.jsonl 活跃（mtime 09-19 19:52+08）；
  check-relay plan 子命令照跑 exit=1：MISSING_SECTION 系自含清单非 writing-plans
  模板预期态，无 PLACEHOLDER 命中（增补三同款口径）。
- 换防复位（板不重建）：relay_started_utc 重锚 2026-09-19T11:58:59Z（熔断复位
  留痕）；batch_count 1→0；status READY/claim -/claimed_by -/claimed_at -
  /no_progress_count 0/hold_reason - 均期望态零改写；protocol 段 rev1+rev1.1 增量
  条款在册（增补/增补二所立），无需补齐；next_batch=B4-2a 收尾批锚不变；复位后
  board 机检 0 fail（1 warn=冻结旧行 R3 预期）；板头 automation_id 字段行已锚定
  替换为新火 id（锚定计数=1 守卫过；历史日志旧 id 存量不动）。
- 新全局火=automation-3776af0e-7217-406a-802c-870cb88b6533（新 hub 调度会话创建，
  全局唯一 */10 轮转，服务本板+Synapse 板）。本板 last_dispatch_utc=09-19T08:55:10Z
  早于姊妹板 10:02:42Z——首班有效火先轮本板（next_batch=B4-2a 收尾批：门一备源
  承载异构审+门二实证终审→推送全部本地笔（实现笔 f5a8150+HOLD 板面笔 72e7e2f+
  [HUMAN-LOCK] 锁面笔）→守望 CI 至绿→勾选 B4-2a）。
- 板上既有条款自动生效：执行指令只携带未销案指令（调度员增补六定型）、门一/
  拟定者备源承载直至用户另行通知、UI 开批通道经验沿用历任实测累积（Ctrl+N/
  「取消选择当前项目」清空再勾选防反致解绑/调度侧 Edit 遇「文件已改」重读再
  落笔/主输入框 a11y 写入不生效须前台激活后 app 级 strategy=event 真实键盘写入，
  前台被锁连败 2-3 次即记欠账退出勿硬抢）。
