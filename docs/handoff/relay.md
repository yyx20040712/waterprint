# 批次接力状态板（机器门控文件——会话按此行动，人可读）

> 项目：WaterPrint 智水蓝图 ｜ 战役裁决书=docs/design/2026-09-18_complexity-governance-ruling.md
> （三轮用户裁决+五方案设计定案，下称《裁决书》；本板清单为《裁决书》批次编排的
> 执行投影，排程冲突时以《裁决书》为准并回改本板）。
> 建板：2026-09-18 主控会话（复杂度治理批 0/1/CI 修复批收口后——本板取代仓外
> 一次性交接文档；历史交接件在仓外档案区只追加不回改）。
> 前任交接：`E:/zcode_md/治理批-复杂度治理-2026-09-18/00-交接文档-新会话继续.md`
> （2026-09-18 同日建立——内容已并入本板首批批次日志，克隆者以本板为准）。

- status: RUNNING
- automation_id: automation-2988ca0b-9af5-4ae0-a8ed-319602ec2ddf
- shared_fire: true
- plan: docs/handoff/relay.md#执行清单（自含清单，收口 grep 本文件 `- [ ]` 计余量）
- spec: docs/design/2026-09-18_complexity-governance-ruling.md
- poll_interval_min: 10
- fire_budget_min: 120
- last_dispatch: 2026-09-19T11:14:24+08:00
- heartbeat_utc: 2026-09-19T03:16:30Z
- claim: executor-B4-1-20260919T1116-a7f3
- no_progress_count: 0
- checked_total: 20
- checked_done: 13
- last_handover: 2026-09-19
- claimed_by: executor-B4-1-20260919T1116-a7f3
- claimed_at: 2026-09-19T11:16:30+08:00
- next_batch: B4-1（第四波首批：操作链集中 debug 观测面——复用 calc-diag 独立 artifact（ADR-012）+任务事件流+trace 聚合，新增 GET /api/debug/ops-chain 或 events 流扩展+webapp 诊断 pane；前置槽位=批 3a 投影共享件已就绪——实现批双门）

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

> 历史批次日志滚动归档（B2-6 收口起）：2026-09-18 建板~B2-4 增补二段
> （batch 0~3 与 B2-1~B2-4 全量、调度员增补一/二）已迁
> relay-archive-001.md（原文零改动纯迁移，追加勿改写纪律延续至归档件）；
> 本板自调度员增补三起留活跃链，满 400 行再滚下一档（滚动阈值口径与
> 归档件头注一致）。

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

### batch B2-5 — 2026-09-19 02:25（hub 火执行者会话：批 2 实装步②，HOLD 呈报——代码面完成+镜像锁面待用户批准）
- 交付（代码面 commit d223a6c 本地待批后随锁面笔推送）：formulas.py 487 行机制件拆子包四件——
  spec（规格声明+DSL 解析，143 行）/store（登记真源+静态校验+查询面，145 行）/apply（唯一
  求值正门，188 行）/\_\_init\_\_（聚合正门九名 re-export，37 行），预算 150/150/200/40 全过；
  429 条目留 manifest 原位零搬动（D1-B）；file-contracts 删旧 1 行增四件行（精确行数注记
  机锁）；幂等哨兵=\_\_init\_\_ 批次行 b2-s2-formulas-package+聚合 import 三行（W9）。
- 等价性证据（全绿面）：改造前后注册表 dump 逐行恒等（三段聚合入口 flows+manning+
  discover_units+插入序+sha256 指纹，TOTAL=429——门二独立重跑复证零差异）+代码体 19/19
  成员字节恒等（git show 旧件 vs 新四件逐成员 diff，N2 机器闭合）+golden 4 绿+registry
  55 绿+run_gates 15 绿+gen_status 零漂移（2158B）+§1a 再生成 27 节点零 diff（探针 4）。
- 两处主控级校准（门一对抗后成立）：①聚合 import 书写序取 ruff 字母序（定案序 spec→store
  →apply 为字面；字母序下依赖序经链式 import 隐式保持且模块体执行序逐帧等价——门一审
  推演加强确认；isort 为 15 门禁硬性面，noqa 豁免留 lint 债否决）；②dump 探针字段路径
  e.spec（定案模板 s.expression 对 _Entry 包装两侧同错，校准对称适用零损）。
