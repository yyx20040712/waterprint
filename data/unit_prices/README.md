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
  缺列=装载拒绝**（prices 硬契约）；万元族（万元/台、万元/套、万元）=10000
  （万元/套=批6o 词表新增，与台同倍率——词面变更值零变），元族与
  裸量纲族=1。条目面值保持 RATIFY3 批准口径零变更——消费侧 estimate
  明细 amount=量×面值×scale 折元（b6d-design §二案甲）。
- installations.yaml 增 `aao.microporous_aerator_piping`（22.0 万元/台，
  台=按组/每系列一套——cass 组 quantity=池数同款口径；同物同价沿用 2024
  市场询价；§14 事后追认）。
  〔批6o 词表标准化 2026-09-29：本条已改「万元/套」——见下节词表面。〕

## 单位词表面（批6o 2026-09-29——price_data_version 1.2.0 起）

用户裁决 2026-09-28（增补五十六 H 立项+增补六十二③ 裁量规则）：不搞全量
统一、具体问题具体分析——**单体设备类用「台」、散件布设类（管路/分布式
系统）用「套」**，逐条按此裁量。

| 单位 | 语义 | 覆盖条目 |
|---|---|---|
| 万元/台 | 单体设备类：整机出厂、铭牌计数、台数语义自明 | EQUIPMENT 30 条（泵/风机/搅拌器/格栅/刮泥机/滗水器/沉砂器/分离器/仪表/柜体/堰/模块/回收装置等） |
| 万元/套 | 散件布设类：管路/分布式组件/成套系统/批量散件（按系统或批次成套计价） | EQUIPMENT 12 条（微孔曝气器+管路×2/鼓风机房/排泥阀及管路/斜管填料/PAC·PAM 加药系统×4/长柄滤头+滤板/配水配气系统/气动阀门 1 批） |
| 万元 | 整包合计项（COMMON_EQUIP——整包采购计价非设备计数） | common.* 8 条 |
| m | 管道延米计量 | pipe.dn300~dn1500 12 档 |
| m3/m2/m/t/kg | 建筑工程量纲（元族面值） | buildings 11 条 |
| dimensionless/元/(m3.d) | 费率与造价指标 | auxiliary 9 条 |

- 台/套逐条裁定全表+边界裁量记档（鼓风机房→套/紫外模块→台/气动阀门批→套/
  磁种回收装置→台）单源=.workflow/backend-calc-complete/b6o-wording-audit.md
  §二（会话卷宗）；仓内冻结面=core/tests/cost/test_prices.py
  `_EQUIP_UNIT_BY_KEY` 42 键冻结表（改任一条单位/增删设备条目即测试红——
  词表变更=显式数据批事件）。**本表计数（30/12/42）与逐条裁定以镜像测试
  冻结表为准——条目增删须随批同步冻结表与本表（计数锚=test_unit_
  vocabulary_freeze 断言 12/42）。**
- 值零变语义：万元/套 与 万元/台 同倍率 1e4（manifest unit_scales）——词面
  变更非数值变更，estimate 金额链零变（独立复算随批6o 卷宗）。
- RATIFY3 批准面重签记录=manifest.yaml 抽验记录槽位末行（预授权②事后
  追认制呈终裁）。
