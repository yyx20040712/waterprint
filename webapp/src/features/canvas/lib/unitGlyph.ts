/**
 * 象形图标+域色纯函数：unit_id/kind → Unicode 工艺字形；business_line →
 * 节点/连线色（C2-canvas 画布标签重制——task-C2-canvas-plan.md §二 P3/P4）。
 *
 * 输入:  unitId（design.nodes 键）+kind（内置四 kind 或 null）；
 *        business_line（/api/units UnitMetaEntry 字段——四值
 *        municipal/sludge/mine_water/conveyance，全库 32 单元前缀一致）
 * 输出:  象形字形串+域色/流色串（CSS 消费面——SVG stroke/fill 与
 *        inline style 同串直用）
 *
 * 规格说明（C2-canvas 批，glm D 项①②痛点处置）：
 *   - 字形=Unicode 几何稳定集（视觉稿态三全谱渲染实证——Windows/
 *     Chromium 零缺字；避 emoji 化字符如 ☀）；映射=工艺功能聚类
 *     （32 unit_id 精确键——unitGlyph.test.ts 全库枚举防漏键）；
 *     未收录键回退 ▢（自定义键不炸——显示层降级非错误）；
 *   - 域色四色制+选中鎏金=视觉稿 A 冻结语言；**本文件为四域色主源**
 *     （R-G3 联动清单——GC-02 处置）：同值字面量消费面=global.css 变量
 *     轴（--wp-water/sludge/mine/convey）+CanvasFlow LEGEND_LINES+
 *     UnitNode（SELECT 鎏金组与 DOMAIN_ICON_STYLES 域派生组）——改色
 *     红线=N 处联动（本表
 *     为比对基准）；中性灰 #595959=未收录键回退（antd 无槽位灰——
 *     PortHandle NEUTRAL_BORDER 先例）；
 *   - 流色两色制（P4）：任一端 sludge→泥棕（污泥去向判定——剩余
 *     污泥/回流混合边归泥）；双端已知非 sludge→水蓝；任一端未知
 *     （未收录）→中性灰（不误导域归属）；recycle 虚线由投影层
 *     叠加（本函数不管线型只管色）；
 *   - 零运行期库 import（projectFlow 同构——node 测试不拖 DOM 面）。
 */

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

/** 业务线 → 节点域色（bar/图标/minimap/图例共用——视觉稿冻结值）。 */
export function domainColorOf(businessLine: string | null | undefined): string {
  switch (businessLine) {
    case "municipal":
      return "#4da3ff";
    case "sludge":
      return "#9c6b45";
    case "mine_water":
      return "#35c9b0";
    case "conveyance":
      return "#9aa8b8";
    default:
      return NEUTRAL_DOMAIN;
  }
}

/** 未收录/清单未达回退色（灰——不误导域归属）。 */
export const NEUTRAL_DOMAIN = "#595959";

/** 边流色（两色制 P4）：任一 sludge→泥；双端已知非 sludge→水；否则中性。 */
export function streamColorOf(
  srcLine: string | null | undefined,
  dstLine: string | null | undefined,
): string {
  if (srcLine === "sludge" || dstLine === "sludge") {
    return "#9c6b45";
  }
  if (srcLine !== undefined && srcLine !== null && dstLine !== undefined && dstLine !== null) {
    return "#4da3ff";
  }
  return NEUTRAL_DOMAIN;
}