- 门审：门一（ops-gate1-k2 备源承载，审包 593 行自包含）**B0/W0/N8 PASS**——六项强制
  审项全过+两独立推演（429 注册序零影响=import 期零注册+注册序归 manifest 导入序+
  _REGISTRY 单例；apply 遮蔽面存量消费零回归，import…as 形态新陷阱）。N3/N4/N5 批内
  修复（遮蔽警示注释/溯源口径统一/spec 输出补 _normalize_dim）；N1 公共名跨件边（apply→
  spec.InvalidFormulaError 直连边，三角非纯链）本笔补记；N6/N7/N8 挂账（镜像交互入设计
  模板/零符号公式 StopIteration 既往缺陷/assert -O 模式——均非本批引入）。门二（ops-probe
  独立重跑未读主控结论）矩阵 **10/10 无 RED**（含薄壳实效双向验证：拷入 6 passed/移除
  复现红/tests 面零残留）。
- **HOLD 根因（R-B2-5-1 呈报）**：镜像规则（test_mirror_rule，永续激活）对拆分新增三
  源件机械触发镜像测试义务（test_spec/store/apply.py 按文件名全树匹配）；新增测试=三
  连锁（manifest 新键+只读位+镜像件）→触碰三信任根→[HUMAN-LOCK] 人类批准墙（AGENTS
  §7「AI 只能起草不得自行提交」）。CI core job 跑 tests 全量含镜像规则——代码面推送必
  红，「收口即推送+守望 CI 至绿」不可达。定案 §3.7「零新增测试文件确认」+白名单禁改
  core/tests/\*\* 漏检此交互（审核 W12 未覆盖）。三替代（noqa/改镜像规则自削门禁/自行
  提交）均违制度否决。**处置=HOLD 呈报**：三件薄壳（最小义务=导入冒烟+公开面在场；
  行为主体保留在既有 test_formulas.py——孤儿测试不违规）起草于 .workflow/probes/b2-5/
  mirror-tests-draft/（apply 件经 importlib 取子模块对象——正门 re-export 函数遮蔽
  子模块名），实效已双向验证。**请用户批准：镜像测试三连锁 [HUMAN-LOCK] 锁面笔**
  （批准后拷入三件+lock_tests.py 重锁 296→299+[HUMAN-LOCK] commit+推送 d223a6c 全部
  本地笔→CI 复绿→勾选 B2-5→B2-6 续跑）。
- 上批搭车兑现：设计书 §4.3-3 断言句勘误（B2-4 增补一 F-3 挂账——W10 载体=探针 3，
  本笔随批）；ci.yml pytest 步吞日志修法递延至锁面笔批（HOLD 收口无 CI 验证回路，
  next_batch 行已锚定修法口径）。
- 转达条款回执：执行指令携带的 B2-3 两项 Rulings 裁决回执（R-B2-3-1 追认/R-B2-3-2
  知悉）经核对**已由 B2-4 执行者销案**（批次日志 batch B2-4 在案+调度员增补三确认）——
  板头执行指令原文保留（换防时发布照原文携带的既定纪律），本批无重复销案动作。
- 账本：gate1（findings B0/W0/N8）/probe（10/10）/impl-HOLD 三行；health-scan RED=0/
  WARN×3（历史欠账回显：2026-09-13 设计链同源行/18 行缺 usage/1 行 in=0——非本批引入）。
- 勾选 8/20 不变（B2-5 主体完成唯镜像锁面待批，批准复绿后勾选）；CI 预告：本批推送
  （d223a6c+勘误+板面笔）首跑 core job 预期红=镜像规则（唯一红面，根因即 R-B2-5-1），
  批准后复绿——守望记录随终报。

### batch B2-5 补记 — 2026-09-19 02:35（CI 守望定性：预告兑现——红面=镜像规则唯一）
- CI run 35380008265（a186a0a 推送触发）：**红=内核质量 ×3 版本（3.12/3.13/3.14），
  唯 Pytest 步红**——Ruff/Mypy/import-linter 静态面全绿（与本地 772/773 唯镜像红
  同构，本地三重验证[本会话+门二独立重跑+薄壳实效双向]置信度充分）；其余 7 job
  全绿（前端构建/依赖审计/服务层×2/架构门禁/镜像构建/性能基准）。
- 红面定性=预告兑现（批次日志 batch B2-5 CI 预告段）：根因即 R-B2-5-1（镜像规则
  对新三源件机械触发义务），**非功能缺陷**——dump 逐行恒等+golden 4 绿+19/19
  成员字节恒等已闭环行为面等价。用户批准锁面笔后复绿路径已锚 next_batch 行。
