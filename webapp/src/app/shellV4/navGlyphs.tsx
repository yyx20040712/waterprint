/**
 * 导航单线图标（美感抛光批 #13——图标统一：viewer3d 结构栏 ◻/≋/▦/▭
 * 与 deliverables 左树 ▦/▥/▤/▧ 文本字形退役，统一为 16px 视框 1.6px
 * monoline currentColor SVG——复用 viewer3dZone ToolIcon/图纸卡 SheetGlyph
 * 的描边语言，不新增另一套图标库；固定视框+光学居中消除跨平台字重与
 * 基线漂移）。
 *
 * 输入:  kind（unit/wave/grid/rect/site/profile/flow/doc 八形——消费面
 *        viewer3dZone 结构栏与 deliverablesZone 左树）
 * 输出:  16×16 单线 SVG（stroke=currentColor、strokeWidth 1.6、fill=none
 *        ——尺寸由消费面 width/height 或默认 14px 承载）
 */
export type NavGlyphKind =
  | "unit"
  | "wave"
  | "grid"
  | "rect"
  | "site"
  | "profile"
  | "flow"
  | "doc";

/** 各形路径段（M/折线/wave 三正弦近似——每形 1–3 段，克制不摹画）。 */
const GLYPH_PATHS: Record<NavGlyphKind, readonly string[]> = {
  // 单元（◻——场景/结构里的单元小方）
  unit: ["M4.5 4.5h7v7h-7z"],
  // 管廊（≋——三条波浪线）
  wave: [
    "M2.5 5.5c1.2-1.4 2.6-1.4 3.8 0s2.6 1.4 3.8 0 2.6-1.4 3.4 0",
    "M2.5 10.5c1.2-1.4 2.6-1.4 3.8 0s2.6 1.4 3.8 0 2.6-1.4 3.4 0",
  ],
  // 道路与走廊（▦——2×2 田字）
  grid: ["M3.5 3.5h9v9h-9z", "M8 3.5v9", "M3.5 8h9"],
  // 场地红线（▭——宽扁矩形）
  rect: ["M2.5 6h11v4h-11z"],
  // 全厂总平面图（▦→分区平面：外框+两横一竖内墙）
  site: ["M3 3.5h10v9H3z", "M3 9.5h10", "M8.5 3.5v6"],
  // 高程纵断图（▥→地层剖面：底线+两级台阶线）
  profile: [
    "M2.5 12.5h11",
    "M2.5 12.5V8h4V5.5h7",
  ],
  // 工艺图（▤→流程：两框一连线）
  flow: ["M2.5 4.5h4v4h-4z", "M9.5 7.5h4v4h-4z", "M6.5 6.5h3"],
  // 计算说明书（▧→文档：页形+两行文）
  doc: ["M4 2.5h8v11H4z", "M6 6h4", "M6 9h4"],
};

export function NavGlyph({
  kind,
  size = 14,
}: {
  kind: NavGlyphKind;
  /** 像素边长（默认 14——树行/徽标列 13–14px 槽位）。 */
  size?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {GLYPH_PATHS[kind].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
