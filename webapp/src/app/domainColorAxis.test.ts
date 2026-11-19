/**
 * 域色 CSS 轴 app 层守卫（批6n UF-53 双轴归一——门一回炉双席 W 处置；
 * b1 主题地基批：providers 装载期接线自 installDomainColorAxis 直调改
 * themeStore.applyThemeMode〔data-theme 属性+按模注入〕——守卫面随动）。
 *
 * 输入:  ./global.css 原文+./providers 模块（静态 import——装载期求值）+
 *        ../shared/store/themeStore（装载期 readStoredThemeMode→light）+
 *        ../shared/ui/semanticColors domainCssVarsFor（期望值真源）
 * 输出:  两守卫面——①global.css 域色声明退役守卫（#hex/rgb(/hsl(/
 *        color-mix( 四形态声明不得复入〔k1-W3/d1-W2 扩形态〕——全文件
 *        口径非仅 :root〔d1-N4〕）+注入指针在场；②providers 装载期接线
 *        行为级守卫（vi.hoisted 前置 stub document——先于 import 求值
 *        执行〔vitest 变换保证〕；装载即 applyThemeMode：data-theme=
 *        light+light 档域色四键逐键 setProperty——删调用/条件化/迁位
 *        即红）。
 *
 * 形态说明（沿 instAsset.test.ts node:fs 先例+vi.hoisted 先例——零
 *   jsdom 红线；静态 import 走常规导入相与其它 antd 测试件同径）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { domainCssVarsFor } from "../shared/ui/semanticColors";
import { Providers } from "./providers";

/** 装载期接线观测桩（vi.hoisted=先于上方 import 求值执行——stub 就位
 *  后 providers 模块装载即触发 applyThemeMode（data-theme 写入+light
 *  档域色逐键 setProperty），两面调用集落此——单桩双面防后桩覆盖前桩）。 */
const wire = vi.hoisted(() => {
  const calls: Array<[string, string]> = [];
  const dataset: Record<string, string> = {};
  (globalThis as unknown as { document: unknown }).document = {
    documentElement: {
      dataset,
      style: {
        setProperty: (name: unknown, value: unknown) =>
          calls.push([String(name), String(value)]),
      },
    },
  };
  return { calls, dataset };
});

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");

describe("UF-53 域色 CSS 轴 app 层守卫（批6n+b1 三模）", () => {
  it("退役守卫：global.css 全文件零域色轴声明复入（#hex/rgb(/hsl(/color-mix( 四形态）+注入指针在场", () => {
    // 第二真源复入面：`: #hex`/`: rgb(`/`: hsl(`/`: color-mix(` 声明形态
    // （全文件口径——注释面不含「: 值开头」形态已核；inline 注入恒压
    // 样式表声明=复入即静默遮蔽，故守卫必须前置拦〔k1-W3 推演〕）
    const declarations =
      globalCss.match(
        /--wp-(?:water|sludge|mine|convey)\s*:\s*(?:#|rgb\(|hsl\(|color-mix\()/g,
      ) ?? [];
    expect(declarations).toEqual([]);
    // 指针在场：CSS 面须指向注入真源（防线文档化锚）
    expect(globalCss).toContain("installDomainColorAxis");
  });

  it("接线守卫：providers 装载期即 applyThemeMode——data-theme=light+light 档四键注入（hoisted stub 观测）", () => {
    // Providers 在场性（import 非死面）+装载期 setProperty 调用集恰
    // light 档四键（node 测试环境无 localStorage→readStoredThemeMode
    // 回退 light）；期望值自 domainCssVarsFor 派生（真源单点）
    expect(Providers).toBeTypeOf("function");
    const calls = wire.calls.map(([name, value]) => `${name}=${value}`).sort();
    const expected = Object.entries(domainCssVarsFor("light"))
      .map(([name, value]) => `${name}=${value}`)
      .sort();
    expect(calls).toEqual(expected);
    // data-theme 属性同步写入（无闪烁初始化机制锚——themeStore.applyThemeMode）
    expect(wire.dataset.theme).toBe("light");
  });
});
