# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: RUNNING
- automation_id: automation-9d069f57-4d51-4327-a9e2-27cad5d0352f
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-19T23:25:42.868Z
- claim: hubfire-B4-2b-r1-20260919T2331-e3b7
- no_progress_count: 0
- checked_total: 22
- checked_done: 17
- protocol_rev: 1
- last_dispatch_utc: 2026-09-19T23:24:19.203Z
- relay_started_utc: 2026-09-19T14:24:01.889Z
- batch_count: 2
- max_batches: 60
- max_wall_hours: 90
- hold_reason: -
- last_handover: 2026-09-19
- claimed_by: hub-fire-executor-session
- claimed_at: 2026-09-19T23:25:42.868Z
- next_batch: B4-2b 回炉实装批：R-B42b-1~4 四问已裁（见增补九+账本 ruling 行）——免再呈，直接按 .workflow/b4-2b/review-report.md 恢复路径 S1~S7→门二→锁面→推送守望→勾选

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
- [x] B4-2a｜碳核算·前置一：能耗药耗计算面（**计算逻辑呈用户审查——R-B42a-1~4 四项全批**）
- [ ] B4-2b｜碳核算·前置二：运行成本面（opex）
- [ ] B4-2c｜碳核算本体（先详细调研再立项——三轮裁决④）
- [ ] B4-3｜联合枚举（ADR-005 解冻须用户裁决）
- [ ] B4-4｜AI 集成深化
- [ ] B4-5｜矿井水段二（norms 追认前置）+软著（用户亲查计算核心优先）

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

