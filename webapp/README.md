# webapp —— React 前端

React 19 + TypeScript(strict) + Vite 7；feature 切片结构（§13.5）。

> 版本面（FE2 升版批 2026-08-28）：react 19.2 + @react-three/fiber 9.7
> + antd 6.6 + echarts 6.1 + vite 7.3 + vitest 4.1 + @types/three 0.185。
> 未升面记档：typescript 7（tsconfig `baseUrl` 破坏面+白名单禁触）、
> vite 8 / @vitejs/plugin-react 6（rolldown 内核 `manualChunks` 对象
> 形态破坏+vite.config 冻结）、orval 8（钉版 7.21——生成物稳定优先）。

> 当前状态：**M0.5 结构接线完成；viewer3d 已挂载应用壳（FE3 2026-08-29）；
> canvas 只读渲染已挂载默认标签（FE4 批 6b 段一 2026-08-29：design 工艺图
> 经 projectFlow 投影→React Flow 只读画布，URL `?project=` 单一真相）**
> ——57 源文件=入口 1+app 10+features 39+shared 7，全部带 TS 契约头
> （`App.tsx` Tabs 路由状态机+Providers 实装+viewer3d 懒加载标签，
> 由 `scripts/check_webapp.py` 门禁校验）；其余 feature 实装按 M2+ 推进。

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
