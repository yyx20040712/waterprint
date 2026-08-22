# core/tests —— 测试系统（单一事实源）

> 本目录全部文件**只读**（`test-lock.manifest.json` 哈希 + 只读属性，
> 见 AGENTS.md §7）。修改/新增测试 = 人类执行的显式解锁流程。
> 文档导航页：`docs/testing.md`（摘要，以本文件为准）。

## 结构与分层

```
tests/
├─ conftest.py        薄装配（fixtures/路径/hypothesis——禁业务断言与全局 skip）
├─ arch/              架构门禁测试（骨架期即激活，永续运行）
│   ├─ test_structure.py      镜像规则 + 职责表同步 + 单元包固定结构
│   ├─ test_file_budgets.py   行数 ≤500 / compute ≤400
│   ├─ test_hygiene.py        占位符/裸 except/乱码/UTF-8 = 0
│   └─ test_lock.py           测试只读校验（manifest + 属性）
├─ contracts|registry|graph|solution|elevation|cost|drafting|geometry|
│  network|project|trace|app/     镜像测试（test_<模块名>.py）
├─ properties_*       性质测试（hypothesis：非负/单调/守恒/边界/字节级等价）
├─ golden/            端到端（两大案例）+ golden_data/（期望值数据，人类维护）
├─ snapshots/         syrupy 输出快照（Excel/DXF/审计报告内容哈希）
└─ benchmark/         pytest-benchmark 性能基准（§18.1 预算）
```

## 休眠机制（骨架期 → 实现期）

每个镜像测试文件用 getattr 守卫：目标符号缺失 → skip 并注明缺什么。
**实现合入后 skip 必须归零**（CI 以 `-ra` 输出 skip 原因；里程碑 DoD
含 "skip 数 = 本里程碑范围"）。守卫写在只读文件内，AI 无法篡改。

## 硬规则

1. 镜像命名：`topo.py` ↔ `test_topo.py`（arch/test_structure 强制）；
   units_lib 单元包例外（固定结构 §13.6：test_compute.py + properties.py）。
2. 红绿纪律：每个测试先失败一次再通过（AGENTS §6）。
3. 期望值来源：docs/norms 手算对照表 + golden_data 数据文件；
   实现者自编数字 = 无效测试。
4. 常驻不变量：双跑 diff=0、序列化往返无损、incremental==全量（字节级）、
   DS 守恒、混合 min/max 夹逼。
5. 性能基准门禁值见计划 §18.1；劣化即失败。