### batch B4-2a 收尾批 — 2026-09-19 12:16Z~（hub 火执行者会话：双门审+推送守望，B4-2a 勾选收官）
- 门一（ops-gate1-k2 备源承载——用户指令 2026-09-18 未销案；审包 1454 行自包含=.workflow/reviews/b4-2a-gate1-package.md）**B0/W3/N6 有条件放行**：W-1 系数库四键消费面注记错标（TS-F12/13→实为 TS-F15/16；BZ-F12/13→实为 BZ-F19/20——旧式不消费泵效率/水密度）→处置笔 91bfb92 改正（纯注记面零数值变化）；W-2 自报「泵 1510」算术不合（4525+1510+1178=7213≠7240）→门二独立实跑 power_pump=1536.54 与 golden 锁定值逐位一致=简报转写笔误非代码缺陷，呈批报告已勘误、本条勘误为 1537（加和闭合 4525+1537+1178=7240）；W-3① 锁面笔 tiaojiechi manifest 未披露改动=纯重排（TJ-F14 移至 TJ-F13 后内容零变化——git show diff 实证）→本条补披露，教训=锁面笔逐文件动机清单须覆盖 stat 全量（含无语义重排）；W-3② 六单元能耗键未入 out_dims=**非漏登**：out_dims=消费投影非义务全集（check_out_dims 规格注记「③非第二真源」），aao/cass 五键登记系图纸投影取数（drawing_projection_municipal L166-204 fields+dim_of），六单元能耗键无图纸/详情消费面，盲登记将胀 l7 non_drawn 锁面期望 29→31 须再走 [HUMAN-LOCK]→挂账（能耗键消费面立项时随批登记）。N-1~N-6 记档（N-2 CASS duty 风机容量补偿物理口径供 B4-2b 复核/N-4 docstring 措辞/N-6 CASS 枚举面同步评估——组织账本 gate1 行）。
- 门二（ops-probe 独立重跑矩阵——绑定档案已随 2026-09-19 用户裁决改随宿主会话模型，B4-1 model-not-found 欠账自愈）**7/9 GREEN**：M3 server 315 passed/M4 gen_status 零漂移 2158B（锁面 303+ADR 24+coefficients 1.3.0 三数核实）/M5 check_readonly 303 键/M6 能耗值独立复算（亲跑内核非读期望）municipal design power 4525.34/1536.54/1177.87/7239.75 kWh/d 三族和=total 浮点精确相等+比电耗 0.208274（pump 期望 1510 偏差+1.76%=A1 转写误差与 W-2 同案闭卷）+mine 3420.58/1753.44/133.74/1095.90/M7 跨进程 serialize 双锚字节恒等（539381B sha256=golden 锁定锚 a847f491…）/M8 loop·recycle 回流增量 1.13~1.37% 带内+四案全工况零磁种毛耗键/M9 推送面范围核对 server/webapp 零变更+data_version 1.3.0。**两 RED 同根因=relay.md 超 500 文件预算**（HEAD 523 行=治理工单板面笔 59e462e 入库时已超限；M1 check_file_budgets+M2 arch 镜像 1 red）→处置=本笔滚动归档。
- 板面滚动归档：调度员增补五~batch B4-1 补记段 260 行原文零改动纯迁移 relay-archive-002.md；主板压缩回预算内（M1/M2 RED 同笔吸收）。归档件一号 396 行近满续二号档。
- 推送面（收口即推送+守望 CI 至绿——三轮裁决④）：a1bc269 认领（已推）+f5a8150 实现+72e7e2f HOLD 板面+91e1b3a [HUMAN-LOCK] 锁面+91a663c 回炉收口+59e462e 治理工单+4fce000 本批认领+91bfb92 处置+本板面笔+收口终笔。认领笔未提前单独推送注记（板面超预算态下推送必红——4fce000 消息在档）。
- Rulings：本批无新增（W-3②=主控级挂账处置；A2 根因 HEAD 既有非本批引入；无触发用户裁决项新事实）。
- 账本：gate1（B0/W3/N6 有条件放行·备源绑定承载）/probe（7/9 GREEN·绑定自愈）/impl 三行；health-scan 见终报。勾选 14→15/22（B4-2a）；next_batch=G-1（治理小批·用户直排，调度员增补九）。CI 守望绿证随终笔补记。
- CI 守望链（收口即推送+守望 CI 至绿——三轮裁决④）：首跑 run 35443805720（ed891c7 面，a1bc269 起八笔）10 job 中服务层 3.13/3.14 两红——唯一真红=test_compare AAO metrics 23≠28；根因=本地 server venv 旧 core 站点拷贝遮蔽（门二 M3「315 passed」系假绿，账本 incident 行勘误登记），CI 新装暴露。→R-B42aF-1 用户对话内批准锁面笔（第四次锁面摩擦事件——调度员增补九口径随批呈报提醒）→[HUMAN-LOCK] 11f3cc7：期望 23→28（B4-2a 能耗五键入 aao out_dims，图纸投影取数面；非消红——门二独立复算 28 键全在场在先）+lock_tests 全根清单重锁 303 键（COST2 经草稿器命令显式通过）+server venv 改 uv 编辑安装去假绿根因（真值面全量 server 315 passed+run_gates 15 绿复验）。→二跑 run **35444614717 全绿**（success，11f3cc7 面）——守望闭环。收口终笔推送面=本笔（板面终笔，预期绿，下批首跑覆盖核对——B3-c 补记二口径）。
- 会话终态：B4-2a 一批完成（含双门+首跑红→用户裁决→锁面笔→二跑绿全程），勾选 14→15/22，READY，claim 归位；next_batch=G-1 治理小批（aao/cass 同族公式族结构恒等机器断言+显式 delta 清单——用户直排，G-2 随后）。

### batch G-1 — 2026-09-19 13:23Z~21:5X（hub 火执行者会话：同族一致性门禁，用户直排工单①收官）
- 交付（三笔：实现 13e7e84+处置 a38a3e5+处置二 ef511a6，均经推送守望 CI 绿 run 35447156038）：第十六门禁
  scripts/check_family_parity.py（主件 375 行）+共享库 family_parity_lib.py（137 行，same_layer_lib 先例拆件——
  处置笔二后 502 行超宪法 §2 预算墙拆解析层）+run_gates GATES 挂载（门禁数基线 15→16）+file-contracts §4 双件登记
  +status.md 重生成（gen_status --check 2158B 零漂移）。断言五层：①完整性（两包全部公式 ID=族对∪独有清单精确集合
  相等——分叉无「不登记」路径）②恒等对（RHS 别名归一+空白归一恒等+符号集/逐符号量纲/输出符号/输出量纲四面对齐）
  ③delta 对（表达式豁免但双向符号集差=声明精确集合+交集量纲全检+过期退役断言）④out_dims 镜像满额断言（17/17，
  例外 2 键 _MIRROR_EXEMPT 显式登记——l_pool_raw/b_pool_raw AAO 侧不投影 raw 中间键，B4-2a W-3② 消费投影口径）
  ⑤声明区自检（族对无重复/别名无自环链式多对一/族对∩独有空/解析平账三数对齐——含属性调用形态/例外表死条目过期）。
  声明面：恒等 15 对（需氧 4/污泥 3/曝气 2/能耗 1/几何平移 3/容积平移 2）+delta 4 对（AO-F23↔CA-F31 duty_ratio
  周期曝气 R-B42a-1 审查在档/AO-F24↔CA-F32 搅拌容积取面/AO-F20↔CA-F28 曝气头取面/AO-F19↔CA-F11 构造容积口径）
  +别名 4 对（v_o↔v_load/t_p↔t_selector/v_anaerobic↔v_selector/w_stir_bio↔w_stir）+独有 aao 6/cass 14 逐条注记。
