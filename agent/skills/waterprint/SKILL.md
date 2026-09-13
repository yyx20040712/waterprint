---
name: waterprint
description: WaterPrint 污水处理厂设计内核的 21 个 MCP 工具使用技能——建项目、算方案、读诊断、调参数、导出计算书／图纸／设计说明书。草稿——集成批随实装校对。
---

<!-- 契约头：路径 agent/skills/waterprint/SKILL.md｜职责：教 ZCode 用 WaterPrint 21 工具完成「参数化设计+诊断迭代+说明书生成」｜禁区：本技能不教 AI 手算任何工程数值（AI 永不算数——ADR-019）｜状态：草稿——集成批随实装校对（工具签名按 v2 设计书 D3 权威表誊录，实装后如有出入以实装为准） -->

# WaterPrint 设计助手技能（草稿）

> 状态：草稿——集成批随实装校对。工具签名与行为按 AI1 路线 v2 设计书
> D3 权威表（21 工具）编写；MCP 实装批落定后须逐条对照修正。

## 一、概述

WaterPrint 是一个污水处理厂设计内核：你给它一份「项目」（工艺单元图+
参数），它按规范公式（GB 50014-2021 等，全部带条文出处）算出每个构筑物
的尺寸／负荷／出水，并留全程计算迹（trace）。你的角色是**编排者**：

- **AI 永不算数**：任何工程数值（池容、流量、浓度、造价）都只能来自
  工具返回值或计算迹——禁止心算、估算、编造。需要数字时调工具。
- **AI 只做四件事**：理解需求→选种子模板建项目→依诊断调参数→组织
  工具产出（计算书／图纸／设计说明书）。
- 数字与公式一一锚定：说明书里每个计算值都带〔公式 ID〕，可回查
  trace 与条文——你写叙述文字时禁止新增任何数字（后检会拒绝）。

## 二、快速开始（全链示例对话）

用户：「帮我按市政污水 3.5 万吨每日的规模做一个 AAO 方案，出水一级 A。」

```text
你：wp_list_units(category="municipal")            # 看可用水线单元（≤36 行摘要）
你：wp_create_project(seed="municipal_34760")       # 以 golden 模板为种子建沙箱项目
你：wp_get_project_outline()                        # 节点+连接+参数摘要（确认拓扑）
你：wp_validate_design()                            # 结构校验（清单式，零计算）
你：wp_run_calc()                                   # 全厂计算（同步，<5s）→ 摘要+design_digest
你：wp_get_result_summary()                         # 达标判定+逐单元一行+质量平衡（≤1.5k token）
你：wp_get_diagnostics()                            # 三源回喂：warnings/convergence/mass_balance/effluent
你：wp_get_unit_detail(unit_id="municipal_aao")     # 需要深挖的单元按需回取
你：wp_export_calcbook() / wp_export_audit()        # 计算书 xlsx / 公式溯源 HTML
你：wp_export_dxf()                                 # 图纸
你：wp_export_report()                              # 设计说明书（Markdown，数值全锚定）
```

## 三、工具速查表（21 个——D3 权威表）

| # | 工具 | 组 | 批 | 功能与守护 |
|---|---|---|---|---|
| 1 | `wp_list_units` | 知识 | A2 | 36 单元目录（可按 category 过滤），≤36 行摘要 |
| 2 | `wp_get_unit_manifest` | 知识 | A2 | 单单元参数 schema（grid 档位/约束/说明） |
| 3 | `wp_query_knowledge` | 知识 | A2 | constraint_kb/coefficients 只读检索 |
| 4 | `wp_create_project` | 项目 | A2 | golden 种子白名单或空白新建，落沙箱 |
| 5 | `wp_get_project_outline` | 项目 | A2 | 节点+连接+参数摘要，token 友好 |
| 6 | `wp_validate_design` | 项目 | A2 | 结构校验直通，清单式零计算 |
| 7 | `wp_update_params` | 编辑 | A2 | 批量改参（grid 三面守护+undo 快照+逐条接受/拒绝清单） |
| 8 | `wp_run_calc` | 计算 | A2 | 全厂计算（同步 <5s），摘要+design_digest+结果文件路径 |
| 9 | `wp_run_enumeration` | 计算 | A2 | 单单元枚举 Top-N（默认 10）摘要+全量路径 |
| 10 | `wp_run_design_map` | 计算 | A2 | 可行域比例+边界摘要+全量路径 |
| 11 | `wp_get_result_summary` | 结果 | A2 | 达标判定+逐单元一行+质量平衡偏差（≤1.5k token） |
| 12 | `wp_get_diagnostics` | 结果 | A2 | 三源回喂：warnings 六键（含调节方向）+convergence/mass_balance/effluent |
| 13 | `wp_get_unit_detail` | 结果 | A2 | 单单元全量结果按需回取 |
| 14 | `wp_get_trace_excerpt` | 结果 | A2 | 按单元/公式 ID 抽 trace 片段 |
| 15 | `wp_get_estimate_summary` | 结果 | A2 | 概算摘要（内存投影，无文件落盘） |
| 16 | `wp_get_layout_summary` | 结果 | A2 | 高程/场景聚合投影摘要（供说明书第 5 章） |
| 17 | `wp_export_calcbook` | 导出 | A2 | 计算书 xlsx |
| 18 | `wp_export_audit` | 导出 | A2 | 公式溯源审计 HTML |
| 19 | `wp_export_dxf` | 导出 | A2 | 图纸 dxf |
| 20 | `wp_export_ifc` | 导出 | A2 | 三维 ifc |
| 21 | `wp_export_report` | 导出 | A3 | 设计说明书管线入口（七章节 Markdown+数值锚定） |

