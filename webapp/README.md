# webapp —— React 前端

React 18 + TypeScript(strict) + Vite；feature 切片结构（§13.5）。

> 当前状态：**M0.5 结构接线完成**——43 源文件=入口 1+app 4+features 32+
> shared 6，全部带 TS 契约头（`main.tsx`/`App.tsx` 可编译骨架屏 +
> feature/shared 规格骨架，由 `scripts/check_webapp.py` 门禁校验）；
> feature 实装按 M2+ 推进。

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