- 红绿演练四笔留证（.workflow/g1-drills.md 仓外档案）：恒等对系数分叉红（4.57→4.50 精确指向 AO-F10↔CA-F20）/
  公式改名完整性双红/delta 过期红（CA-F31 删 duty_ratio→「应退役并入 _PAIRS」）/镜像缺键红（删 e_stir 行→精确
  指向 AO-F25↔CA-F33）——还原后全绿+工作树零残留。开发自证一笔：首版 delta 声明错误被门禁自身抓红（别名在
  delta 层生效语义一致性顺带实证）。
- 双门：门一（ops-gate1-k2 备源承载——用户指令 2026-09-18 未销案）三轮收敛 **B0/W0/N2 放行**（一审 B0/W4/N5
  有条件→处置笔：W-1 解析平账实修/W-2 镜像满额断言实修（顺带抓真差异一处入例外表）/W-3 delta 豁口挂账 docstring
  注记/W-4 呈报；二审 B0/W1/N4（W-1r 属性调用文案>实现）→处置笔二真覆盖收口+N-b 例外自检超建议加做；三审全闭环
  放行）；门二（ops-probe 随宿主模型）两轮 **8/8+5/5 GREEN**（声明面 9 恒等+4 delta 亲核/完整性计数 25/33 交叉
  吻合/aao+cass 包内测试 62 passed/红演练两轮独立复现精确）。
- **Rulings 呈报（用户裁决位，不阻断）**：门一 W-4——工单括注四族（需氧量/曝气/污泥/能耗），实现把 manifest
  头注既有「CASS 同族平移」声明面的几何/容积族（AO-F16~F18↔CA-F24~F26+AO-F1↔CA-F3+AO-F3↔CA-F4+AO-F19↔
  CA-F11）一并机器化（19 对全覆盖+两侧独有显式清单）。依据=工单主词「同族公式族」涵盖既有平移声明面+完整性反向
  断言使任何一侧新增公式逃不掉登记；如裁定收缩=机械移除（移入 _SOLO_* 一行操作）。N 级记档：行数账目以 CI 实跑
  为准/豁免期 cass 侧掉键静默（消费投影口径可接受）/工厂封装归静态读不变量明文排除/单向归一 cass 侧碰撞不检。
- 卫生小记：本批三次 commit 触发 git geometric-repack 维护任务权限失败（multi-pack-index Permission denied）
  ——提交/推送均成功不阻断，2026-09-13 只读位残留同族现象，留观（若再现按 .git/maintenance 权限排查）。
- 账本：impl/gate1（三轮终态）/gate2（两轮终态）三行在册；health-scan 收口前 RED=0/WARN×4（均历史欠账：设计链
  同源历史行/27 行缺 usage 历史记账/cache 字段/cfg 漂移——非本批引入）。盘点件=.workflow/skills-inventory-G1.md。
- 勾选 15→16/22（G-1）；next_batch=G-2；收口判定⑤READY（勾选有进展 no_progress 归零；batch_count 2/60、
  墙钟 ~2h/90h 熔断远未触发）。本笔为收口终态置位（置 READY=最后一笔，此后本会话零板/仓写入）。

### 调度员欠账行 — 2026-09-19T14:1XZ（hub 调度会话：G-2 开批 UI 通道连续两班失败）
- 事实：WaterPrint 全合格态下（READY ∧ 静默窗过 ∧ 实物静默 ≥5min ∧ 熔断未触发）调度员连续两班（~14:06/~14:10）
  UI 开批未成——a11y 观察缓存与活树错位致点击校验连续拒绝（action_sent=false 零误触；第三次尝试取消绑定与
  展开菜单两笔已成功，菜单内容观察再次错位后按「连败 2-3 次勿硬抢」停手）。last_dispatch_utc 未写（仍
  13:21:13Z），板保持全合格态，G-2 开批顺延至下一班火重试。
