/**
 * B4 亮色基线守卫（暗色残留=0 断言常设门——任务书 D6 判定集六面；
 * 纯 node 读源扫描：node:fs 读 webapp/src 原文+静态 import 真源模块，
 * domainColorAxis/themeLinkage 同径零 jsdom）。
 *
 * 输入:  webapp/src 全域源文（.ts/.tsx/.css）+./providers themeConfig+
 *        ../shared/ui/semanticColors DOMAIN_CSS_VARS/SEMANTIC_COLORS
 * 输出:  六判定面——①暗算法字面零命中（全域含测试）；②providers
 *        themeConfig 暗值清单（D1 表左列）零命中；③global.css :root
 *        15 色键亮值冻结+暗值零命中+规则体 D5 字面量零命中+全文件
 *        深底 hex（RGB 亮度<0.35，注释剥除）零命中；④内联暗值文件
 *        清单（D5 实测集+R-G3 派生面）逐文件零命中；⑤prefers-
 *        color-scheme 媒体查询零基线；⑥色板冻结锚（D1/D2/D3 亮值
 *        逐键+域色双轴同值+核心同值对）。
 *
 * 形态说明：判定集正则零命中+域色双轴同值+色板冻结锚——B6 收口批
 *   复扫引用同一件（残留回归常设门）。暗算法字面在断言侧以
 *   ["dark","Algorithm"].join("") 拼接构造（防本文件自匹配伪红）。
 * dxfScene ACI 1-7 色不在 ④ 判定集：DXF 预览底 #fafafa 亮面既成
 *   （DrawingPreview PREVIEW_BACKGROUND——ACI 深灰/纯色调色为亮底
 *   适配值非暗期残留；键值冻结=dxfScene.test 既有锚）。
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { theme } from "antd";

import { themeConfig } from "./providers";
import {
  DOMAIN_CSS_VARS,
  SEMANTIC_COLORS,
} from "../shared/ui/semanticColors";

const SRC_ROOT = join(__dirname, "..");
const readSrc = (rel: string): string =>
  readFileSync(join(SRC_ROOT, rel), "utf-8");

/** 收集 webapp/src 全域源文件相对路径（.ts/.tsx/.css——判定集扫描面）。 */
function collectSrcFiles(dir: string, prefix = ""): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const rel = prefix === "" ? name : `${prefix}/${name}`;
    const abs = join(dir, name);
    if (statSync(abs).isDirectory()) {
      out.push(...collectSrcFiles(abs, rel));
    } else if (/\.(tsx?|css)$/.test(name)) {
      out.push(rel);
    }
  }
  return out;
}
const srcFiles = collectSrcFiles(SRC_ROOT);

/** 行内注释剥除（//与块注释——lum 扫描与字面判定的注释甄别面；
 *  块注释跨行态按逐行前缀 * 粗剥=本仓注释书写惯例覆盖）。 */
function stripComments(text: string): string {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|\s)\/\/.*$/gm, "$1")
    .split(/\r?\n/)
    .filter((line) => !/^\s*\*/.test(line))
    .join("\n");
}

/** RGB 简单亮度（D6③ 判定口径：0.2126R+0.7152G+0.0722B 线性权和
 *  ——深底 hex=<0.35；与批档 scan-dark-b4.cjs 同式）。 */
function rgbLuminance(hex: string): number | null {
  const full =
    hex.length === 3
      ? hex
          .split("")
          .map((c) => c + c)
          .join("")
      : hex;
  if (full.length !== 6) return null;
  const r = parseInt(full.slice(0, 2), 16) / 255;
  const g = parseInt(full.slice(2, 4), 16) / 255;
  const b = parseInt(full.slice(4, 6), 16) / 255;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** :root 块内 --wp-* 声明抽取 → Map（themeLinkage.test 同式剥注释）。 */
function parseRootVars(css: string): Map<string, string> {
  const noComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const block = noComments.match(/:root\s*\{([^}]*)\}/)?.[1] ?? "";
  const vars = new Map<string, string>();
  for (const m of block.matchAll(/(--wp-[\w-]+)\s*:\s*([^;]+);/g)) {
    const [, name, value] = m;
    if (name !== undefined && value !== undefined) {
      vars.set(name, value.trim().toLowerCase());
    }
  }
  return vars;
}

