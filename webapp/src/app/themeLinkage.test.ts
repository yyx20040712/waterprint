/**
 * GR-39 双源联动清单机检化守卫（2A5——A 线色值单源批）。
 *
 * 输入:  ./global.css 原文（node:fs 直读）+./providers themeConfig
 *        （静态 import——2A5 起导出；模块装载期求值，与
 *        domainColorAxis.test 先例同径）
 * 输出:  三守卫面——①:root 变量轴解析（--wp-* 声明抽取+hex 小写归一）；
 *        ②同值对断言全集（头注 A2-N-01 清单对+扩展对〔bodyBg/Tabs 四
 *        态色——providers 自注清单成员，头注未列〕：改任一侧不同步即
 *        红）；③清单↔测试互证（头注联动清单逐行锚在场——头注删行即红）。
 *
 * B4 亮色基线（2026-10-09 任务书 D8）：全部同值断言两侧亮值化；D1/D2
 *   表 deliberate 背离两对（bg-container/bg-deep）收窄或转值锚，G1-02
 *   鎏金对更新为 inkBar↔colorPrimary（AC 锚）——断言数不降、语义同强度
 *   （暗值断言→亮值断言=同步），逐条对账=批档 impl-report-b4.md。
 *
 * 形态说明（范式=domainColorAxis.test.ts：node:fs 读 CSS 原文+静态
 *   import JS 模块，node 直测零 jsdom）。antd 无槽位自持真源/设计字面量
 *   （--wp-scrollbar-hover/--wp-dot-color/--wp-gold-soft/渐变三停）不入
 *   对表——global.css 头注口径（A2-N-06/UF-53 批6n 注记节）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { themeConfig } from "./providers";

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");

/** 归一比较口径：trim+小写（hex 大小写漂移不计，值漂移计）。 */
function norm(value: string | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

/** :root 块内 --wp-* 声明抽取 → Map（值侧已归一——供同值对断言消费）。
 *  回炉 R1（d1-W1）：抽取前剥 /* *\/ 注释——防头注注释含「:root {」伪块
 *  劫持首匹配/注释内伪声明覆盖真值（方向=解析面加固，漏抽=假红非假绿）。 */
function parseRootVars(css: string): Map<string, string> {
  const noComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const block = noComments.match(/:root\s*\{([^}]*)\}/)?.[1] ?? "";
  const vars = new Map<string, string>();
  for (const m of block.matchAll(/(--wp-[\w-]+)\s*:\s*([^;]+);/g)) {
    const [, name, value] = m;
    if (name !== undefined && value !== undefined) {
      vars.set(name, norm(value));
    }
  }
  return vars;
}

const cssVars = parseRootVars(globalCss);

