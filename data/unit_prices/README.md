# unit_prices —— 定额单价库

迁移来源：旧系统 `src/models/cost/unit_prices.py`（2019 黑龙江计价定额）。
迁移时**人工抽验 10%**（§5 迁移清单），抽验记录进本目录 manifest.yaml。

## 文件规划（迁移期创建）

```
unit_prices/
├─ manifest.yaml        # data_version + 变更记录 + 抽验记录
├─ buildings.yaml       # 建筑工程（混凝土/钢筋/土方…按定额章节分文件）
├─ installations.yaml   # 安装工程（工艺管道/设备安装…）
├─ auxiliary.yaml       # 措施费率/间接费率/税率/预备费率（FeeRule 数据）
└─ field_mapping.yaml   # 结果字段 ID → 定额项键 映射（takeoff 消费）
```

## 条目 schema（每条必须齐全）

```yaml
- key: "KL9-1"            # 定额子目号（price_key，全库唯一）
  name: "某定额子目名称"
  unit: "m3"              # 计价单位（与工程量单位一致，不一致加载失败）
  price: 0.0              # 示例形态，非真实数据；真实值迁移时录入
  source: "HLJ-2019 建筑工程计价定额 第9章"   # 必填
  note: "可选说明"
```

设备族条目（installations.yaml 的 EQUIPMENT 迁移条目）在六列之外扩展可选第 7 列
`quantity`（台数）；COMMON_EQUIP 合计项旧源无台数，不带此列。

## 硬规则

- `key` 与 takeoff 的 price_key 引用闭环：失联键 = 启动失败
  （core cost/prices.py R3）；
- 费率条目（费率类）带 `base` 取费基数表达式（受限 DSL，
  与 solution/constraints 同风格）；
- 版本升级（定额换版）→ 新 data_version → 全部概算结果过期。

## 金额倍率契约（批6d 2026-09-26——price_data_version 1.1.0 起）

- manifest.yaml `unit_scales` 节=单位→折元倍率全契约：**全条目单位须全覆盖，
  缺列=装载拒绝**（prices 硬契约）；万元族（万元/台、万元）=10000，元族与
  裸量纲族=1。条目面值保持 RATIFY3 批准口径零变更——消费侧 estimate
  明细 amount=量×面值×scale 折元（b6d-design §二案甲）。
- installations.yaml 增 `aao.microporous_aerator_piping`（22.0 万元/台，
  台=按组/每系列一套——cass 组 quantity=池数同款口径；同物同价沿用 2024
  市场询价；§14 事后追认）。