- 处置预案：若续败按协议降级（UI 通道失败欠账 → 会话内直跑承载）或呈用户处理；本行即欠账登记。

### 增补六 — 2026-09-19T14:14:16Z（hub 停火：用户令删火）
- 用户在 hub 调度会话下达删火令：全局轮转火 automation-3776af0e-7217-406a-802c-870cb88b6533
  已 CronDelete（回执 deleted:true，CronList 空集复核）。本条为调度员尾部纯追加，
  claim/状态字段未动；板头 automation_id 字段行保留旧值仅为历史审计指向。
- 本火任内战果：两批完成——B4-2a 收尾批（12:14:47Z 发布，勾选 14→15）+G-1 治理小批
  （13:21:13Z 发布，勾选 15→16/22，batch_count 0→2）；G-2 开批因调度员 UI 通道连败
  两班欠账顺延（欠账行在册）——停火后无火重试，G-2 由用户择径（手动会话按本板清单
  领批，或日后重布防由火班续）。
- 本板现 READY（无在途执行者），停火后停于 READY 无火接续——预期态非异常。恢复两径
  同规：用户显式 /batch-relay 重布防（换防协议 hub 变体），或手动会话按本板清单领批。
- 调度员会话自本增补起不再开批、不再补派（停火令优先）。
- 板头执行指令转达条款规则（调度员增补六定型）与门一/拟定者备源承载事实留存，
  重布防时随板面原文生效。

### 增补七 — 2026-09-19T14:24:01.889Z（hub 换防：新调度会话接替，重布全局轮转火）
- 旧火核查：CronList 空集——用户点名旧火 automation-3776af0e-…（增补五所布、增补六
  删火在案）已亡，零清场动作；新火布防后 CronList 复核全局恰一条。
- 深度设计门（换防重走；口径=板内 plan 字段指向的《裁决书》/自含清单）：过——
  《裁决书》占位符 grep 零命中、执行清单机检 16 勾+6 开=22 与板头计数一致、
  org-ledger.jsonl 活跃（mtime 09-19 21:54+08）；check-relay plan 子命令照跑 exit=1：
  MISSING_SECTION 系自含清单非 writing-plans 模板预期态，无 PLACEHOLDER 命中
  （增补三/五同款口径）。
- 换防复位（板不重建）：relay_started_utc 重锚 2026-09-19T14:24:01.889Z（熔断复位留痕）；batch_count
  2→0；status READY/claim -/claimed_by -/claimed_at -/no_progress_count 0/
  hold_reason - 均期望态零改写；max_batches 60/max_wall_hours 90 维持（用户布防
  指令明示 22 项维持 60/90）；protocol 段 rev1+rev1.1 增量条款在册（增补/增补二
  所立），无需补齐；next_batch=G-2 锚不变；复位后 board 机检 0 fail（1 warn=冻结
  旧行 R3 预期）；板头 automation_id 字段行已锚定替换为新火 id（锚定计数=1 守卫过；
  历史日志旧 id 存量不动）。
- 新全局火=automation-9d069f57-4d51-4327-a9e2-27cad5d0352f（新 hub 调度会话创建，全局唯一 */10 轮转，服务本板+Synapse
  板，首班 14:34Z）。姊妹板 Synapse RUNNING 在途（b32 B 票心跳新鲜）非轮转候选——
  **首班有效火先轮本板，G-2 拆件配方回写宪法优先补开**（用户布防指令明示；调度员
  欠账行处置预案随行：前调度会话 UI 通道 a11y 观察缓存错位连败两班，本调度会话
  a11y 状态全新，若再现连败按预案降级会话内直跑或呈用户，勿硬抢）。
- 板上既有条款自动生效：执行指令只携带未销案指令（增补六定型）、门一/拟定者备源
  承载直至用户另行通知、UI 开批通道经验沿用历任实测累积。


