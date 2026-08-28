# Golden Cases（端到端验收用例）—— 录入指引

两个真实设计案例，数据落位 `core/tests/golden/golden_data/`（只读，与测试同锁）。
**期望值唯一合法来源 = docs/norms 手算对照表 + 旧系统结果（差异逐条解释）**；
实现者不得自编数字（§16 A9）。三单元（粗/细格栅、旋流沉砂池）对照表已签字生效
（2026-08-23，见 `docs/norms/`），golden 期望值录入自该三表起。

| 案例 | 规模 | 标准 | 源数据（旧系统） | 验收里程碑 |
|------|------|------|------------------|-----------|
| 市政污水 | 34,760 m³/d | 一级 A | `Graduation_design/ddesign_tool/resources/yyx.ddesign.json`（34 节点全厂：水线 13 单元 + 污泥线 + 集配水 + 高程配置） | M2 |
| 矿井水 | 43,836 m³/d | 地表水 III 类 | `Graduation_design/ddesign_tool/resources/kuangjing.ddesign.json`（8 节点矿井水线） | M3 |

## 已知口径陷阱（录入前必读）

1. **双轨不一致实例**：旧 `self_test.py` 中 `Q_avg_daily=34760.7, Kz=1.4,
   Q_design=0.57`——但 34760.7/86400×1.4 = **0.5632 m³/s**，旧值 0.57 与派生
   关系不符（正是新架构用派生属性根除的双轨病灶）。golden 录入**只取
   q_avg_daily 与 Kz**，q_design 由契约派生；差异写入 notes.md。
2. 旧文件的 `gdys_stss`（管道水头损失）与 `jcws_smbg`（进厂水面标高）在新
   架构折叠为高程子系统**输入配置**（§14.3），不再作为单元节点录入。
3. `constraint_overrides` 旧键需逐条对照 `data/constraint_kb` 新键名，
   映射关系记入 notes.md。
4. **录入前另须定**（`docs/business-logic.md` §10 待确认项）——**Q1
   已裁（Ruling 九裁④，2026-08-28）**：浓缩上清液/脱水滤液回流口
   **启用**（sup/filtrate 产股+厂首端回收边），但回流**边实装归
   GOLDEN3 批**（validate_edge R1 跨流体/_recycle_port 展开面+水量
   平衡断言+市政回流 golden 案例随之开档）——现行 golden 图
   sup/filtrate 口声明不连边（UF-11 Ruling ② 形态）；Q2 矿井水案例
   "III 类"执行口径（GB 3838 环评从严 or 地方标准，影响 B10 模块
   限值绑定）——I1 从严口径暂以 notes/source 文字承载（coefficients
   std.* 键族未建，补建归数据批挂账）。

## 录入步骤（每案例五步，预计 0.5~1 天/案例）

### Step 1 —— 从源文件提取设计输入

打开源 `.ddesign.json`，提取以下四类进 `input_project.json`：

- **进水与标准**：进水六指标（BOD5/CODcr/SS/NH3N/TN/TP）+ 水温 +
  `q_avg_daily`（m³/d，边界换算）+ `Kz`；出水标准绑定写 coefficients
  数据包的标准条目键（如 `std.gb18918-1a`），**不内联限值数字**。
- **工艺图**：逐节点 → `{unit_id（新命名，按 units_lib 归属表）,
  参数覆盖 dict（字段 ID → 值，逐条复核出处）}`；逐边 → 端口引用
  （注意水/泥类型与 recycle 标记——污泥回流边必须标 recycle）。
- **工况**：`checked_units`（勾选检修敏感性校核的单元列表，建议 M2 先
  勾 AAO 与二沉池两个）。
- **假设覆盖**：源文件中散落的默认假设（超高、安全系数等）→ 迁入
  `assumption_overrides`（键名对齐 registry/assumptions）。

### Step 2 —— 手算对照（docs/norms 流程）

按 `docs/norms/README.md` 流程摘录条文并手算，**每案例至少覆盖**：
进水泵房设计流量与扬程、AAO 有效容积与停留时间、二沉池表面负荷与
直径、各污泥环节湿泥量与 DS、出水浓度与达标裕度（design/avg 两档）。
每项标注条文号；与旧系统结果差异逐条解释（口径不同/旧错——参照
上面 0.57 的例子，预期会有一批）。

### Step 3 —— 写 `input_project.json`