const globalCss = readSrc("app/global.css");
const cssVars = parseRootVars(globalCss);

describe("B4 亮色基线·判定面①：暗算法字面零命中（全域含测试）", () => {
  // 口径注（R3）：源文件面=.ts/.tsx/.css（collectSrcFiles 收集域）——
  // .md 叙述面（README/批档）不在扫描域，叙述词不构成残留。
  it("src 全域零 dark+Algorithm 拼接串（拼接构造防本件自匹配）", () => {
    const needle = ["dark", "Algorithm"].join("");
    const hits = srcFiles.filter((rel) =>
      readSrc(rel).includes(needle),
    );
    expect(hits, `暗算法字面残留：${hits.join(", ")}`).toEqual([]);
  });
});

describe("判定面②：providers themeConfig 暗值清单（D1 表左列）零命中", () => {
  it("providers.tsx 全文（含注释）零 D1 左列暗值字面", () => {
    const providers = readSrc("app/providers.tsx");
    const darkLiterals = [
      "#3d8bfd", "#7ab2ff", "#0b1526", "#12213a", "#1a2d4d",
      "#243a5e", "#1b2c49", "#e8eef7", "#9db0c9", "#5d7290",
      "#3ddc97", "#f5b544", "#ff6b6b", "#0a1220", "#d9a94a",
      "#16263f", "#1c2f52", "rgba(130, 170, 246", "rgba(130,170,246",
    ];
    const hits = darkLiterals.filter((lit) => providers.includes(lit));
    expect(hits, `providers 暗值残留：${hits.join(", ")}`).toEqual([]);
  });
});

