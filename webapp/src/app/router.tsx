/**
 * 路由表：标签页式工作区（画布/方案/三维/高程/概算/图纸）。
 *
 * 输入:  各 feature 切片的路由组件
 * 输出:  路由配置（AntD Tabs 标签页状态机——App.tsx activeKey 消费）
 *
 * 规格说明（FE6 批 6b 段四 D1 扩六值）：
 *   - 路由名与次序=冻结面六值 canvas/solutions/viewer3d/elevation/cost/
 *     drawings（solutions 插 canvas 后第二位=用户流程：设计→看方案；
 *     简报 D1 显式枚举序为准——elevation 后 cost/drawings 次序与 FE3
 *     五值面 drawings/cost 互换，以简报字面为准记档）；
 *   - 三维视图独立路由 + 懒加载 chunk（§12.6，vite manualChunks 已配）；
 *   - 画布是默认标签且常驻（切换不卸载，防画布状态丢失）；
 *   - 路由状态进 view 态持久化（§12.3：不参与 content-hash）；
 *   - 本文件只做路由组合，禁止业务逻辑。
 */
export type AppRoute =
  | "canvas"
  | "solutions"
  | "viewer3d"
  | "elevation"
  | "cost"
  | "drawings";

export const ROUTES: readonly AppRoute[] = [
  "canvas",
  "solutions",
  "viewer3d",
  "elevation",
  "cost",
  "drawings",
] as const;