describe("GR-39 双源联动清单机检化（2A5）", () => {
  it(":root 解析：变量轴声明可抽取（解析面自证——锚键实值在场）", () => {
    // 防正则腐化前置拦：解析坏=同值对断言面全红的前置信号（锚值字面自证
    // ——B4 亮值锚〔D2 表〕）
    expect(cssVars.get("--wp-bg-page")).toBe("#f5f6f8");
    expect(cssVars.get("--wp-gold")).toBe("#8a6100");
    expect(cssVars.get("--wp-error")).toBe("#b3261e");
    // 回炉 R2（d1-W2）：成对键在场断言——双侧同步缺失（""=="" 静默绿）
    // 通道收口：CSS 侧键在场先立，则 token 侧缺配置必在值断言面红
    const pairedKeys = [
      "--wp-bg-page",
      "--wp-bg-container",
      "--wp-bg-elevated",
      "--wp-bg-deep",
      "--wp-border",
      "--wp-border-2",
      "--wp-text",
      "--wp-text-2",
      "--wp-text-3",
      "--wp-success",
      "--wp-error",
      "--wp-font-mono",
      "--wp-gold",
    ];
    for (const key of pairedKeys) {
      expect(cssVars.has(key), `轴键缺失：${key}`).toBe(true);
      // d1 复审 N1 补强：值非空——空白值+对侧同缺的 ""=="" 窄子案收口
      expect(norm(cssVars.get(key)), `轴键空白值：${key}`).not.toBe("");
    }
  });

  it("同值对·头注清单全集：--wp-* 轴 ↔ antd token（改任一侧不同步即红）", () => {
    expect(cssVars.get("--wp-bg-page")).toBe(
      norm(themeConfig.token?.colorBgLayout),
    );
    // B4（D1/D2 表背离收窄）：colorBgContainer 升 BG-2 白——轴键仍
    // BG-1 面板底，对行收窄为 siderBg 单侧；container token 侧改值锚
    expect(cssVars.get("--wp-bg-container")).toBe(
      norm(themeConfig.components?.Layout?.siderBg),
    );
    expect(themeConfig.token?.colorBgContainer).toBe("#ffffff");
    expect(cssVars.get("--wp-bg-container")).toBe("#fafbfc");
    expect(cssVars.get("--wp-bg-elevated")).toBe(
      norm(themeConfig.token?.colorBgElevated),
    );
    // B4（D1/D2 表背离）：headerBg 升页面底——--wp-bg-deep 轴自持键
    // （消费面=statusBar），token 侧无对行→值锚
    expect(cssVars.get("--wp-bg-deep")).toBe("#eceff3");
    expect(cssVars.get("--wp-border")).toBe(
      norm(themeConfig.token?.colorBorder),
    );
    expect(cssVars.get("--wp-border-2")).toBe(
      norm(themeConfig.token?.colorBorderSecondary),
    );
    expect(cssVars.get("--wp-text")).toBe(norm(themeConfig.token?.colorText));
    expect(cssVars.get("--wp-text-2")).toBe(
      norm(themeConfig.token?.colorTextSecondary),
    );
    expect(cssVars.get("--wp-text-3")).toBe(
      norm(themeConfig.token?.colorTextTertiary),
    );
    expect(cssVars.get("--wp-success")).toBe(
      norm(themeConfig.token?.colorSuccess),
    );
    expect(cssVars.get("--wp-error")).toBe(
      norm(themeConfig.token?.colorError),
    );
    // 字体串逐字同值（归一口径下字符级比对——mono 栈两侧漂移即红）
    expect(cssVars.get("--wp-font-mono")).toBe(
      norm(themeConfig.token?.fontFamilyCode),
    );
    // 鎏金：G1-02 B4 更新——墨条=AC 蓝（↔colorPrimary 同值锚），装饰金
    // 单源=global.css 轴（--wp-gold 与 inkBar 不再同值=任务书 D1 注记）
    expect(themeConfig.components?.Tabs?.inkBarColor).toBe(
      themeConfig.token?.colorPrimary,
    );
    expect(cssVars.get("--wp-gold")).toBe("#8a6100");
  });

  it("同值对·扩展对（A1）：bodyBg/Tabs 四态色——providers 自注清单成员（头注未列）", () => {
    // 同值事实入机检面=覆盖既有契约自述（providers components.Tabs 自注）
    // B4：itemSelectedColor=AC 锚（D1 表——与 colorPrimary 同值替代原
    // --wp-text 对行；未选/悬浮按压两态仍轴同值）
    expect(cssVars.get("--wp-bg-page")).toBe(
      norm(themeConfig.components?.Layout?.bodyBg),
    );
    expect(cssVars.get("--wp-text-2")).toBe(
      norm(themeConfig.components?.Tabs?.itemColor),
    );
    expect(cssVars.get("--wp-text")).toBe(
      norm(themeConfig.components?.Tabs?.itemHoverColor),
    );
    expect(cssVars.get("--wp-text")).toBe(
      norm(themeConfig.components?.Tabs?.itemActiveColor),
    );
    expect(themeConfig.components?.Tabs?.itemSelectedColor).toBe(
      themeConfig.token?.colorPrimary,
    );
  });

  it("清单↔测试互证：头注联动清单逐行锚在场（防清单腐化——删行即红）", () => {
    // global.css 头注 A2-N-01 清单行（逐字锚——含对齐空格）+error 扩行
    expect(globalCss).toContain(
      "--wp-bg-page   ↔ providers colorBgLayout",
    );
    expect(globalCss).toContain(
      "--wp-bg-container ↔ providers components.Layout.siderBg",
    );
    expect(globalCss).toContain(
      "--wp-bg-elevated ↔ providers colorBgElevated",
    );
    expect(globalCss).toContain(
      "--wp-bg-deep    ↔ 轴自持键",
    );
    expect(globalCss).toContain("--wp-border    ↔ providers colorBorder");
    expect(globalCss).toContain(
      "--wp-border-2  ↔ providers colorBorderSecondary",
    );
    expect(globalCss).toContain(
      "--wp-text/2/3  ↔ providers colorText/Secondary/Tertiary",
    );
    expect(globalCss).toContain(
      "--wp-success   ↔ providers colorSuccess",
    );
    expect(globalCss).toContain(
      "--wp-font-mono ↔ providers fontFamilyCode",
    );
    expect(globalCss).toContain(
      "A2-N-01 联动清单扩行：--wp-error ↔ providers colorError",
    );
    // D3 机检化注记锚（global.css 联动清单节尾注记行——删注记即红）
    expect(globalCss).toContain(
      "2A5 机检化：本清单同值对经 app/themeLinkage.test.ts 断言",
    );
  });
});
