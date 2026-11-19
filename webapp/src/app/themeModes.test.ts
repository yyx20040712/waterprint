/**
 * 三主题 antd 配置面测试（b1 主题地基批——app/themeModes 冻结锚）。
 *
 * 输入:  ./themeModes 三导出（MODE_COLORS/globalThemeConfigFor/
 *        v4ThemeConfigFor）+../shared/store/themeStore THEME_MODES
 * 输出:  三断言面——①三模色板=已批准设计稿字面（bg 四档/border 两档/
 *        text 三档/accent+onAccent/语义三色+soft 三键/canvas/shadow——
 *        逐键逐模冻结）；②globalThemeConfigFor：algorithm 映射
 *        （light·warm=default/dark=dark）+seed/components 逐键=色板值
 *        +密度冻结 13/28/6；③v4ThemeConfigFor：同色板+密度 12/26/6
 *        （scoped 面密度差=既有 v4 形）。
 */
import { theme } from "antd";
import { describe, expect, it } from "vitest";

import { THEME_MODES } from "../shared/store/themeStore";
import { MODE_COLORS, globalThemeConfigFor, v4ThemeConfigFor } from "./themeModes";

/** 已批准设计稿三主题色板字面（.zcode/dev-troupe/frontend-redesign/
 *  index.html :root/warm/dark 三块——改值须对账设计稿裁决）。 */
const DRAFT_PALETTES = {
  light: {
    bgPage: "#f2f5f3", bgContainer: "#fafcfa", bgElevated: "#fdfefc",
    bgDeep: "#f5f7f5", border: "#d4dcd7", border2: "#e5eae6",
    accent: "#246b63", accentSoft: "#e2eeea", onAccent: "#f7fbfa",
    text: "#202826", text2: "#5c6965", text3: "#65716b",
    success: "#2f7151", successSoft: "#e4efe7",
    warning: "#87600f", warningSoft: "#f4ecd9",
    error: "#a3453d", errorSoft: "#f5e6e3", canvas: "#edf2f0",
    shadow: "rgba(39, 55, 49, 0.08)",
  },
  warm: {
    bgPage: "#eee9dd", bgContainer: "#f7f2e7", bgElevated: "#fbf7ee",
    bgDeep: "#f1ebdf", border: "#d7cebc", border2: "#e6ddcc",
    accent: "#76613d", accentSoft: "#eae0cd", onAccent: "#fffaf0",
    text: "#302f29", text2: "#666459", text3: "#6b675b",
    success: "#52704c", successSoft: "#e7eadb",
    warning: "#765214", warningSoft: "#eee2c8",
    error: "#8b493e", errorSoft: "#eee0d7", canvas: "#eae3d5",
    shadow: "rgba(74, 61, 39, 0.08)",
  },
  dark: {
    bgPage: "#161b1a", bgContainer: "#1e2423", bgElevated: "#242b29",
    bgDeep: "#1a201f", border: "#39433f", border2: "#2c3532",
    accent: "#7bb9ac", accentSoft: "#263c36", onAccent: "#112823",
    text: "#e3e9e6", text2: "#aab6b1", text3: "#8b9892",
    success: "#88bb96", successSoft: "#24382b",
    warning: "#d2ae6b", warningSoft: "#3b3323",
    error: "#df9289", errorSoft: "#402b29", canvas: "#131817",
    shadow: "rgba(0, 0, 0, 0.18)",
  },
} as const;

describe("themeModes 三主题 antd 配置面（b1 主题地基批）", () => {
  it("三模色板=设计稿字面（逐键逐模冻结——19 键）", () => {
    expect([...THEME_MODES].sort()).toEqual(["dark", "light", "warm"]);
    for (const mode of THEME_MODES) {
      expect(MODE_COLORS[mode], `色板键集 ${mode}`).toEqual({
        ...DRAFT_PALETTES[mode],
      });
    }
  });

  it("globalThemeConfigFor：algorithm 映射+seed/components=色板值+密度冻结 13/28/6", () => {
    for (const mode of THEME_MODES) {
      const config = globalThemeConfigFor(mode);
      const c = DRAFT_PALETTES[mode];
      expect(
        config.algorithm,
        `${mode} 算法`,
      ).toBe(mode === "dark" ? theme.darkAlgorithm : theme.defaultAlgorithm);
      const t = config.token ?? {};
      expect(t.colorPrimary).toBe(c.accent);
      expect(t.colorInfo).toBe(c.accent);
      expect(t.colorLink).toBe(c.accent);
      expect(t.colorBgLayout).toBe(c.bgPage);
      expect(t.colorBgContainer).toBe(c.bgElevated);
      expect(t.colorBgElevated).toBe(c.bgElevated);
      expect(t.colorBorder).toBe(c.border);
      expect(t.colorBorderSecondary).toBe(c.border2);
      expect(t.colorText).toBe(c.text);
      expect(t.colorTextSecondary).toBe(c.text2);
      expect(t.colorTextTertiary).toBe(c.text3);
      expect(t.colorSuccess).toBe(c.success);
      expect(t.colorWarning).toBe(c.warning);
      expect(t.colorError).toBe(c.error);
      // 主操作面文字=稿 on-accent（夜间浅青底配深字——非默认纯白）
      expect(t.colorTextLightSolid).toBe(c.onAccent);
      // M1 密度冻结值（仅换色不换密度）
      expect(t.fontSize).toBe(13);
      expect(t.controlHeight).toBe(28);
      expect(t.borderRadius).toBe(6);
      const layout = config.components?.Layout ?? {};
      expect(layout.headerBg).toBe(c.bgPage);
      expect(layout.headerHeight).toBe(48);
      expect(layout.siderBg).toBe(c.bgContainer);
      expect(layout.bodyBg).toBe(c.bgPage);
      const tabs = config.components?.Tabs ?? {};
      expect(tabs.inkBarColor).toBe(c.accent);
      expect(tabs.itemColor).toBe(c.text2);
      expect(tabs.itemHoverColor).toBe(c.text);
      expect(tabs.itemActiveColor).toBe(c.text);
      expect(tabs.itemSelectedColor).toBe(c.accent);
      const table = config.components?.Table ?? {};
      expect(table.headerBg).toBe(c.bgDeep);
      expect(table.rowHoverBg).toBe(c.bgDeep);
      expect(table.colorSplit).toBe(c.border2);
    }
  });

  it("v4ThemeConfigFor：同色板+密度 12/26/6（scoped 面密度差=既有 v4 形）", () => {
    for (const mode of THEME_MODES) {
      const config = v4ThemeConfigFor(mode);
      const c = DRAFT_PALETTES[mode];
      expect(
        config.algorithm,
        `${mode} v4 算法`,
      ).toBe(mode === "dark" ? theme.darkAlgorithm : theme.defaultAlgorithm);
      const t = config.token ?? {};
      expect(t.colorPrimary).toBe(c.accent);
      expect(t.colorBgLayout).toBe(c.bgPage);
      expect(t.colorText).toBe(c.text);
      expect(t.fontSize).toBe(12);
      expect(t.controlHeight).toBe(26);
      expect(config.components?.Layout?.siderBg).toBe(c.bgContainer);
      expect(config.components?.Table?.headerBg).toBe(c.bgDeep);
    }
  });
});
