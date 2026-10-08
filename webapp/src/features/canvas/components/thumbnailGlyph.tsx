/**
 * 缩略图字形件（B1 骨架批 2026-10-09——v4 工艺画布节点缩略形态：36 类
 * 预绘简笔 SVG（32 包 unit_id+4 builtin kind），线性 stroke=currentColor、
 * viewBox 64×40——wireframe-d-v4 屏 1 缩略图节点形）。
 *
 * 输入:  kind（unit_id 或 builtin kind——画布查表口径 kind ?? unitId 同 M1）
 * 输出:  ThumbnailGlyph（简笔 SVG——未知 kind 回退象形框）；THUMBNAIL_
 *        GLYPH_KINDS（36 键集——app 层 catalogCategories.test 目录全量×
 *        键集对账消费）；hasThumbnailGlyph（判别）
 *
 * 规格说明（B1 任务书 §二.③ 白名单件+§三.3 缩略图节点形态）：
 *   - 一件一形：同类族共享结构母题（格栅/圆形池/矩形池/渠道），族内
 *     以杆距/内件/流向箭头分异（目视可辨——非装饰性图形）；
 *   - 全部 stroke=currentColor（消费面着色=选中蓝/常态 FG-1）；fill=none
 *     线性简笔（全局规则：简笔线性图标）；
 *   - 键集=映射表全域恰等（DoD §四.5 对账单源在 app 层测试——分层红线
 *     features 禁 import app，本件不持有映射表）；
 *   - 纯渲染零数据依赖（name_zh 图题在消费面——本件只画形）。
 */
import type { ReactElement, ReactNode } from "react";

/** 字形 viewBox（消费面 svg width/height 按此纵横比 8:5）。 */
const GLYPH_VIEWBOX = "0 0 64 40";

/** 36 kind 键集（32 包 unit_id+4 builtin kind——映射表全域恰等）。 */
export const THUMBNAIL_GLYPH_KINDS: readonly string[] = [
  // 一级处理
  "municipal_cugeshan",
  "municipal_xigeshan",
  "municipal_chenshachi",
  "municipal_chuchenchi",
  "municipal_tiaojiechi",
  "municipal_wushui_tisheng",
  "municipal_bashi_jiliangcao",
  "conveyance_jishuijing",
  "conveyance_peishuijing",
  "conveyance_jipeishuijing",
  "conveyance_peishuiqu",
  // 二级处理
  "municipal_aao",
  "municipal_cass",
  "municipal_erchunchi",
  // 深度处理
  "municipal_gaomidu",
  "municipal_vxinglvchi",
  "municipal_ziwai",
  // 矿井水处理
  "mine_water_input",
  "mine_water_tiaojiechi",
  "mine_water_chenshachi",
  "mine_water_ningjiao",
  "mine_water_cifenli",
  "mine_water_gaomidu",
  "mine_water_vxinglvchi",
  "mine_water_ziwai",
  // 污泥处理
  "sludge_bengzhan",
  "sludge_nongsuo",
  "sludge_hebing",
  "sludge_xiaohua",
  "sludge_tuoshui",
  "sludge_ganhua",
  "sludge_shusong",
  // 结构节点（builtin）
  "municipal_input",
  "junction",
  "quality_edit",
  "recycle_junction",
];

/** kind 判别（键集成员）。 */
export function hasThumbnailGlyph(kind: string): boolean {
  return (THUMBNAIL_GLYPH_KINDS as readonly string[]).includes(kind);
}

/** 波浪线（水面母题——等宽步进 sin 形）。 */
const wave = (x: number, y: number, w: number): string => {
  const s = w / 4;
  return `M${x} ${y}c${s * 0.5} -4 ${s * 1.5} 4 ${s * 2} 0s${s * 1.5} 4 ${s * 2} 0`;
};

