# webapp —— React 前端

React 19 + TypeScript(strict) + Vite 7；feature 切片结构（§13.5）。

> 版本面（FE2 升版批 2026-08-28）：react 19.2 + @react-three/fiber 9.7
> + antd 6.6 + echarts 6.1 + vite 7.3 + vitest 4.1 + @types/three 0.185。
> 未升面记档：typescript 7（tsconfig `baseUrl` 破坏面+白名单禁触）、
> vite 8 / @vitejs/plugin-react 6（rolldown 内核 `manualChunks` 对象
> 形态破坏+vite.config 冻结）、orval 8（钉版 7.21——生成物稳定优先）。

> 当前状态：**M0.5 结构接线完成；viewer3d 已挂载应用壳（FE3 2026-08-29）；
> canvas 只读渲染已挂载默认标签（FE4 批 6b 段一 2026-08-29：design 工艺图
> 经 projectFlow 投影→React Flow 只读画布，URL `?project=` 单一真相）；
> params 参数面板已挂载 canvas 侧栏（FE5 批 6b 段三 2026-08-29：ParamForm
> 选中单元参数编辑（META1 目录+design 覆盖→草稿→apply 提交重算+read 键
> invalidate）+AssumptionsPanel 假设只读清单+画布节点点击选中态）；
> solutions 方案浏览已挂载第二标签（FE6 批 6b 段四 2026-08-29：单单元枚举
> 提交→EventSource SSE 任务进度（TaskPanel 徽标/进度/failed 回显/取消）
> →服务端分页方案表（动态列+margin_min 语义色）→行级应用（grid_fields
> 投影 params→read 键 invalidate）+无解诊断面板；URL `?task=` 与
> `?project=` 双参联动（params 表单 apply 亦回写——FE5 挂账③收口））；
> elevation 高程纵断已挂载第四标签（FE7 批 6b 段五 2026-08-29：echarts
> 首消费——lazy ProfileChart 独立异步 chunk 按需注册五件；GET
> /api/elevation latest done calc 按需投影（±0.00 相对标高+crest 服务端
> 投影+空段损失恒 0 注记）+ConditionSwitcher 工况按需切换+PumpStationsPanel
> 提升点位/跌水警告；"wp:task" 事件桥 invalidate 前缀键——apply 重算后
> 面板刷新）；cost 概算已挂载第六标签（FE8 批 6b 段六 2026-08-29：GET
> /api/cost latest done calc 四模块装配（load_prices→load_fee_rules→
> takeoff→build_estimate→check_indicators——服务端单点，前端零算价）；
> EstimateTable 分级汇总（明细可折叠溯源=定额键+source_field_ids+单价+
> 三元组串——M4 任一数字可回溯落点）+IndicatorsCard 指标对照（OK 绿/
> WARN 橙/未校核灰）+工况 Select 缺省 design 回显；非 lazy 无大件；
> "wp:task" 事件桥第四处内联 invalidate 前缀键）**
> ——77 源文件=入口 1+app 13+features 56+shared 7，全部带 TS 契约头
> （`App.tsx` Tabs 六标签路由状态机+Providers 实装+viewer3d 懒加载标签，
> 由 `scripts/check_webapp.py` 门禁校验——77 计数机器一致）；唯 drawings
> 一标签维持占位屏，其余 feature 实装按 M2+ 推进。

## 结构

```
src/
├─ app/          路由与 Provider 组合（唯一允许组合 features 的层）
├─ features/     canvas/params/solutions/elevation/cost/viewer3d/drawings
│                （features 互相禁止 import —— 见各 README）
└─ shared/       api（orval 生成，禁手改）/ store / ui
```

## 命令（环境就绪后，见根 README 环境待办）

```bash
pnpm install          # 需 corepack enable 启用 pnpm
pnpm dev              # vite dev server（代理 /api → 127.0.0.1:8000）
pnpm build            # tsc --noEmit + vite build
pnpm test             # vitest
pnpm orval            # 由 api-contracts/openapi.json 重新生成客户端
```

> 本地链=orval→dev/build/test：`generated/` 不入库（根 .gitignore 排除），
> clone 后先 `pnpm orval` 再 dev/build（CI webapp job 已在 build 前常驻跑
> `pnpm orval`——契约重生成与消费同源，FE1 D3 口径）。

## 硬规则（CI/评审强制）

- 单文件 ≤500 行；features 互相禁止 import（`scripts/check_webapp.py` 机器强制）；
- 每个源文件首块 `/** … */` 契约头含 职责/输入/输出（同门禁强制）；
- 服务端类型只从 orval 生成（禁手写双份）；
- 前端零业务计算/零业务几何推导（TS 侧复制业务逻辑 = 评审拒绝）。
