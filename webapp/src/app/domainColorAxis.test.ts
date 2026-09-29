/**
 * 域色 CSS 轴 app 层守卫（批6n UF-53 双轴归一——门一回炉双席 W 处置）。
 *
 * 输入:  ./global.css 原文+./providers 模块（静态 import——装载期求值）+
 *        ../shared/ui/semanticColors DOMAIN_CSS_VARS（期望值真源）
 * 输出:  两守卫面——①global.css 域色声明退役守卫（#hex/rgb(/hsl(/
 *        color-mix( 四形态声明不得复入〔k1-W3/d1-W2 扩形态〕——全文件
 *        口径非仅 :root〔d1-N4〕）+注入指针在场；②providers 装载期接线
 *        行为级守卫（vi.hoisted 前置 stub document——先于 import 求值
 *        执行〔vitest 变换保证〕；providers 装载即 installDomainColorAxis
 *        逐键 setProperty——删调用/条件化/迁位即红〔k1-W1/d1-W4〕）。
 *
 * 形态说明（沿 instAsset.test.ts node:fs 先例+viewer3dPane.test.tsx
 *   vi.hoisted 先例——零 jsdom 红线；运行时动态 import 方案满载死锁
 *   弃用〔30s 时限两轮实证〕，静态 import 走常规导入相与其它 antd
 *   测试件同径）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { DOMAIN_CSS_VARS } from "../shared/ui/semanticColors";
import { Providers } from "./providers";

/** 装载期接线观测桩（vi.hoisted=先于上方 import 求值执行——stub 就位
 * 后 providers 模块装载即触发注入，setProperty 调用集落此）。 */
const wireCalls = vi.hoisted(() => {
  const calls: Array<[string, string]> = [];
  (globalThis as unknown as { document: unknown }).document = {
    documentElement: {
      style: {
        setProperty: (name: unknown, value: unknown) =>
          calls.push([String(name), String(value)]),
      },
    },
  };
  return calls;
});

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");

describe("UF-53 域色 CSS 轴 app 层守卫（批6n）", () => {
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

  it("接线守卫：providers 装载期即注入四键（hoisted stub 观测——删调用/条件化即红）", () => {
    // Providers 在场性（import 非死面）+装载期 setProperty 调用集恰四键
    expect(Providers).toBeTypeOf("function");
    const calls = wireCalls.map(([name, value]) => `${name}=${value}`).sort();
    // 期望值自 DOMAIN_CSS_VARS 派生（真源单点——与 shared 层键集冻结锚互证）
    const expected = Object.entries(DOMAIN_CSS_VARS)
      .map(([name, value]) => `${name}=${value}`)
      .sort();
    expect(calls).toEqual(expected);
  });
});
