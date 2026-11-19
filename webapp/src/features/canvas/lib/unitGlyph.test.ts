/**
 * unitGlyph/domainColorOf/domainIconStyle/streamColorOf vitest（C2-canvas
 * 批——task-C2-canvas-plan.md §三测试面；图标对齐小批 +domainIconStyle；
 * b3 功能面重涂批：域色/流色断言面改 --wp-* 轴变量串〔随主题注入轴换肤
 * ——原 light 档冻结 hex 断言退役〕）。
 *
 * 输入:  全库 32 unit_id 清单（四域——core discover_units 枚举同源）
 *        +内置 kind/未收录键样例+business_line 值域样例
 * 输出:  覆盖断言：32 键全枚举无回退（漏键即红）+4 内置 kind 字形
 *        +未收录回退 ▢+域色五值（四域=轴变量串+中性恒值）+图标三色组
 *        （color-mix 派生）+流色三态（泥优先/水/中性）
 */
import { describe, expect, it } from "vitest";

import {
  GLYPH_FALLBACK,
  NEUTRAL_DOMAIN,
  domainColorOf,
  domainIconStyle,
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
  it("32 unit_id 全枚举无回退（漏键方向完备钳制；多键方向由聚类抽样钳制"
      + "——GC-07 措辞收窄：object literal 重键=后键覆盖前键必改抽样期望）", () => {
    // 非回退断言：每键返回非 ▢ 字形（表漏 ANY 键即红——防漏主目标）
    for (const unitId of ALL_UNIT_IDS) {
      const glyph = unitGlyph(unitId, null);
      expect(glyph, `${unitId} 应有映射字形`).not.toBe(GLYPH_FALLBACK);
      expect(glyph, `${unitId} 字形应非空`).toBeTruthy();
    }
    // 清单长度自证（测试面常量——与 core discover_units 枚举同源维护）
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

describe("domainColorOf：四域+中性回退（b3 域色三态收口——轴变量串）", () => {
  it("四域=--wp-* 轴变量串（真源=DOMAIN_COLORS 按模注入轴——零字面色）", () => {
    expect(domainColorOf("municipal")).toBe("var(--wp-water)");
    expect(domainColorOf("sludge")).toBe("var(--wp-sludge)");
    expect(domainColorOf("mine_water")).toBe("var(--wp-mine)");
    expect(domainColorOf("conveyance")).toBe("var(--wp-convey)");
  });

  it("未知/缺省回退中性灰（不误导域归属；三模恒值字面）", () => {
    expect(domainColorOf("future_domain")).toBe(NEUTRAL_DOMAIN);
    expect(domainColorOf(null)).toBe(NEUTRAL_DOMAIN);
    expect(domainColorOf(undefined)).toBe(NEUTRAL_DOMAIN);
  });
});

describe("streamColorOf：两色制流色（泥优先/水/中性三态——轴变量串）", () => {
  it("任一端 sludge 即泥色（剩余污泥/回流混合边归泥）", () => {
    expect(streamColorOf("municipal", "sludge")).toBe("var(--wp-sludge)");
    expect(streamColorOf("sludge", "municipal")).toBe("var(--wp-sludge)");
    expect(streamColorOf("sludge", "sludge")).toBe("var(--wp-sludge)");
  });

  it("双端已知非 sludge 即水色（水线内部+跨非泥域）", () => {
    expect(streamColorOf("municipal", "municipal")).toBe("var(--wp-water)");
    expect(streamColorOf("mine_water", "conveyance")).toBe("var(--wp-water)");
  });

  it("任一端未知即中性灰（清单未达/自定义键不误导）", () => {
    expect(streamColorOf("municipal", null)).toBe(NEUTRAL_DOMAIN);
    expect(streamColorOf(undefined, "sludge")).toBe("var(--wp-sludge)");
    expect(streamColorOf(null, undefined)).toBe(NEUTRAL_DOMAIN);
  });
});

describe("domainIconStyle：域色图标三色组（b3 派生组——随注入轴三态）", () => {
  it("四域=color-mix 自轴域色派生（bg 10%/border 38%/fg=轴色——零字面色）", () => {
    expect(domainIconStyle("municipal")).toEqual({
      bg: "color-mix(in srgb, var(--wp-water) 10%, transparent)",
      border: "color-mix(in srgb, var(--wp-water) 38%, transparent)",
      fg: "var(--wp-water)",
    });
    expect(domainIconStyle("sludge")).toEqual({
      bg: "color-mix(in srgb, var(--wp-sludge) 10%, transparent)",
      border: "color-mix(in srgb, var(--wp-sludge) 38%, transparent)",
      fg: "var(--wp-sludge)",
    });
    expect(domainIconStyle("mine_water").fg).toBe("var(--wp-mine)");
    expect(domainIconStyle("conveyance").fg).toBe("var(--wp-convey)");
  });

  it("未知/缺省回退中性灰组（三模恒值字面——bg/border/fg 三键齐）", () => {
    expect(domainIconStyle("future_domain")).toEqual({
      bg: "rgba(89,89,89,.08)", border: "rgba(89,89,89,.3)", fg: "#595959",
    });
    expect(domainIconStyle(null)).toEqual(domainIconStyle(undefined));
  });
});