- HOLD 期间火班纪律：见 HOLD 即不接管不重跑（hub 守卫——删火权归调度员，本板
  只置状态）；用户批准可经调度员转达（同 B2-3 Rulings 回执模式）。

### batch B2-5 补记二 — 2026-09-19 02:50（用户裁决 R-B2-5-1 销案+锁面笔落地——B2-5 全绿收口）
- 用户裁决回执（对话内 AskUserQuestion 两问）：**R-B2-5-1→批准薄壳三连锁；执行通道→
  本会话立即执行**。批准即构成 AGENTS §7 人类显式批准事件（AI2 U7 授权链同款模式），
  [HUMAN-LOCK] commit be086eb 首行带标签+逐文件修改动机（4 文件：三薄壳+manifest）。
- 三连锁执行细节：三薄壳拷入 core/tests/registry/→lock_tests.py 重锁——裸跑被 COST2
  只增不减守卫拦截（会挤掉 units_lib 包内 38 条目），按守卫指引携完整根清单显式重跑
  （agent/core/server 三根+units_lib 32 包内 tests），296→**299 键**新增恰 3 零删除，
  只读位同步设置。
- 复绿证据：全量 pytest **776 passed 全绿**（772+镜像规则修复 1+薄壳 3——数序吻合）；
  run_gates 15 绿（check_trust_root 本地模式=HEAD 触三信任根首行带标签过；check_
  readonly=299 键全对）；gen_status 零漂移（2158B）。
- 板面：HOLD→READY、B2-5 勾选（8→9/20）、next_batch=B2-6（步③验证型零动作步——
  ci.yml 吞日志搭车项随该批实施）。Rulings 待用户：无（本批 R-B2-5-1 已销案）。

### batch B2-5 补记三 — 2026-09-19 03:35（CI 守望终态：绿——收口闭环）
- 收口笔 f22cdca run **35386353427 全绿**（success，10 job 全过——含内核质量 ×3
  版本 Pytest 复绿=镜像规则红面消除实证）。红绿链完整：35380008265（预告红，
  根因 R-B2-5-1）→be086eb 锁面笔（[HUMAN-LOCK]）→35386353427 复绿——「收口即
  推送+守望 CI 至绿」闭环。本笔为纯板面绿证登记（推送触发的新 run 预期绿，由
  下批首跑覆盖核对，不再逐笔守望）。
- 会话终态：B2-5 一批完成（勾选 8→9/20），READY，claim 归位；next_batch=B2-6
  （步③验证型零动作步——白名单三态=新建无/修改无/禁改全仓；check_out_dims_
  consistency 绿+15 门禁全量+pytest core/tests 绿=确认性验收；ci.yml 吞日志搭车
  项随批实施）。

### 调度员增补四 — 2026-09-19T03:51:12+08:00（hub 停火：用户令删火，新会话换防交接）
- 用户在 hub 调度会话下达删火令：全局轮转火 automation-9d2ab6a4-8aa2-4f96-9a44-
  fa9b23577f85 已 CronDelete（回执 deleted:true，CronList 空集复核）。本条为调度员
  尾部纯追加，claim/状态字段未动；板头 automation_id 字段行保留旧值仅为历史审计
  指向。
- 本火任内战果：B2-5 一批完成（HOLD→用户对话批准 R-B2-5-1→[HUMAN-LOCK] 锁面笔
  be086eb→CI 全绿复绿闭环，勾选 8→9），B2-6 已于 03:46:01 发布并认领。
- **在途 batch（B2-6，claim hubfire-B2-6-20260919T0347-c31f9）不受影响——执行者
  独立于火，自行完成收口（翻票+提交+板回写 READY）**。收口后本板停于 READY 且
  无火接续——此为预期态非异常。恢复两径同规：用户显式 /batch-relay 重布防（新
  automation_id 回填本板，换防协议 hub 变体），或手动会话按本板清单领批。
- 调度员会话自本增补起不再开批、不再补派（含执行者中途死亡亦不接管——停火令
  优先）。
- 板头执行指令中的转达条款（B2-3 两项 Rulings 裁决回执——已由 B2-4 销案）与备源
  承载事实留存原文，重布防时随注入指令照原文携带。

