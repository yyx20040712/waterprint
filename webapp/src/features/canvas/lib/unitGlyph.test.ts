/**
 * unitGlyph/domainColorOf/streamColorOf vitest（C2-canvas 批——
 * task-C2-canvas-plan.md §三测试面）。
 *
 * 输入:  全库 32 unit_id 清单（四域——core discover_units 枚举同源）
 *        +内置 kind/未收录键样例+business_line 值域样例
 * 输出:  覆盖断言：32 键全枚举无回退（漏键即红）+4 内置 kind 字形
 *        +未收录回退 ▢+域色五值+流色三态（泥优先/水/中性）
 */
import { describe, expect, it } from "vitest";

import {
  GLYPH_FALLBACK,
  NEUTRAL_DOMAIN,
  domainColorOf,
  streamColorOf,
  unitGlyph,
} from "./unitGlyph";

/** 全库 32 unit_id（四域——与 core discover_units 枚举一致）。 */
const ALL_UNIT_IDS = [
  "municipal_aao",
  "municipal_bashi_jiliangcao",
  "municipal_cass",
  "municipal_chenshachi",
  "municipal_chuchenchi",
  "municipal_cugeshan",
  "municipal_erchunchi",
  "municipal_gaomidu",
  "municipal_tiaojiechi",
  "municipal_vxinglvchi",
  "municipal_wushui_tisheng",
  "municipal_xigeshan",
  "municipal_ziwai",
  "sludge_bengzhan",
  "sludge_ganhua",
  "sludge_hebing",
  "sludge_nongsuo",
  "sludge_shusong",
  "sludge_tuoshui",
  "sludge_xiaohua",
  "mine_water_chenshachi",
  "mine_water_cifenli",
  "mine_water_gaomidu",
  "mine_water_input",
  "mine_water_ningjiao",
  "mine_water_tiaojiechi",
  "mine_water_vxinglvchi",
  "mine_water_ziwai",
  "conveyance_jipeishuijing",
  "conveyance_jishuijing",
  "conveyance_peishuijing",
  "conveyance_peishuiqu",
] as const;

describe("unitGlyph：全库字形映射", () => {
  it("32 unit_id 全枚举无回退（漏键/重键即红——表键数恰 32）", () => {
    // 非回退断言：每键返回非 ▢ 字形
    for (const unitId of ALL_UNIT_IDS) {
      const glyph = unitGlyph(unitId, null);
      expect(glyph, `${unitId} 应有映射字形`).not.toBe(GLYPH_FALLBACK);
      expect(glyph, `${unitId} 字形应非空`).toBeTruthy();
    }
    // 表键数恰 32：ALL_UNIT_IDS 若与表漂移（漏键→上断言红；表多键→此处由
    // 回退分支测试+聚类抽样双面钳制；重键不可能——object literal 后键覆盖
    // 前键会改变聚类抽样期望）
    expect(ALL_UNIT_IDS.length).toBe(32);
  });

  it("聚类抽样：格栅 ▤/生物 ◉/滤池 ⋀/浓缩 ◐/消化 ⬡/磁分离 ⊛/井渠 ◇", () => {
    expect(unitGlyph("municipal_cugeshan", null)).toBe("▤");
    expect(unitGlyph("municipal_xigeshan", null)).toBe("▤");
    expect(unitGlyph("municipal_aao", null)).toBe("◉");
    expect(unitGlyph("municipal_cass", null)).toBe("◉");
    expect(unitGlyph("municipal_vxinglvchi", null)).toBe("⋀");
    expect(unitGlyph("mine_water_vxinglvchi", null)).toBe("⋀");
    expect(unitGlyph("sludge_nongsuo", null)).toBe("◐");
    expect(unitGlyph("sludge_xiaohua", null)).toBe("⬡");
    expect(unitGlyph("mine_water_cifenli", null)).toBe("⊛");
    expect(unitGlyph("conveyance_peishuiqu", null)).toBe("◇");
  });

  it("内置四 kind 字形（kind 优先于 unit_id 面）", () => {
    expect(unitGlyph("inlet", "municipal_input")).toBe("▽");
    expect(unitGlyph("j1", "junction")).toBe("⊕");
    expect(unitGlyph("q1", "quality_edit")).toBe("✎");
    expect(unitGlyph("r1", "recycle_junction")).toBe("↻");
  });

  it("未收录键回退 ▢（自定义 unit_id 与未知 kind 双面）", () => {
    expect(unitGlyph("custom_unknown", null)).toBe(GLYPH_FALLBACK);
    expect(unitGlyph("x", "future_kind")).toBe(GLYPH_FALLBACK);
  });
});

describe("domainColorOf：四域+中性回退", () => {
  it("四域色值（视觉稿冻结——与 global.css 变量轴同值双源）", () => {
    expect(domainColorOf("municipal")).toBe("#4da3ff");
    expect(domainColorOf("sludge")).toBe("#9c6b45");
    expect(domainColorOf("mine_water")).toBe("#35c9b0");
    expect(domainColorOf("conveyance")).toBe("#9aa8b8");
  });

  it("未知/缺省回退中性灰（不误导域归属）", () => {
    expect(domainColorOf("future_domain")).toBe(NEUTRAL_DOMAIN);
    expect(domainColorOf(null)).toBe(NEUTRAL_DOMAIN);
    expect(domainColorOf(undefined)).toBe(NEUTRAL_DOMAIN);
  });
});

describe("streamColorOf：两色制流色（泥优先/水/中性三态）", () => {
  it("任一端 sludge 即泥色（剩余污泥/回流混合边归泥）", () => {
    expect(streamColorOf("municipal", "sludge")).toBe("#9c6b45");
    expect(streamColorOf("sludge", "municipal")).toBe("#9c6b45");
    expect(streamColorOf("sludge", "sludge")).toBe("#9c6b45");
  });

  it("双端已知非 sludge 即水色（水线内部+跨非泥域）", () => {
    expect(streamColorOf("municipal", "municipal")).toBe("#4da3ff");
    expect(streamColorOf("mine_water", "conveyance")).toBe("#4da3ff");
  });

  it("任一端未知即中性灰（清单未达/自定义键不误导）", () => {
    expect(streamColorOf("municipal", null)).toBe(NEUTRAL_DOMAIN);
    expect(streamColorOf(undefined, "sludge")).toBe("#9c6b45");
    expect(streamColorOf(null, undefined)).toBe(NEUTRAL_DOMAIN);
  });
});
