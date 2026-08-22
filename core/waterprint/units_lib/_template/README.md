# <单元名>（<业务线>）

> 一段话职责：本单元做什么、依据什么规范。

## 输入

- 上游端口量：水（WaterFlow + WaterQuality）/ 泥（SludgeFlow）
- 参数：见 manifest.py 声明（字段 ID、范围、出处）

## 输出

- 下游端口量与结果维度字段（字段 ID 见 dimensions 注册表）
- 约束：constraints.py 声明

## 交付四件套（M2 起 DoD）

1. 计算（compute.py 向量化唯一实现）
2. 测试（tests/test_compute.py golden 数值 + tests/properties.py 物理不变性）
3. 三维组件（geometry 投影消费本单元字段，前端类型化渲染）
4. 图纸模板（drafting 平面/剖面，manifest 驱动）

## 规范依据

- 条文列表（GB 50014-2021 §x.x.x 等，逐条与 docs/norms 手算对照表链接）
- 领域专家复核签字：＿＿＿（日期：＿＿＿）