### 调度员欠账行二 — 2026-09-19T14:33:49.607Z（hub 调度会话：G-2 开批 UI 两径受阻，让位下一班）
- 事实：本板全合格态（四条件过：READY ∧ 静默窗 69min≥30 ∧ 实物静默 板面 5.2min/git
  28.6min≥5 ∧ 熔断 0/60·6min/90h），开批 UI 通道连败三试——①「新建任务」按钮滚出
  侧栏视口（任务标签堆积），a11y 树 400 元素封顶被裁：AXPress 首试即拒（actions 仅剩
  AXScrollIntoView）、AXScrollIntoView 后全量树不复现；②Ctrl+N 键盘径被前台守卫拒
  （action_sent=false 零误触）——前台=Synapse_remake node_modules electron.exe
  （b32 B 票 Electron 44 实测占用，观察窗内 pid 34332→29572 重启一次=测试循环进行中），
  按「在途勿动+前台连败勿硬抢」纪律不强抢。last_dispatch_utc 未写（仍 13:21:13Z），
  板保持全合格态。
- 处置：让位下一班火重试（缓开一班零成本，G-2 顺延）；若续败按欠账行一预案降级
  （会话内直跑承载）或呈用户处理；本行即欠账登记（欠账行一在册，本行为第二条）。

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


### 增补八 — 2026-09-19T23:01:19.723Z（hub 调度会话：用户裁决落板+HOLD 解除复位，火班续跑）
- 用户裁决（对话宣示「我裁完了」+回执确认）：**G-1 呈批三项全按推荐确认**——①范围维持
  19 对全覆盖（几何/容积平移族纳入正式成立，门一 W-4 呈报项销案）；②delta 豁口挂账维持
  （公共符号系数漂移不在断言面属知情差异，docstring 注记为准）；③门一/拟定者备源承载
  指令继续有效未销案。账本 ruling 行 2026-09-19T22:47:35Z 已落（本增补即板面回执补记，
  原「随 G-2 批次日志首段补记」计划已过时由本条承接）。
- **B4-2b 四问（R-B42b-1~4：①C 案落位②factor.opex.* 五键③计算口径挂账边界④锁面笔
  授权）裁决内容未在案**——全仓扫描（板面/账本/.workflow/git 近 30min 唯一改动=上述
  G-1 ruling 行）+用户回执仅涉 G-1 三项。回炉实装批**开工首步=向用户呈四问补裁**
  （B4-2a 先例径：AskUserQuestion 四项→回执落账→回炉实装），批准前禁动仓禁锁面。
- HOLD 解除（用户管理指令·单项目恢复径）：status HOLD→READY、hold_reason→-；
  claim/-、no_progress_count 0、batch_count 2、last_dispatch_utc 15:26:43.792Z 均不动
  （HOLD 恢复非换防，熔断不复位）。
- 火班续跑（用户 Q2 裁决）：全局火 automation-9d069f57-…（用户保留未删）仍在册——
  下一班有效火按四条件核（本笔后板面 mtime 静默 ≥5min）即注入 B4-2b 回炉实装批。
- 复位后 board 机检随本笔复核 0 fail。

### 增补九 — 2026-09-19T23:17:06.030Z（用户裁决落板：B4-2b 四问+R-G2-1 全回执，回炉批免再呈）
- **B4-2b 四问（R-B42b-1~4）裁决在案**（本会话 AskUserQuestion 两轮，授权链与论证全文=账本
  ruling 行）：①落位 C 案+②factors 五键=用户委托主控按「最规范、最有利于后来者维护代码」判据
  裁定（裁据：总线稳定红线+同构第五例；unit_prices 备选须同步三处孪生 env 构造+flows 满墙强制
  拆件+server 触碰面扩——翻案通道开放）；③计算口径（F1~F3+365 天+逐工况 sparse+挂账边界）
  批准；④锁面笔授权（golden 双锚+data_version 1.4.0 串+键集钳制+test_app_opex.py+manifest
  303→304+gen_status 重入库——[HUMAN-LOCK] 工序按 B4-2a 先例）。**回炉实装批开工免再呈四问**，
  直接按 .workflow/b4-2b/review-report.md 恢复路径 S1~S7 开工。
- R-G2-1（门禁脚本 _lib 拆法入宪指针票面外搭车）维持入宪——G-2 呈报项销案。
- 本条为用户直排裁决落板（增补八同款：READY 态增补，写前回读 claim=- 无占用；本笔后板面
  mtime 静默 5min 起火班四条件重新可满足）。