v1 能力边界：**种子/既有项目的参数化设计+诊断迭代+说明书生成**——
不含拓扑编辑（不能加单元/删单元/连边；空白模板仅作零节点骨架）。

## 四、调参回路剧本（诊断驱动迭代至达标）

标准回路：**run → get_diagnostics → update_params → 重算 → trust 达标**。

1. `wp_run_calc()` 得到达标判定摘要；
2. `wp_get_diagnostics()` 读 warnings——每条警告六键齐全：
   `severity / source / message / param_key / condition_key / affected_unit_ids`；
3. **按 `warnings.param_key` 调节**（这是官方调节方向指针）：
   - 池容不足／超负荷 → 调对应单元的池数、档位参数；
   - 出水指标超限 → 看 effluent 裕度（margin<0 即超标），调泥龄/回流比/负荷类参数；
   - 质量平衡偏差大 → 看 mass_balance 的 closure_rel/delta_rel 定位单元；
   - 回路不收敛 → 看 convergence 的 iterations/final_residual；
4. `wp_update_params(patches=[...])` 改参——**只提 grid 档位内的值**；
   逐条接受/拒绝清单会告诉你哪些没改成（非档位值必入拒绝清单，别硬塞）；
5. 重新 `wp_run_calc()`，循环直至 `wp_get_result_summary()` 判定达标；
6. 收尾导出全套产物（calcbook/audit/dxf/report）。

## 五、产物说明与路径约定（沙箱五区）

沙箱根内五区（一切读写都限制在沙箱内，正式区只读）：

| 区 | 内容 |
|---|---|
| `projects/` | 项目文件（`.wp.json`）与项目锁（`.wp.lock`） |
| `results/` | 全量计算结果（`calc-{task_id}.json`，文件名带 design_digest） |
| `sessions/` | 会话日志（`{session_id}.jsonl`，逐工具调用留痕） |
| `exports/` | 导出产物（计算书 xlsx／审计 HTML／dxf／ifc） |
| `reports/` | 设计说明书（Markdown，含溯源索引） |

要点：
- 改参只对沙箱项目开放；正式区项目须先落沙箱副本。
- 结果文件名带 design_digest——改设计后旧产物的 digest 对不上=stale，
  消费前必须重算。
- 所有工具返回摘要 JSON（≤1.5k token）+`artifact_path`；细节经
  #13/#14 按需回取，不要一次拉全量。

## 六、错误处置对照

| 症状 | 处置 |
|---|---|
| `wp_update_params` 拒绝某条 patch（grid 拒绝） | 该参数只收 manifest 声明的 grid 档位值——先 `wp_get_unit_manifest` 看合法档位，再改提 |
| 产物标 stale（digest 不匹配） | 设计已变更——重跑 `wp_run_calc` 后再取结果/导出 |
| 枚举/设计图报无解诊断 | 读 `diagnose_infeasibility` 清单式诊断：按约束冲突对逐条放宽（grid 档位内）或换单元参数档 |
| 计算结果某单元警告越出建议带 | 非强条违背——可接受但建议按 `param_key` 调回常用带并在说明书叙述中说明理由 |
| 叙述稿被说明书后检拒绝（检出数字） | AI 叙述段禁止任何数字（阿拉伯/小数/百分比/中文数字/量纲紧邻）——支撑数值由程序注入，删掉数字改为引用结论 |

---
（本技能文档为 AI1 战役轨道丙交付草稿；集成批实装后逐条校对工具签名与
返回形态，并补充真实返回样例。）
