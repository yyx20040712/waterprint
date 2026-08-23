# coefficients —— 去除率/经验系数库

`registry/coefficients.py` 消费；随规范版本演进（数据驱动，非代码分支）。

## 文件规划（M0/M1 起创建）

> 状态注：removal_rates.yaml 与 factors.yaml 已于 0.1.0 生效
> （2026-08-23 签字；其余三个规划文件随里程碑创建）。

```
coefficients/
├─ manifest.yaml            # data_version + 变更记录
├─ removal_rates.yaml       # 各单元六指标去除率（manifest.removal_refs 引用键）
├─ factors.yaml             # 经验系数（曝气修正/污泥产率/α β 系数…）
├─ pipe_roughness.yaml      # 管网粗糙系数（按管材）
├─ indicator_bands.yaml     # 单位造价指标带（cost/indicators 消费）
└─ assumptions_source.yaml  # 设计假设默认值来源附件（registry/assumptions 的数据备份）
```

## 条目 schema（每条必须齐全）

```yaml
- key: "removal.aao.bod5.high_load"
  value: 0.0            # 示例形态，非真实数据；真实值经条文/手册核定录入
  unit: "dimensionless"  # 规范单位（dimensionless/percent-decimal…）
  source: "GB 50014-2021 表 x.x.x"   # 必填
  note: "适用条件说明（负荷区间/水温…）"
```

## 硬规则

- 去除率键与单元 manifest.removal_refs 闭环校验（失联=启动失败）；
- 适用条件写 note（不做代码分支——多档取值 = 多个键，单元按工况
  映射选键，ADR-007 精神）；
- 出水标准（一级A/III类限值）也在此包（contracts/quality.py R1
  "标准是数据"）。
