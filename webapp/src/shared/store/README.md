# shared/store —— zustand slices

每 feature 一个 slice 文件（features/*/store/*.ts），本目录只放
跨 feature 的公共 store 工具（持久化中间件封装、devtools 约定）。

## 文件清单（M0.5 结构接线已创建规格骨架；实装期填充实现）

| 文件 | 职责 |
|------|------|
| `persist.ts` | localStorage 持久化封装（view 态持久化——design 态永不经前端存储） |
| `devtools.ts` | 开发期 devtools 约定 |

## 规则

- UI 态走 zustand；服务态走 TanStack Query（§2 选型）；
  界限：**一切来自服务端的数据不进 zustand**（queryKey 含三元组
  自动失效，§17.2）；
- 画布/3D 状态全经 store 持有，不依赖组件重挂载（§11 R14）。
