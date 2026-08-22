# Golden Cases（端到端验收用例）—— 录入指引

两个真实设计案例，数据落位 `core/tests/golden/golden_data/`（只读，与测试同锁）。
**期望值唯一合法来源 = docs/norms 手算对照表 + 旧系统结果（差异逐条解释）**；
实现者不得自编数字（§16 A9）。

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

按 `docs/norms.md` 流程摘录条文并手算，**每案例至少覆盖**：
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

每条期望值一条记录（`tolerance` 单位随字段；`source` 必填）：

```json
{
  "items": [
    {"condition_key": "design", "scope": "municipal_aao",
     "field_id": "有效容积字段ID", "expected": 0.0,
     "tolerance": 0.0, "source": "GB 50014-2021 §x.x.x 手算 / 旧系统+差异注记"}
  ],
  "notes": "见 notes.md"
}
```

覆盖面最低要求：每个工艺单元 ≥2 条关键结果 + 全厂汇总（出水浓度、
达标裕度、总泥量）× 基线两档工况 + 每个受检单元的检修工况 1 条。

### Step 5 —— notes.md、签字、锁定

`notes.md` 写：源文件路径、口径差异清单（含 0.57 类问题的处理）、
单位制注记；录入人签字（案例 README 签字栏）。然后**由人类**运行：

```bash
python scripts/lock_tests.py        # 刷新锁定清单（新数据文件纳入哈希保护）
```

端到端测试（`tests/golden/test_municipal_e2e.py` / `test_mine_water_e2e.py`）
将自动从 skip 转为激活，并在 M2/M3 实现后逐项对照。

## 验收口径（M2/M3 DoD）

- 全部 items 逐项通过（超容差 = 失败，不许放宽 tolerance 让它变绿——
  放宽容差 = 数据修正，须重新签字并解释）；
- 计算书/图纸导出物绑定三元组，任一数字可回溯条文与输入（审计演示）。