describe("判定面③：global.css :root 亮值冻结+暗值/深底 hex 零命中", () => {
  it(":root 15 色键=D2 亮值表（逐键冻结锚）", () => {
    const lightAxis: Record<string, string> = {
      "--wp-bg-page": "#f5f6f8",
      "--wp-bg-container": "#fafbfc",
      "--wp-bg-elevated": "#ffffff",
      "--wp-bg-deep": "#eceff3",
      "--wp-border": "#d6d9de",
      "--wp-border-2": "#e8eaed",
      "--wp-gold": "#8a6100",
      "--wp-gold-soft": "rgba(138, 97, 0, 0.32)",
      "--wp-text": "#1f2329",
      "--wp-text-2": "#646a73",
      "--wp-text-3": "#8a93a0",
      "--wp-success": "#2e7d32",
      "--wp-error": "#b3261e",
      "--wp-scrollbar-hover": "#c3c9d2",
      "--wp-dot-color": "#dfe3ea",
    };
    for (const [key, value] of Object.entries(lightAxis)) {
      expect(cssVars.get(key), `轴键 ${key} 非亮值`).toBe(value);
    }
  });

  it(":root 旧 15 暗值零复入+规则体 D5 字面量零命中", () => {
    const darkValues = [
      "#0b1526", "#12213a", "#1a2d4d", "#0a1220", "#243a5e",
      "#1b2c49", "#d9a94a", "#e8eef7", "#9db0c9", "#5d7290",
      "#3ddc97", "#ff6b6b", "#2f4d7d", "#1e3153",
      "rgba(217, 169, 74", "rgba(217,169,74",
    ];
    const d5RuleLiterals = [
      "#b98a35", "#f0cf8a", "rgba(77, 163, 255", "rgba(77,163,255",
    ];
    const hits = [...darkValues, ...d5RuleLiterals].filter((lit) =>
      globalCss.includes(lit),
    );
    expect(hits, `global.css 暗值/D5 残留：${hits.join(", ")}`).toEqual([]);
  });

  it("全文件深底 hex 零命中（背景族声明 RGB 亮度<0.35 判定——注释剥除后）", () => {
    // 甄别口径（D6③）：深底=background 族声明位的暗 hex（暗面板/暗底
    // 复辟面）；深字/深墨水值（--wp-text #1f2329、--wp-error、鎏金渐变
    // 停点等前景/墨色）=亮色正确形态非深底——不入判定（渐变停点=下行
    // D5 冻结锚另行机器断言）。
    const code = stripComments(globalCss);
    const darkHits: string[] = [];
    for (const m of code.matchAll(
      /background(?:-color)?\s*:\s*([^;]*#[0-9a-fA-F]{3,6}[^;]*);/g,
    )) {
      const decl = m[1] ?? "";
      if (decl.includes("gradient")) continue; // 渐变=墨色面（D5 冻结锚）
      for (const h of decl.matchAll(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g)) {
        const lum = rgbLuminance(h[1] ?? "");
        if (lum !== null && lum < 0.35) darkHits.push(`#${h[1]}`);
      }
    }
    expect(darkHits, `深底 hex 残留：${[...new Set(darkHits)].join(", ")}`).toEqual([]);
  });

  it("D5 规则体亮值冻结锚：鎏金渐变三停+定位光环双 rgba", () => {
    expect(globalCss).toContain("#a07300");
    expect(globalCss).toContain("#6d4e00");
    expect(globalCss).toContain("rgba(22, 119, 255, 0.55)");
    expect(globalCss).toContain("rgba(22, 119, 255, 0.28)");
  });
});

describe("判定面④：内联暗值文件清单逐文件零命中（D5 实测集+R-G3 派生面）", () => {
  it("各文件旧暗期字面量零残留（含注释——注释面同步改写）", () => {
    const inlineDark: Record<string, string[]> = {
      "app/themeLinkage.test.ts": ["#0b1526", "#d9a94a", "#ff6b6b"],
      "features/params/components/AssumptionsPanel.tsx": [
        "rgba(27, 44, 73", "rgba(27,44,73", "#8c8c8c",
      ],
      "features/params/components/ParamForm.tsx": [
        "rgba(27, 44, 73", "rgba(27,44,73",
        "rgba(61, 139, 253", "rgba(61,139,253", "#7ab2ff",
      ],
      "features/params/components/ParamTabs.tsx": [
        "rgba(61, 139, 253", "rgba(61,139,253", "#7ab2ff",
      ],
      "features/viewer3d/components/Scene.tsx": ["#0e2415", "#0b1526"],
      "features/viewer3d/components/ThumbnailStage.tsx": [
        "#0e2415", "#0b1526",
      ],
      "features/viewer3d/components/GroundStage.tsx": [
        "#1b2c49", "#2e5239", "#3d619c",
      ],
      "features/viewer3d/components/Annotations.tsx": [
        "#e8eef7", "#0a1220", "#1f1f1f",
      ],
      "features/solutions/lib/tornadoCharts.ts": [
        "#bfbfbf", "#d9d9d9", "#a3a3a3",
      ],
      "features/solutions/lib/jointCharts.ts": ["#bfbfbf"],
      "features/siteplan/lib/canvasDisplay.ts": ["#1f2933", "#2c2c2c"],
      "features/siteplan/components/SiteCanvas.tsx": ["#141414", "#c3ccd6"],
      "features/canvas/lib/unitGlyph.ts": [
        "rgba(77, 163, 255", "rgba(77,163,255", "#7ab2ff",
        "rgba(53, 201, 176", "rgba(53,201,176", "#52d8c2",
        "rgba(154, 168, 184", "rgba(154,168,184", "#b8c6d6", "#d4a273",
      ],
      // R1-mini 补强（主控预裁）：rgba 系扫描盲区两组+statusBar 换档面
      "features/canvas/components/UnitNode.tsx": [
        "rgba(217, 169, 74", "rgba(217,169,74", "#2c4568",
      ],
      "features/ai_chat/components/ChatPanel.tsx": ["#1c2540", "#141a2e"],
      "app/statusBar.tsx": ["var(--wp-text-3)"],
    };
    for (const [rel, literals] of Object.entries(inlineDark)) {
      const text = readSrc(rel);
      const hits = literals.filter((lit) => text.includes(lit));
      expect(hits, `${rel} 暗期字面残留：${hits.join(", ")}`).toEqual([]);
    }
  });

  it("R1 补强锚：UnitNode/ChatPanel/statusBar 现值冻结（rgba 盲区防复辟）", () => {
    // 主控预裁回炉（R1-mini 2026-10-09）：鎏金派生组新 rgb 基+气泡亮值
    // +状态条换档——现值冻结锚（复辟即红）
    const unitNode = readSrc("features/canvas/components/UnitNode.tsx");
    expect(unitNode).toContain("rgba(138, 97, 0, 0.75)");
    expect(unitNode).toContain("rgba(138,97,0,.35)");
    expect(unitNode).toContain("rgba(138,97,0,.14)");
    expect(unitNode).toContain("#6b7a8c");
    const chatPanel = readSrc("features/ai_chat/components/ChatPanel.tsx");
    expect(chatPanel).toContain("#eaf1fb");
    expect(chatPanel).toContain("#f0f2f5");
    expect(readSrc("app/statusBar.tsx")).toContain("var(--wp-text-2)");
  });

  it("R2 暗基 rgb 家族零命中（主控终裁视觉回炉——三族非测试源面零残留）", () => {
    // 家族=rgba 基 18,33,58 / 11,21,38 / 3,10,22（暗期深底调色基——
    // 豁免：App.tsx 品牌图形 rgba(29,95,208,·) 不在族内；rgba(0,0,0,·)
    // 纯黑软影非暗基调色）。needle 拼接构造防本件自匹配；扫描面=非测试
    // .ts/.tsx/.css（注释同计——历史注记须改写非存留）。
    const darkBases = [
      ["18", "33", "58"],
      ["11", "21", "38"],
      ["3", "10", "22"],
    ];
    const nonTestFiles = srcFiles.filter(
      (rel) => !/\.test\.(ts|tsx)$/.test(rel),
    );
    const hits: string[] = [];
    for (const base of darkBases) {
      for (const sep of [", ", ","]) {
        const needle = `rgba(${base.join(sep)}`;
        for (const rel of nonTestFiles) {
          if (readSrc(rel).includes(needle)) hits.push(`${rel}: ${needle}…`);
        }
      }
    }
    expect(hits, `暗基家族残留：${hits.join("; ")}`).toEqual([]);
  });

  it("R2 六修值点冻结锚（视觉验收残面处方值——复辟即红）", () => {
    const canvasFlow = readSrc("features/canvas/components/CanvasFlow.tsx");
    expect(canvasFlow).toContain("rgba(255,255,255,.92)"); // 图例条亮底
    expect(canvasFlow).toContain("rgba(31,35,41,.14)"); // Controls 亮影
    expect(canvasFlow).toContain("maskColor"); // MiniMap 显式亮罩
    expect(canvasFlow, "暗蓝晕影=已退役").not.toContain("radial-gradient");
    const unitNode = readSrc("features/canvas/components/UnitNode.tsx");
    expect(unitNode).toContain("rgba(31,35,41,.14)"); // 默认影亮化
    expect(unitNode).toContain("rgba(31,35,41,.18)"); // 菜单影+选中尾影
    const gate = readSrc(
      "features/viewer3d/components/FirstFrameGate.tsx",
    );
    expect(gate).toContain("rgba(245, 246, 248, 0.92)"); // 首帧遮罩亮底
    expect(gate).toContain("#646a73"); // 前景深字（fallback 同翻）
  });

  it("R3 锚：.wp-gold-edge 规则体零 hex/rgb 字面（全 var() 消费——:root 轴提升自动亮化，字面复辟即红）", () => {
    // 门二 W1 处置落档：鎏金收边=border-image 渐变停点 var(--wp-gold-soft)
    // ×2 全轴消费——B4 零改动面（主控亲证 2026-10-09 grep 现值）。
    const block = globalCss.match(/\.wp-gold-edge\s*\{([^}]*)\}/);
    expect(block, ".wp-gold-edge 规则块缺席").not.toBeNull();
    const body = block?.[1] ?? "";
    expect(body, "规则体 hex 字面复辟").not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(body, "规则体 rgb 字面复辟").not.toMatch(/rgba?\(/);
  });
});

describe("判定面⑤：系统配色偏好媒体查询零基线", () => {
  it("src 全域零该媒体查询面（无双主题查询——拼接构造防本件自匹配）", () => {
    const needle = ["prefers", "color", "scheme"].join("-");
    const hits = srcFiles.filter((rel) => readSrc(rel).includes(needle));
    expect(hits, `媒体查询残留：${hits.join(", ")}`).toEqual([]);
  });
});

describe("判定面⑥：色板冻结锚（D1/D3 亮值+域色双轴同值+核心同值对）", () => {
  it("themeConfig=D1 亮值表（algorithm+seed+components 逐键）+密度冻结值", () => {
    expect(themeConfig.algorithm).toBe(theme.defaultAlgorithm);
    const t = themeConfig.token ?? {};
    expect(t.colorPrimary).toBe("#1677ff");
    expect(t.colorInfo).toBe("#1677ff");
    expect(t.colorLink).toBe("#1677ff");
    expect(t.colorBgLayout).toBe("#f5f6f8");
    expect(t.colorBgContainer).toBe("#ffffff");
    expect(t.colorBgElevated).toBe("#ffffff");
    expect(t.colorBorder).toBe("#d6d9de");
    expect(t.colorBorderSecondary).toBe("#e8eaed");
    expect(t.colorText).toBe("#1f2329");
    expect(t.colorTextSecondary).toBe("#646a73");
    expect(t.colorTextTertiary).toBe("#8a93a0");
    expect(t.colorSuccess).toBe("#2e7d32");
    expect(t.colorWarning).toBe("#8a6100");
    expect(t.colorError).toBe("#b3261e");
    const layout = themeConfig.components?.Layout ?? {};
    expect(layout.headerBg).toBe("#f5f6f8");
    expect(layout.siderBg).toBe("#fafbfc");
    expect(layout.bodyBg).toBe("#f5f6f8");
    const tabs = themeConfig.components?.Tabs ?? {};
    expect(tabs.inkBarColor).toBe("#1677ff");
    expect(tabs.itemColor).toBe("#646a73");
    expect(tabs.itemHoverColor).toBe("#1f2329");
    expect(tabs.itemActiveColor).toBe("#1f2329");
    expect(tabs.itemSelectedColor).toBe("#1677ff");
    const table = themeConfig.components?.Table ?? {};
    expect(table.headerBg).toBe("#f0f2f5");
    expect(table.rowHoverBg).toBe("#f0f2f5");
    expect(table.colorSplit).toBe("#e8eaed");
    // M1 密度冻结值（B4 仅换色不换密度——任务书 D1 引言）
    expect(t.borderRadius).toBe(6);
    expect(t.controlHeight).toBe(28);
    expect(t.fontSize).toBe(13);
  });

  it("域色双轴同值：DOMAIN_CSS_VARS=D3 亮值表且===domain_* 键", () => {
    const lightDomains: Record<string, string> = {
      "--wp-water": "#1677ff",
      "--wp-sludge": "#9c6b45",
      "--wp-mine": "#0e9e88",
      "--wp-convey": "#6b7a8c",
    };
    for (const [key, value] of Object.entries(lightDomains)) {
      expect(DOMAIN_CSS_VARS[key as keyof typeof DOMAIN_CSS_VARS]).toBe(value);
    }
    expect(DOMAIN_CSS_VARS["--wp-water"]).toBe(SEMANTIC_COLORS.domain_water);
    expect(DOMAIN_CSS_VARS["--wp-sludge"]).toBe(SEMANTIC_COLORS.domain_sludge);
    expect(DOMAIN_CSS_VARS["--wp-mine"]).toBe(SEMANTIC_COLORS.domain_mine);
    expect(DOMAIN_CSS_VARS["--wp-convey"]).toBe(SEMANTIC_COLORS.domain_convey);
    // 管廊派生跟随（D3：pipe_* 随域色单源）
    expect(SEMANTIC_COLORS.pipe_water).toBe(DOMAIN_CSS_VARS["--wp-water"]);
    expect(SEMANTIC_COLORS.pipe_sludge).toBe(
      DOMAIN_CSS_VARS["--wp-sludge"],
    );
    expect(SEMANTIC_COLORS.domain_neutral).toBe("#595959");
  });

  it("核心同值对（CSS 轴↔antd token——themeLinkage 双源契约的锚集）", () => {
    const t = themeConfig.token ?? {};
    expect(cssVars.get("--wp-bg-page")).toBe(t.colorBgLayout);
    expect(cssVars.get("--wp-bg-elevated")).toBe(t.colorBgElevated);
    expect(cssVars.get("--wp-bg-container")).toBe(
      themeConfig.components?.Layout?.siderBg,
    );
    expect(cssVars.get("--wp-border")).toBe(t.colorBorder);
    expect(cssVars.get("--wp-text")).toBe(t.colorText);
    expect(cssVars.get("--wp-success")).toBe(t.colorSuccess);
    expect(cssVars.get("--wp-error")).toBe(t.colorError);
  });
});
