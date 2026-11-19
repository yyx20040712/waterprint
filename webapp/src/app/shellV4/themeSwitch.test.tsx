/**
 * @vitest-environment jsdom
 *
 * 主题切换器测试（b1 主题地基批——顶带工具区三钮组）。
 *
 * 输入:  ./themeSwitch（ThemeSwitch 纯展示+store 订阅）
 * 输出:  三断言面——①三钮在场（正常/护眼/夜间+示意 chip）且当前态
 *        aria-pressed 单真；②点击=store mode+documentElement data-theme+
 *        localStorage 三面联动（jsdom 真 DOM 行为级）；③切换后重渲染
 *        pressed 态随动。
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { THEME_STORAGE_KEY, useThemeStore } from "../../shared/store/themeStore";
import { ThemeSwitch } from "./themeSwitch";

describe("ThemeSwitch 主题切换器（b1 主题地基批）", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dataset.theme = undefined;
    useThemeStore.setState({ mode: "light" });
  });
  afterEach(() => {
    cleanup();
    window.localStorage.clear();
  });

  it("三钮在场：正常/护眼/夜间+当前态 aria-pressed 单真", () => {
    render(<ThemeSwitch />);
    const group = screen.getByRole("group", { name: "界面主题" });
    expect(group).toBeTruthy();
    for (const label of ["正常", "护眼", "夜间"]) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
    const pressed = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true");
    expect(pressed.length).toBe(1);
    expect(pressed[0]?.textContent).toContain("正常");
  });

  it("点击护眼：store mode+data-theme+localStorage 三面联动", () => {
    render(<ThemeSwitch />);
    screen.getByRole("button", { name: "护眼" }).click();
    expect(useThemeStore.getState().mode).toBe("warm");
    expect(document.documentElement.dataset.theme).toBe("warm");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("warm");
  });

  it("切换后重渲染：pressed 态随动（夜间单真）", () => {
    const { rerender } = render(<ThemeSwitch />);
    useThemeStore.getState().setMode("dark");
    rerender(<ThemeSwitch />);
    const dark = screen.getByRole("button", { name: "夜间" });
    expect(dark.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: "正常" }).getAttribute("aria-pressed")).toBe(
      "false",
    );
  });
});