/** 36 形映射（kind→简笔内件组——svg 根由组件统一供给）。 */
const GLYPHS: Readonly<Record<string, ReactNode>> = {
  // ── 格栅族：渠道框+垂直栅杆（粗疏/细密分异） ──
  municipal_cugeshan: (
    <>
      <rect x="6" y="6" width="48" height="28" rx="2" />
      <path d="M18 8v24M28 8v24M38 8v24M48 8v24" />
    </>
  ),
  municipal_xigeshan: (
    <>
      <rect x="6" y="6" width="48" height="28" rx="2" />
      <path d="M13 8v24M18 8v24M23 8v24M28 8v24M33 8v24M38 8v24M43 8v24M48 8v24" />
    </>
  ),
  // ── 圆形池族：圆池+内件分异（旋流/辐流刮臂/浓缩泥层） ──
  municipal_chenshachi: (
    <>
      <circle cx="32" cy="20" r="13" />
      <path d="M24 20c4-5 13-4 15 2s-5 11-12 9-9-9-3-11" />
    </>
  ),
  municipal_chuchenchi: (
    <>
      <circle cx="32" cy="18" r="12" />
      <circle cx="32" cy="18" r="1.2" />
      <path d="M32 18l-9-6M32 18l9 6M25 29l7 6 7-6" />
    </>
  ),
  municipal_erchunchi: (
    <>
      <circle cx="32" cy="18" r="12" />
      <path d="M25 18a7 7 0 1 0 14 0a7 7 0 1 0-14 0" strokeDasharray="3 2" />
      <circle cx="32" cy="18" r="1.2" />
      <path d="M25 29l7 6 7-6" />
    </>
  ),
  sludge_nongsuo: (
    <>
      <circle cx="32" cy="18" r="12" />
      <path d="M22 23a12 12 0 0 0 20 0" strokeWidth="3" />
      <circle cx="32" cy="18" r="1.2" />
    </>
  ),
  // ── 矩形池族：池体+内件分异（水面/曝气虚线/斜板/V 滤/消毒灯） ──
  municipal_tiaojiechi: (
    <>
      <rect x="6" y="8" width="46" height="24" rx="2" />
      <path d={wave(12, 22, 34)} />
    </>
  ),
  municipal_aao: (
    <>
      <rect x="6" y="8" width="52" height="24" rx="2" />
      <path d="M24 8v24M42 8v24" strokeDasharray="4 3" />
      <path d="M8 15h48M8 26h48" strokeDasharray="3 2" />
    </>
  ),
  municipal_cass: (
    <>
      <rect x="6" y="8" width="46" height="24" rx="2" />
      <path d="M40 8v24" strokeDasharray="4 3" />
      <circle cx="49" cy="14" r="3" />
      <path d={wave(10, 24, 24)} />
    </>
  ),
  municipal_gaomidu: (
    <>
      <rect x="6" y="6" width="46" height="28" rx="2" />
      <path d="M14 30l7-14M23 30l7-14M32 30l7-14M41 30l7-14" />
    </>
  ),
  mine_water_gaomidu: (
    <>
      <rect x="10" y="6" width="44" height="24" rx="2" />
      <path d="M20 14l7 14M29 14l7 14M38 14l7 14" />
      <path d="M32 30v6M29 33l3 3 3-3" />
    </>
  ),
  municipal_vxinglvchi: (
    <>
      <rect x="6" y="6" width="46" height="28" rx="2" />
      <path d="M14 28l6-11 6 11M28 28l6-11 6 11" />
    </>
  ),
  mine_water_vxinglvchi: (
    <>
      <rect x="8" y="10" width="44" height="20" rx="2" />
      <path d="M18 26l5-9 5 9M33 26l5-9 5 9" />
      <circle cx="20" cy="32" r="1" />
      <circle cx="32" cy="32" r="1" />
      <circle cx="44" cy="32" r="1" />
    </>
  ),
  municipal_ziwai: (
    <>
      <rect x="6" y="14" width="48" height="12" rx="2" />
      <path d="M18 8v10M32 8v10M46 8v10" />
      <circle cx="18" cy="8" r="1.6" />
      <circle cx="32" cy="8" r="1.6" />
      <circle cx="46" cy="8" r="1.6" />
    </>
  ),
  mine_water_ziwai: (
    <>
      <rect x="10" y="14" width="48" height="12" rx="2" />
      <path d="M22 8v10M36 8v10M50 8v10" />
      <circle cx="22" cy="8" r="1.6" />
      <circle cx="36" cy="8" r="1.6" />
      <circle cx="50" cy="8" r="1.6" />
      <path d="M10 18L16 12" />
    </>
  ),
  mine_water_tiaojiechi: (
    <>
      <rect x="12" y="10" width="44" height="22" rx="2" />
      <path d={wave(17, 24, 30)} />
      <path d="M12 14l6-6" />
    </>
  ),
  mine_water_chenshachi: (
    <>
      <rect x="6" y="12" width="52" height="16" rx="2" />
      <path d="M12 20h12M20 17l5 3-5 3M36 20h12M44 17l5 3-5 3" />
    </>
  ),
  // ── 泵/计量/井渠族 ──
  municipal_wushui_tisheng: (
    <>
      <rect x="14" y="6" width="36" height="28" rx="2" />
      <circle cx="32" cy="20" r="6" />
      <path d="M30 17l5 3-5 3z" />
    </>
  ),
  municipal_bashi_jiliangcao: (
    <>
      <path d="M6 10h16l9 10-9 10H6" />
      <path d="M58 10H42l-9 10 9 10h16" />
    </>
  ),
  conveyance_jishuijing: (
    <>
      <circle cx="34" cy="20" r="10" />
      <path d={wave(28, 20, 12)} />
      <path d="M6 20h14M17 17l4 3-4 3" />
    </>
  ),
  conveyance_peishuijing: (
    <>
      <circle cx="26" cy="20" r="10" />
      <circle cx="26" cy="20" r="1.2" />
      <path d="M33 13l8-6M35 20h10M33 27l8 6" />
    </>
  ),
  conveyance_jipeishuijing: (
    <>
      <circle cx="32" cy="20" r="10" />
      <circle cx="32" cy="20" r="1.2" />
      <path d="M6 20h12M14 17l4 3-4 3M40 14l6-4M40 26l6 4" />
    </>
  ),
  conveyance_peishuiqu: (
    <>
      <rect x="6" y="14" width="52" height="12" rx="2" />
      <path d="M20 14v12M34 14v12M48 14v12" />
    </>
  ),
  // ── 矿井水专有族 ──
  mine_water_input: (
    <>
      <path d="M32 4v12M27 11l5 6 5-6" />
      <path d="M12 32q20 7 40 0" />
    </>
  ),
  mine_water_ningjiao: (
    <>
      <circle cx="18" cy="22" r="4" />
      <circle cx="32" cy="16" r="5" />
      <circle cx="46" cy="22" r="4" />
      <path d="M22 21l5-3M37 19l5 2" />
    </>
  ),
  mine_water_cifenli: (
    <>
      <circle cx="32" cy="20" r="10" />
      <path d="M20 8v6h7M44 8v6h-7" />
      <circle cx="32" cy="20" r="1.2" />
    </>
  ),
  // ── 污泥处理族 ──
  sludge_bengzhan: (
    <>
      <circle cx="24" cy="20" r="7" />
      <path d="M22 17l5 3-5 3z" />
      <path d="M31 20h20M47 17l4 3-4 3" />
    </>
  ),
  sludge_hebing: (
    <>
      <path d="M6 12l14 8M6 28l14-8" />
      <circle cx="24" cy="20" r="4" />
      <path d="M28 20h14M38 17l4 3-4 3" />
    </>
  ),
  sludge_xiaohua: (
    <>
      <path d="M32 5c7 6 11 10 11 16a11 11 0 0 1-22 0c0-6 4-10 11-16z" />
      <path d={wave(27, 24, 10)} />
    </>
  ),
  sludge_tuoshui: (
    <>
      <rect x="12" y="10" width="14" height="20" rx="1" />
      <rect x="38" y="10" width="14" height="20" rx="1" />
      <path d="M30 32v4M34 30v5" />
    </>
  ),
  sludge_ganhua: (
    <>
      <rect x="10" y="18" width="44" height="14" rx="2" />
      <path d="M24 6l3 5M32 4v6M40 6l-3 5" />
      <path d={wave(15, 27, 30)} />
    </>
  ),
  sludge_shusong: (
    <>
      <rect x="6" y="14" width="52" height="12" rx="6" />
      <path d="M22 20l5-4v8zM32 20l5-4v8z" />
    </>
  ),
  // ── 结构节点族（builtin） ──
  municipal_input: (
    <>
      <path d="M6 20h18M20 17l4 3-4 3" />
      <circle cx="40" cy="20" r="6" />
    </>
  ),
  junction: (
    <>
      <path d="M6 12l14 8M6 28l14-8" />
      <circle cx="26" cy="20" r="4" />
      <path d="M30 20h14M40 17l4 3-4 3" />
    </>
  ),
  quality_edit: (
    <>
      <path d="M28 5h8M30 5v8l-8 14a4 4 0 0 0 4 6h12a4 4 0 0 0 4-6l-8-14V5" />
      <path d={wave(27, 28, 10)} />
    </>
  ),
  recycle_junction: (
    <>
      <path d="M40 20a8 8 0 1 1-8-8" />
      <path d="M28 8l-4 4 4 4" />
      <circle cx="24" cy="20" r="2.5" />
    </>
  ),
};

/** 未知 kind 回退象形（虚线方框+斜杠——诚实降级非装饰）。 */
const GLYPH_FALLBACK: ReactElement = (
  <>
    <rect x="10" y="8" width="44" height="24" rx="3" strokeDasharray="4 3" />
    <path d="M10 32L54 8" strokeDasharray="4 3" />
  </>
);

/** 缩略图字形（36 kind 预绘简笔 SVG——线性 currentColor）。 */
export function ThumbnailGlyph({
  kind,
  width = 64,
  height = 40,
}: {
  kind: string;
  width?: number;
  height?: number;
}): ReactElement {
  return (
    <svg
      width={width}
      height={height}
      viewBox={GLYPH_VIEWBOX}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.3}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      data-kind={kind}
    >
      {GLYPHS[kind] ?? GLYPH_FALLBACK}
    </svg>
  );
}
