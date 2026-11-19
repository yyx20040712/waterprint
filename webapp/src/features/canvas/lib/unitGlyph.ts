/**
 * 象形图标+域色纯函数：unit_id/kind → Unicode 工艺字形；business_line →
 * 节点/连线色（C2-canvas 画布标签重制——task-C2-canvas-plan.md §二 P3/P4；
 * b3 功能面重涂批 2026-11-19：域色/流色/图标三色组全数改 CSS 变量串输出
 * ——随 themeStore applyThemeMode→installDomainColorAxis 按模重注入的
 * --wp-water/sludge/mine/convey 轴取值，三主题即时换肤〔b1 遗留「JS 域色
 * 恒 light 档」收口——R-G3 人工联动面就此机轴化〕）。
 *
 * 输入:  unitId（design.nodes 键）+kind（内置四 kind 或 null）；
 *        business_line（/api/units UnitMetaEntry 字段——四值
 *        municipal/sludge/mine_water/conveyance，全库 32 单元前缀一致）
 * 输出:  象形字形串+域色/流色/图标三色组串（CSS 消费面——SVG stroke/
 *        fill 与 inline style 同串直用；域色=var(--wp-*) 变量串〔轴注入
 *        取值〕，中性灰=三模恒值字面〔semanticColors domain_neutral〕）
 *
 * 规格说明（C2-canvas 批；b3 域色三态收口）：
 *   - 字形=Unicode 几何稳定集（视觉稿态三全谱渲染实证——Windows/
 *     Chromium 零缺字；避 emoji 化字符如 ☀）；映射=工艺功能聚类
 *     （32 unit_id 精确键——unitGlyph.test.ts 全库枚举防漏键）；
 *     未收录键回退 ▢（自定义键不炸——显示层降级非错误）；
 *   - 域色四色制（b3 变量化）：已知业务线→var(--wp-water/sludge/mine/
 *     convey)〔消费面=画布节点/连线/图例/MiniMap——SVG 属性与 inline
 *     style 均可解析 CSS 变量，主题切换零重渲染换肤〕；改色单源=
 *     semanticColors DOMAIN_COLORS（三模记录）→installDomainColorAxis
 *     注入轴，本件零字面色；中性灰=NEUTRAL_DOMAIN（三模恒值 #595959
 *     ——字面安全）；未收录键回退中性（不误导域归属）；
 *   - 域色图标三色组（domainIconStyle——rgba 派生组随主题）：bg/border
 *     =color-mix 自轴域色派生（10%/38% 透明度），fg=轴域色直用——三模
 *     随轴自动派生，原 light 冻结字面组退役（消费面经 CSS 面取值）；
 *   - 流色两色制（P4）：任一端 sludge→泥（var(--wp-sludge)——污泥去向
 *     判定：剩余污泥/回流混合边归泥）；双端已知非 sludge→水
 *     （var(--wp-water)）；任一端未知（未收录）→中性灰；recycle 虚线
 *     由投影层叠加（本函数不管线型只管色）；
 *   - 零运行期库 import（projectFlow 同构——node 测试不拖 DOM 面；
 *     semanticColors 为零依赖纯常量表，import 不破此性质）。
 */
import { SEMANTIC_COLORS } from "../../../shared/ui/semanticColors";

/** 未收录键回退字形（占位方块——显示层降级）。 */
export const GLYPH_FALLBACK = "▢";

/** 工艺单元字形表（32 键=全库 unit_id——测试全枚举防漏；聚类见计划书）。 */
const UNIT_GLYPHS: Record<string, string> = {
  // 市政污水（13）
  municipal_cugeshan: "▤",
  municipal_xigeshan: "▤",
  municipal_wushui_tisheng: "▲",
  municipal_chenshachi: "◎",
  municipal_chuchenchi: "◎",
  municipal_erchunchi: "◎",
  municipal_gaomidu: "◎",
  municipal_aao: "◉",
  municipal_cass: "◉",
  municipal_vxinglvchi: "⋀",
  municipal_ziwai: "✦",
  municipal_tiaojiechi: "▬",
  municipal_bashi_jiliangcao: "▽",
  // 污泥处理（7）
  sludge_bengzhan: "▲",
  sludge_nongsuo: "◐",
  sludge_xiaohua: "⬡",
  sludge_tuoshui: "▦",
  sludge_ganhua: "▦",
  sludge_shusong: "▸",
  sludge_hebing: "⊕",
  // 矿井水（8）
  mine_water_input: "▽",
  mine_water_chenshachi: "◎",
  mine_water_gaomidu: "◎",
  mine_water_vxinglvchi: "⋀",
  mine_water_ziwai: "✦",
  mine_water_tiaojiechi: "▬",
  mine_water_cifenli: "⊛",
  mine_water_ningjiao: "✳",
  // 输配水（4）
  conveyance_jipeishuijing: "◇",
  conveyance_jishuijing: "◇",
  conveyance_peishuijing: "◇",
  conveyance_peishuiqu: "◇",
};

