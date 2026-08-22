/**
 * 路由表：标签页式工作区（画布/三维/高程/图纸/概算）。
 *
 * 输入:  各 feature 切片的路由组件
 * 输出:  路由配置（React Router 或标签页状态机，M2 定型）
 *
 * 规格说明（骨架冻结）：
 *   - 三维视图独立路由 + 懒加载 chunk（§12.6，vite manualChunks 已配）；
 *   - 画布是默认标签且常驻（切换不卸载，防画布状态丢失）；
 *   - 路由状态进 view 态持久化（§12.3：不参与 content-hash）；
 *   - 本文件只做路由组合，禁止业务逻辑。
 */
export type AppRoute =
  | "canvas"
  | "viewer3d"
  | "elevation"
  | "drawings"
  | "cost";

export const ROUTES: readonly AppRoute[] = [
  "canvas",
  "viewer3d",
  "elevation",
  "drawings",
  "cost",
] as const;
