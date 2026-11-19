/**
 * GR-39 双源联动清单机检化守卫（2A5——A 线色值单源批；b1 主题地基批
 * 2026-11-19 三态扩面：同值断言自单亮基线扩为 light/warm/dark 三模逐对）。
 *
 * 输入:  ./global.css 原文（node:fs 直读——三主题块 ：root=light 基线+
 *        html[data-theme="warm"/"dark"] 两覆写块）+./themeModes
 *        globalThemeConfigFor（静态 import——三模 antd 配置单源）
 * 输出:  四守卫面——①三主题块变量轴解析（--wp-* 声明抽取+hex 小写归一
 *        ——解析面自证锚）；②同值对断言三模全集（GR-39 清单对逐模：
 *        改任一侧任一模不同步即红）；③清单↔测试互证（global.css 头注
 *        联动清单逐行锚在场——删行即红）；④作用域机制守卫（.wp-v4-root
 *        scoped 块零 --wp- 声明〔防继承遮蔽三主题块〕+data-theme 选择器
 *        三块在场）。
 *
 * B4 沿革（2026-10-09）：全部同值断言亮值化；b1 主题地基批：色板整体
 *   换为已批准设计稿三主题值（正常/护眼/夜间），断言面三模化——
 *   单模漂移（如只改 dark 块漏改 antd 侧）即红。
 *
 * 形态说明（范式=domainColorAxis.test.ts：node:fs 读 CSS 原文+静态
 *   import JS 模块，node 直测零 jsdom）。antd 无槽位自持真源
 *   （--wp-gold/-soft/--wp-scrollbar-hover/--wp-canvas/--wp-shadow/
 *   soft 三键）不入对表——global.css 头注口径；其逐模冻结锚在
 *   lightBaseline.test（色板冻结面）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { THEME_MODES, type ThemeMode } from "../shared/store/themeStore";
import { globalThemeConfigFor } from "./themeModes";

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");

/** 归一比较口径：trim+小写（hex 大小写漂移不计，值漂移计）。 */
function norm(value: string | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

/** 主题块选择器（light=：root 基线；warm/dark=html[data-theme] 覆写）。 */
function themeSelector(mode: ThemeMode): string {
  return mode === "light" ? ":root" : `html[data-theme="${mode}"]`;
}

/** 指定主题块内 --wp-* 声明抽取 → Map（值侧已归一——供同值对断言消费）。
 *  沿 R1（d1-W1）剥注释口径：防头注注释含伪块劫持/伪声明覆盖真值。 */
function parseThemeVars(css: string, mode: ThemeMode): Map<string, string> {
  const noComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const selector = themeSelector(mode).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const block =
    noComments.match(new RegExp(`${selector}\\s*\\{([^}]*)\\}`))?.[1] ?? "";
  const vars = new Map<string, string>();
  for (const m of block.matchAll(/(--wp-[\w-]+)\s*:\s*([^;]+);/g)) {
    const [, name, value] = m;
    if (name !== undefined && value !== undefined) {
      vars.set(name, norm(value));
    }
  }
  return vars;
}

const cssVars: Record<ThemeMode, Map<string, string>> = {
  light: parseThemeVars(globalCss, "light"),
  warm: parseThemeVars(globalCss, "warm"),
  dark: parseThemeVars(globalCss, "dark"),
};

/** 双源契约成对键（三模块各须齐——双侧同步缺失的静默绿通道收口）。 */
const PAIRED_KEYS = [
  "--wp-bg-page",
  "--wp-bg-container",
  "--wp-bg-elevated",
  "--wp-bg-deep",
  "--wp-border",
  "--wp-border-2",
  "--wp-text",
  "--wp-text-2",
  "--wp-text-3",
  "--wp-accent",
  "--wp-on-accent",
  "--wp-success",
  "--wp-warning",
  "--wp-error",
  "--wp-font-mono",
  "--wp-accent-soft",
  "--wp-success-soft",
  "--wp-warning-soft",
  "--wp-error-soft",
  "--wp-canvas",
  "--wp-shadow",
  "--wp-gold",
  "--wp-gold-soft",
  "--wp-scrollbar-hover",
] as const;

describe("GR-39 双源联动清单机检化（2A5·b1 三态扩面）", () => {
  it("三主题块解析：变量轴声明可抽取（解析面自证——三模锚键实值在场）", () => {
    // 防正则腐化前置拦：解析坏=同值对断言面全红的前置信号（三模各取
    // 代表键设计稿值字面自证）
    expect(cssVars.light.get("--wp-bg-page")).toBe("#f2f5f3");
    expect(cssVars.warm.get("--wp-bg-page")).toBe("#eee9dd");
    expect(cssVars.dark.get("--wp-bg-page")).toBe("#161b1a");
    expect(cssVars.light.get("--wp-accent")).toBe("#246b63");
    expect(cssVars.dark.get("--wp-accent")).toBe("#7bb9ac");
    for (const mode of THEME_MODES) {
      for (const key of PAIRED_KEYS) {
        expect(cssVars[mode].has(key), `${mode} 轴键缺失：${key}`).toBe(true);
        expect(
          cssVars[mode].get(key),
          `${mode} 轴键空白值：${key}`,
        ).not.toBe("");
      }
    }
  });

  it("同值对·三模全集：--wp-* 轴 ↔ antd token（改任一侧任一模不同步即红）", () => {
    for (const mode of THEME_MODES) {
      const vars = cssVars[mode];
      const config = globalThemeConfigFor(mode);
      const t = config.token ?? {};
      const layout = config.components?.Layout ?? {};
      const tabs = config.components?.Tabs ?? {};
      const table = config.components?.Table ?? {};
      // 四档底
      expect(vars.get("--wp-bg-page"), `${mode} bg-page`).toBe(
        norm(t.colorBgLayout),
      );
      expect(vars.get("--wp-bg-page"), `${mode} headerBg`).toBe(
        norm(layout.headerBg),
      );
      expect(vars.get("--wp-bg-page"), `${mode} bodyBg`).toBe(
        norm(layout.bodyBg),
      );
      expect(vars.get("--wp-bg-container"), `${mode} bg-container`).toBe(
        norm(layout.siderBg),
      );
      // 稿 paper=阅读面：container/elevated 两 token 同值 bg-elevated 轴
      expect(vars.get("--wp-bg-elevated"), `${mode} colorBgContainer`).toBe(
        norm(t.colorBgContainer),
      );
      expect(vars.get("--wp-bg-elevated"), `${mode} colorBgElevated`).toBe(
        norm(t.colorBgElevated),
      );
      expect(vars.get("--wp-bg-deep"), `${mode} Table.headerBg`).toBe(
        norm(table.headerBg),
      );
      expect(vars.get("--wp-bg-deep"), `${mode} Table.rowHoverBg`).toBe(
        norm(table.rowHoverBg),
      );
      // 边线两档
      expect(vars.get("--wp-border"), `${mode} border`).toBe(
        norm(t.colorBorder),
      );
      expect(vars.get("--wp-border-2"), `${mode} border-2`).toBe(
        norm(t.colorBorderSecondary),
      );
      expect(vars.get("--wp-border-2"), `${mode} Table.colorSplit`).toBe(
        norm(table.colorSplit),
      );
      // 文字三档
      expect(vars.get("--wp-text"), `${mode} text`).toBe(norm(t.colorText));
      expect(vars.get("--wp-text-2"), `${mode} text-2`).toBe(
        norm(t.colorTextSecondary),
      );
      expect(vars.get("--wp-text-3"), `${mode} text-3`).toBe(
        norm(t.colorTextTertiary),
      );
      // 操作色（AC 族四 token+Tabs 选中两键）
      expect(vars.get("--wp-accent"), `${mode} colorPrimary`).toBe(
        norm(t.colorPrimary),
      );
      expect(t.colorInfo, `${mode} colorInfo`).toBe(t.colorPrimary);
      expect(t.colorLink, `${mode} colorLink`).toBe(t.colorPrimary);
      expect(vars.get("--wp-accent"), `${mode} inkBar`).toBe(
        norm(tabs.inkBarColor),
      );
      expect(vars.get("--wp-accent"), `${mode} itemSelected`).toBe(
        norm(tabs.itemSelectedColor),
      );
      // 主操作面文字（稿 on-accent）——b4 增对（aiZone 发送钮/报告导出主钮消费）
      expect(vars.get("--wp-on-accent"), `${mode} on-accent`).toBe(
        norm(t.colorTextLightSolid),
      );
      // 语义三色
      expect(vars.get("--wp-success"), `${mode} success`).toBe(
        norm(t.colorSuccess),
      );
      expect(vars.get("--wp-warning"), `${mode} warning`).toBe(
        norm(t.colorWarning),
      );
      expect(vars.get("--wp-error"), `${mode} error`).toBe(norm(t.colorError));
      // Tabs 未选/悬浮按压两态=文字轴同值（providers 自注清单成员）
      expect(vars.get("--wp-text-2"), `${mode} itemColor`).toBe(
        norm(tabs.itemColor),
      );
      expect(vars.get("--wp-text"), `${mode} itemHover`).toBe(
        norm(tabs.itemHoverColor),
      );
      expect(vars.get("--wp-text"), `${mode} itemActive`).toBe(
        norm(tabs.itemActiveColor),
      );
      // 字体串逐字同值（mono 栈两侧漂移即红）
      expect(vars.get("--wp-font-mono"), `${mode} font-mono`).toBe(
        norm(t.fontFamilyCode),
      );
    }
  });

  it("作用域机制守卫：data-theme 三块在场+.wp-v4-root scoped 块零 --wp- 声明", () => {
    // 三主题块选择器在场（删块=该模断联即红——解析面兜底）
    expect(globalCss).toContain(':root {');
    expect(globalCss).toContain('html[data-theme="warm"] {');
    expect(globalCss).toContain('html[data-theme="dark"] {');
    // B7 清点批兑现（b1）：scoped 块若持 --wp- 声明=继承遮蔽 html 级
    // 主题值（最近祖先胜出与特异性无关），三主题换肤必被钉死——零声明
    const scoped = globalCss.match(/\.wp-v4-root\s*\{([^}]*)\}/)?.[1] ?? "";
    const scopedVars = [...scoped.matchAll(/--wp[\w-]*\s*:/g)];
    expect(scopedVars, "scoped 块 --wp- 声明复入").toEqual([]);
  });

  it("清单↔测试互证：头注联动清单逐行锚在场（防清单腐化——删行即红）", () => {
    // global.css 头注 GR-39 三态清单行（逐字锚）——稿 token 对应注记随行
    expect(globalCss).toContain(
      "--wp-bg-page     ↔ providers colorBgLayout（+Layout.headerBg/bodyBg——稿 bg）",
    );
    expect(globalCss).toContain(
      "--wp-bg-container ↔ providers components.Layout.siderBg（稿 surface）",
    );
    expect(globalCss).toContain(
      "--wp-bg-elevated ↔ providers colorBgContainer/colorBgElevated（稿 paper 阅读面）",
    );
    expect(globalCss).toContain(
      "--wp-bg-deep     ↔ providers components.Table.headerBg/rowHoverBg（稿 surface-2）",
    );
    expect(globalCss).toContain(
      "--wp-border      ↔ providers colorBorder（稿 line）",
    );
    expect(globalCss).toContain(
      "--wp-border-2    ↔ providers colorBorderSecondary（+Table.colorSplit——稿 line-soft）",
    );
    expect(globalCss).toContain(
      "--wp-text/2/3    ↔ providers colorText/Secondary/Tertiary（稿 ink/muted/faint）",
    );
    expect(globalCss).toContain(
      "--wp-accent      ↔ providers colorPrimary/Info/Link（+Tabs inkBar/itemSelected——稿 accent）",
    );
    expect(globalCss).toContain(
      "--wp-on-accent   ↔ providers colorTextLightSolid（稿 on-accent——主操作面文字）",
    );
    expect(globalCss).toContain(
      "--wp-success     ↔ providers colorSuccess（稿 ok）",
    );
    expect(globalCss).toContain(
      "--wp-warning     ↔ providers colorWarning（稿 warn）",
    );
    expect(globalCss).toContain(
      "--wp-error       ↔ providers colorError（稿 error）",
    );
    expect(globalCss).toContain(
      "--wp-font-mono   ↔ providers fontFamilyCode",
    );
    // 机检化注记锚（清单节尾注记行——删注记即红）
    expect(globalCss).toContain(
      "themeLinkage.test 三态断言",
    );
  });
});