### batch B3-a — 2026-09-19 05:06（hub 火执行者会话：批 3 第一步·server 投影共享件收敛，完成）
- 交付（commits af73497+8c49498+本板面笔）：services/_shared/ 新子包（包根薄壳 14 行+latest_calc.py 67 行）——latest_calc_result(ctx, project_id, *, not_found) 返回 (task_id, result) 二元组（ENG4 D2 信息超集口径——溯源回显面携 task_id，四单值面解包丢弃）；无结果 raise not_found 注入消费方领域 404 异常类（异常→HTTP 码经 main domain_error_codes 类名义表，类型与消息文本收敛前后逐字恒等）；星型单向唯一依赖=services/__init__ ServiceContext（包根不回指子模块无环——import-linter layers+UF-33 双契约 KEPT 机器确认）。
- 七消费面改接：scene/elevation/cost/exports_io/compare/trust 六份 def 复制同批删除（禁并存，宪法 §2）+exports 转手 import 改直连共享件；孤儿 import 清理四处（scene Mapping+Any/cost Mapping+Any/elevation Any/exports_io ExportSourceNotFoundError）；六处头部规格 R1 注释改共享件口径（模块 docstring 经查无复制叙述——门一 N3 定谳）。契约同步：file-contracts 增 _shared 两行+exports/exports_io 迁出注记+五行消费面描述更新，gen_contract_lines 刷新注记（37 处全吻合，门一算术复算八处全中）。
- 等价性证据（行为零变闭环）：异常类型/消息文本/解包形态/循环体四恒等（门一逐面对账+exports 异常对象同一性推演——旧路径 exports→exports_io raise exports_support.ExportSourceNotFoundError 与新路径 not_found 注入为同一 class 对象）；server pytest 313 passed 全绿；门二共享件语义三验 5/5（混合序列恰取唯一合法项+多合法取注册序最末+空/全非法 raise 注入类且消息逐字相等——探针仓外留存）。
- 门一（ops-gate1-k2 备源承载，审包 550 行仓外快照）**B0/W0/N6 PASS**：N1/N5 批内处置（共享件 docstring 补直连面口径澄清+not_found 单消息构造约定）；N2/N3 包外 grep 定谳零动作（exports_io ctx.manager 零残留/五件 docstring 无陈旧叙述）；N4 残余由门二 5c+pytest 兜底；**N6 记录在案**：site.py 持同类「最近结果」读取但语义故意不同（无结果降级 uncalculated 全量 200 非 404）——正确排除本批收敛，后续批次勿误读为漏收敛。门二（ops-probe 独立重跑）矩阵 **8/8 全 GREEN 零 RED**（pytest/run_gates 19 绿/gen_status 零漂移/import-linter 2 kept/语义三验/星型单向/旧 def 零残留/接线六面）。
- Rulings 回执核对（执行指令转达条款）：B2-3 两项（R-B2-3-1 追认/R-B2-3-2 知悉）经核对**已由 B2-4 执行者销案**（batch B2-4 日志+调度员增补三/五在案），本批无重复销案动作，板头执行指令原文照存。本批新增 Rulings：**无**（实装与《裁决书》方案二批 2a 字面吻合、准入五条全过、零未规划裁决项）。
- 账本：gate1（B0/W0/N6）/probe（8/8）/impl 三行；health-scan RED=0/WARN×3（历史欠账回显，非本批引入）。锁面零动作（零新增测试文件——六消费面既有用例经 import 间接覆盖，信任根零触碰）。
- 勾选 10→11/20；next_batch=B3-b。CI 守望：本批推送首跑绿证随守望补记（收口即推送+守望 CI 至绿——三轮裁决④）。
### batch B3-a 补记 — 2026-09-19 05:1X（CI 守望终态：绿——收口闭环，网络抖动重跑定性）
- 收口笔 54db2f4 run 35393876653 首跑**红=唯一失败 job「前端构建（类型检查）」**：
  根因=corepack 下载 pnpm-10.34.5.tgz 时 TLS 断连（registry.npmjs.org 网络抖动，
  pnpm install 即挂、类型检查未起跑）——**CI 基础设施瞬时故障非代码面**（本批零
  webapp 改动；前驱 run 35390996897[809435a] 同 job 绿在案）。
- 处置=gh run rerun --failed 重跑失败 job → 同 run **conclusion=success 全绿**
  （10 job：架构门禁/内核质量×3/服务层×2/前端构建/镜像构建/依赖审计/性能基准）。
  「收口即推送+守望 CI 至绿」闭环；本笔为纯板面绿证登记（推送触发的后续 run
  预期绿，由下批首跑覆盖核对——B2-6 补记三同款口径）。
- 会话终态：B3-a 一批完成（勾选 10→11/20），READY，claim 归位；next_batch=B3-b
  （批 3 第二步：webapp SSE 生命周期双实现+域色双源→shared 收敛）。


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
