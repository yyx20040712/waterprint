# shared/store —— zustand slices

每 feature 一个 slice 文件（features/*/store/*.ts）。本目录当前无共享件
（M0.5 期 `persist.ts`/`devtools.ts` 结构预留骨架已于复杂度治理清理批
2026-09-18 删除——预留功能从未实装且零引用）；未来跨 feature 的 store
公共工具按「同层晋升准入五条」晋升至此（复杂度治理方案二）。

## 规则

- UI 态走 zustand；服务态走 TanStack Query（§2 选型）；
  界限：**一切来自服务端的数据不进 zustand**（queryKey 含三元组
  自动失效，§17.2）；
- 画布/3D 状态全经 store 持有，不依赖组件重挂载（§11 R14）。
