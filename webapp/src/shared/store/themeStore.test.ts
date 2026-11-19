/**
 * @vitest-environment jsdom
 *
 * 主题模式 store 测试（b1 主题地基批——三主题体系模式真源）。
 *
 * 输入:  ./themeStore 五导出（THEME_STORAGE_KEY/readStoredThemeMode/
 *        applyThemeMode/useThemeStore+THEME_MODES/THEME_MODE_LABELS）
 * 输出:  四断言面——①读存储三态（缺席=light/合法值直出/非法回退 light）；
 *        ②applyThemeMode 双面（documentElement data-theme 属性+域色四轴
 *        按模重注入——夜间档深色域色）；③setMode 三面联动（状态/
 *        localStorage 持久化/DOM 应用）；④值域与标签冻结（三模序+中文
 *        标签+持久化键名）。
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  THEME_MODES,
  THEME_MODE_LABELS,
  THEME_STORAGE_KEY,
  applyThemeMode,
  readStoredThemeMode,
  useThemeStore,
} from "./themeStore";

describe("themeStore 三主题模式真源（b1 主题地基批）", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dataset.theme = undefined;
    useThemeStore.setState({ mode: "light" });
  });
  afterEach(() => {
    window.localStorage.clear();
  });

  it("值域与标签冻结：三模声明序+中文标签+持久化键名", () => {
    expect([...THEME_MODES]).toEqual(["light", "warm", "dark"]);
    expect(THEME_MODE_LABELS).toEqual({
      light: "正常",
      warm: "护眼",
      dark: "夜间",
    });
    expect(THEME_STORAGE_KEY).toBe("waterprint.theme");
  });

  it("readStoredThemeMode 三态：缺席=light/合法值直出/非法回退 light", () => {
    expect(readStoredThemeMode()).toBe("light");
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    expect(readStoredThemeMode()).toBe("dark");
    window.localStorage.setItem(THEME_STORAGE_KEY, "blue");
    expect(readStoredThemeMode()).toBe("light");
    window.localStorage.setItem(THEME_STORAGE_KEY, "");
    expect(readStoredThemeMode()).toBe("light");
  });

  it("applyThemeMode：data-theme 属性+域色四轴按模注入（夜间档）", () => {
    applyThemeMode("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    // 域色四轴随模（夜间档设计值——真源=semanticColors DOMAIN_COLORS.dark）
    expect(
      document.documentElement.style.getPropertyValue("--wp-water"),
    ).toBe("#78acc0");
    expect(
      document.documentElement.style.getPropertyValue("--wp-sludge"),
    ).toBe("#c09a78");
    // 再切回亮色=重注入亮值（幂等换肤）
    applyThemeMode("light");
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(
      document.documentElement.style.getPropertyValue("--wp-water"),
    ).toBe("#286b86");
  });

  it("setMode 三面联动：store 状态+localStorage 持久化+DOM 应用", () => {
    useThemeStore.getState().setMode("warm");
    expect(useThemeStore.getState().mode).toBe("warm");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("warm");
    expect(document.documentElement.dataset.theme).toBe("warm");
    expect(
      document.documentElement.style.getPropertyValue("--wp-convey"),
    ).toBe("#77766e");
  });
});