语义模板（字段最终以 M1 `contracts/project_schema` v1 实现为准；
冲突时走解锁流程修订**数据文件**，不得改测试）：

```json
{
  "format_version": "1.0",
  "design": {
    "influent": {"q_avg_daily_m3d": 0.0, "kz": 0.0,
                  "BOD5": 0.0, "CODcr": 0.0, "SS": 0.0,
                  "NH3N": 0.0, "TN": 0.0, "TP": 0.0, "temp_c": 0.0},
    "effluent_standard_ref": "std.<数据包键>",
    "nodes": [{"unit_id": "municipal_aao", "params": {"字段ID": 0.0}}],
    "edges": [{"src": ["<unit>", "<port>"], "dst": ["<unit>", "<port>"],
                "recycle": false}],
    "checked_units": ["municipal_aao"],
    "assumption_overrides": {"<假设键>": 0.0},
    "elevation": {"inlet_water_level_m": 0.0}
  },
  "view": {},
  "metadata": {}
}
```

### Step 4 —— 写 `expected_summary.json`

**现行结构（municipal_34760 定型 2026-08-26，GOLDEN2 扩面 2026-08-28；
85 锚 = effluent 30 + design_dims 55[41 市政+14 污泥]）**：

```json
{
  "case": "案例标识",
  "checked_units": ["受检单元 unit_id 列表（承载 design_offline_* 工况集）"],
  "condition_keys": ["design", "avg", "design_offline_<unit_id>", "..."],
  "design_dims": {"<unit_id>.<dims 键>": {"value": 0.0, "source": "..."}},
  "effluent": {"design": {"BOD5": {"value": 0.0, "source": "主线实跑 HEAD=<hash>"},
                          "CODCR": {}, "SS": {}, "NH3N": {}, "TN": {}, "TP": {}},
               "avg": {}, "design_offline_<unit_id>": {}},
  "generated": {"engine_version": "...", "data_version": "..."},
  "m3_deferred": {"estimate_total": {"value": 0.0, "source": "...",
                                     "abs": 1e-12, "rel": 1e-12},
                  "total_sludge": {"value": 0.0, "source": "...",
                                   "abs": 1e-12, "rel": 1e-12}},
  "tolerance": {"abs": 1e-12, "rel": 1e-12}
}
```

要点：①终水六指标键名=BOD5/CODCR/SS/NH3N/TN/TP（与
`PlantResult.summary` 六指标族及 calcbook_plant 模板平键一致——
D10 起真值经 app 层 `_summary_of` 注入）；**矿井案例为五指标面**
（SS/CODCR/NH3N/TN/TP——BOD5 不建，Ruling BOD5-不建：矿井水
B/C=0.025 无生化性，BOD5 缺席合法）；②双容差 1e-12 不放宽
（Ruling A3）；③tolerance/design_dims 逐条带 source 必填；
④m3_deferred 两键为**真值数值形态**（GOLDEN2 2026-08-28 换真值
——结构 {value, source, abs, rel} 与 design_dims 条目同形态：
estimate_total=全图 design 档 takeoff→build_estimate grand_total
[测试直调 cost 三正门]；total_sludge=hebing ds_total 干基 kg/d
主口径+q_total 湿基双断言锚；矿井 v1 无此键——污泥链手算表未备，
升版归后续批）。
覆盖面最低要求：每个工艺单元 ≥2 条关键结果（design_dims 面）+
全厂汇总（effluent 指标面）× 全部工况。

### Step 5 —— notes.md、签字、锁定

`notes.md` 写：源文件路径、口径差异清单（含 0.57 类问题的处理）、
单位制注记；录入人签字（案例 README 签字栏）。然后**由人类**运行
（**显式携路径——禁无参全仓裸跑**，无参会重扫全仓挤入外挂目录，
两次事故在案）：

```bash
python scripts/lock_tests.py core/tests/golden   # 显式路径重锁（追加用例另附其 tests 路径）
```

端到端测试（`tests/golden/test_municipal_e2e.py` / `test_mine_water_e2e.py`）
将自动从 skip 转为激活，并在 M2/M3 实现后逐项对照。

## 验收口径（M2/M3 DoD）

- 全部 items 逐项通过（超容差 = 失败，不许放宽 tolerance 让它变绿——
  放宽容差 = 数据修正，须重新签字并解释）；
- 计算书/图纸导出物绑定三元组，任一数字可回溯条文与输入（审计演示）。