/** 内置节点 kind 字形表（四种——core graph/nodes.py 内置域）。 */
const KIND_GLYPHS: Record<string, string> = {
  municipal_input: "▽",
  junction: "⊕",
  quality_edit: "✎",
  recycle_junction: "↻",
};

/** 单元/内置节点 → 象形字形（kind 优先；未收录回退 ▢）。 */
export function unitGlyph(unitId: string, kind: string | null): string {
  if (kind !== null) {
    return KIND_GLYPHS[kind] ?? GLYPH_FALLBACK;
  }
  return UNIT_GLYPHS[unitId] ?? GLYPH_FALLBACK;
}

/** 域色轴变量串表（业务线→var(--wp-*)——installDomainColorAxis 按模
 *  注入的 CSS 轴；消费面=SVG stroke/fill 与 inline style）。 */
export const DOMAIN_COLOR_VARS = {
  water: "var(--wp-water)",
  sludge: "var(--wp-sludge)",
  mine: "var(--wp-mine)",
  convey: "var(--wp-convey)",
} as const;

/** 未收录/清单未达回退色（灰——不误导域归属；三模恒值故字面安全，
 *  semanticColors domain_neutral 单源引用）。 */
export const NEUTRAL_DOMAIN = SEMANTIC_COLORS.domain_neutral;

/** 业务线 → 域色轴变量串（b3 变量化——bar/图标/minimap/图例共用；
 *  真源=semanticColors DOMAIN_COLORS 按模注入的 --wp-* 轴，本件零字面色）。 */
export function domainColorOf(businessLine: string | null | undefined): string {
  switch (businessLine) {
    case "municipal":
      return DOMAIN_COLOR_VARS.water;
    case "sludge":
      return DOMAIN_COLOR_VARS.sludge;
    case "mine_water":
      return DOMAIN_COLOR_VARS.mine;
    case "conveyance":
      return DOMAIN_COLOR_VARS.convey;
    default:
      return NEUTRAL_DOMAIN;
  }
}

/** 域色图标三色组条目（底/边框/前景）。 */
export interface DomainIconStyle {
  bg: string;
  border: string;
  fg: string;
}

/** 域色图标三色组（b3 变量派生组——rgba 冻结字面退役：bg/border=
 *  color-mix 自轴域色透明派生、fg=轴域色直用，三模随注入轴自动派生；
 *  中性组=三模恒值灰字面）。 */
export function domainIconStyle(businessLine: string | null | undefined): DomainIconStyle {
  const base = domainColorOf(businessLine);
  if (base === NEUTRAL_DOMAIN) {
    return {
      bg: "rgba(89,89,89,.08)",
      border: "rgba(89,89,89,.3)",
      fg: NEUTRAL_DOMAIN,
    };
  }
  return {
    bg: `color-mix(in srgb, ${base} 10%, transparent)`,
    border: `color-mix(in srgb, ${base} 38%, transparent)`,
    fg: base,
  };
}

/** 边流色（两色制 P4）：任一 sludge→泥；双端已知非 sludge→水；否则中性。
 * （b3 变量化——色值=域色轴变量串，随主题注入轴换肤。） */
export function streamColorOf(
  srcLine: string | null | undefined,
  dstLine: string | null | undefined,
): string {
  if (srcLine === "sludge" || dstLine === "sludge") {
    return DOMAIN_COLOR_VARS.sludge;
  }
  if (srcLine !== undefined && srcLine !== null && dstLine !== undefined && dstLine !== null) {
    return DOMAIN_COLOR_VARS.water;
  }
  return NEUTRAL_DOMAIN;
}
