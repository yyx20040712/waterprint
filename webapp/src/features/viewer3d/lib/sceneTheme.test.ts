/**
 * sceneTheme vitest（node——b4 功能面重涂 II 批：三维场景随主题四族色
 * 逐模冻结+轴三键真源读取/回退两径）。
 *
 * 输入:  ./sceneTheme（纯表+resolveSceneTheme 注入读取器）
 * 输出:  断言族：①草地/网格四键逐模字面冻结（light=现值零漂移锚）
 *        ②轴三键（engineer/label/labelOutline）：读取器空串=纯表回退
 *        ③读取器返回值透传（--wp-canvas/--wp-text/--wp-bg-page 真源）
 *        ④三模键集完备（七键/模）
 */
import { describe, expect, it } from "vitest";

import { resolveSceneTheme, sceneThemeFor } from "./sceneTheme";

describe("sceneTheme 纯表逐模冻结（b4——三维场景随主题）", () => {
  it("草地/网格四键 light 档=现值零漂移锚（像素级沿承）", () => {
    const light = sceneThemeFor("light");
    expect(light.grassWorld).toBe("#e2ece0");
    expect(light.grass).toBe("#c8dcc2");
    expect(light.gridMajor).toBe("#54719f");
    expect(light.gridMinor).toBe("#d8dee8");
  });

  it("草地/网格四键 warm/dark 档派生值冻结（改值须同步本锚）", () => {
    const warm = sceneThemeFor("warm");
    expect(warm.grassWorld).toBe("#eae4cf");
    expect(warm.grass).toBe("#d2cdaa");
    expect(warm.gridMajor).toBe("#6d6b5c");
    expect(warm.gridMinor).toBe("#ddd8c8");
    const dark = sceneThemeFor("dark");
    expect(dark.grassWorld).toBe("#1d2622");
    expect(dark.grass).toBe("#2a3530");
    expect(dark.gridMajor).toBe("#46628c");
    expect(dark.gridMinor).toBe("#2c3532");
  });

  it("三模键集完备：七键/模（grassWorld/grass/engineer/gridMajor/gridMinor/label/labelOutline）", () => {
    for (const mode of ["light", "warm", "dark"] as const) {
      expect(Object.keys(sceneThemeFor(mode)).sort()).toEqual(
        [
          "engineer",
          "grass",
          "grassWorld",
          "gridMajor",
          "gridMinor",
          "label",
          "labelOutline",
        ].sort(),
      );
    }
  });
});

describe("resolveSceneTheme 轴三键真源读取（DOM 面）", () => {
  it("读取器空串（node/jsdom 无注入面）=纯表回退（AXIS_FALLBACK 亮档字面）", () => {
    const theme = resolveSceneTheme("dark", () => "");
    expect(theme.engineer).toBe(sceneThemeFor("dark").engineer);
    expect(theme.label).toBe("#202826");
    expect(theme.labelOutline).toBe("#f2f5f3");
  });

  it("读取器返回轴计算值透传（--wp-canvas/--wp-text/--wp-bg-page 真源）", () => {
    const vars: Record<string, string> = {
      "--wp-canvas": " #131817 ",
      "--wp-text": "#e3e9e6",
      "--wp-bg-page": "#161b1a",
    };
    const theme = resolveSceneTheme("dark", (name) => vars[name] ?? "");
    expect(theme.engineer).toBe("#131817"); // trim 归一
    expect(theme.label).toBe("#e3e9e6");
    expect(theme.labelOutline).toBe("#161b1a");
    // 草地/网格四键不随读取器变（纯表派生面）
    expect(theme.grassWorld).toBe(sceneThemeFor("dark").grassWorld);
  });
});
