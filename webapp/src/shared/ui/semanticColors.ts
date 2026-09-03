/**
 * 语义色真源表：token→色值唯一映射（SC1 真源化——全 webapp 渲染/2D
 * 描绘统一消费；features 互不 import 的字面平行拷贝全数收编于此）。
 *
 * 输入:  语义 token 字符串（渲染描述/组件携带的 semantic 键）
 * 输出:  SEMANTIC_COLORS（24 键字面表）+ FALLBACK_COLOR（未登记兜底
 *        灰阶）+ semanticColor()（查表函数——未登记语义回退兜底，
 *        禁抛错打断渲染）
 *
 * 迁移口径（SC1 D1/D2）：3D 图元色族 12 键自 PoolBox 本地表迁移、
 * 2D 场面色族 7 键自 SiteRoutes/SiteBoundary/SiteCanvas 平行拷贝收编、
 * 2D 单点彩色语义族 5 键自 SiteCanvas 收编——全部原值迁移零色值变更
 * （像素零漂移）。灰阶族（结构/网格/UI 边框灰）与图表色族
 * （profileChart）不收编（非本批漂移面）。键集冻结锚=
 * semanticColors.test.ts（增删键/改值必须同步字面清单）。
 */
/** 语义色表（token→色值唯一映射处——全 webapp 渲染/2D 描绘统一消费）。 */
export const SEMANTIC_COLORS = {
  // 3D 图元色族（自 PoolBox 迁移，12 键）
  pool_wall: "#8d99a6",
  partition: "#7a8694",
  channel: "#7f8a93",
  ground: "#cfd6dc",
  water_surface: "#2f7fd1", // 蓝水线
  sludge: "#8c5a2b", // 棕泥线
  aerator: "#d48806",
  paddle: "#d48806",
  media: "#6a7f5a",
  gate: "#5b8db8",
  pipe: "#5b8db8",
  decant: "#5b8db8",
  // 2D 场面色族（自 SiteRoutes/SiteBoundary/SiteCanvas 平行拷贝收编，7 键）
  road: "#6b6f76",
  boundary: "#d4380d",
  corridor_water: "#2f7fd1",
  corridor_power: "#f2a93b",
  corridor_gas: "#3fa34d",
  corridor_comm: "#9a6dd7",
  corridor_fallback: "#8c8c8c",
  // 2D 单点彩色语义族（自 SiteCanvas 收编，5 键）
  selected: "#1668dc",
  pending: "#d48806",
  measure: "#2f7fd1",
  spacing_warn: "#faad14", // L4b 校核 WARN 黄
  spacing_error: "#ff4d4f", // L4b 校核 ERROR 红（三色并存：pending=未计算）
} as const;

/** 未登记语义兜底灰阶（禁抛错打断渲染）。 */
export const FALLBACK_COLOR = "#9aa5b1";

/** 语义 token → 色值（未登记语义=灰阶兜底——禁抛错打断渲染）。 */
export const semanticColor = (semantic: string): string =>
  SEMANTIC_COLORS[semantic as keyof typeof SEMANTIC_COLORS] ?? FALLBACK_COLOR;
