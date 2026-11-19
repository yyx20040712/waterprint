/**
 * 三主题基线守卫（b1 主题地基批 2026-11-19 重定位——原 B4 亮色基线
 * 常设门随三主题体系扩面：light 默认基线+按模值域冻结+退役色零复入。
 * 纯 node 读源扫描：node:fs 读 webapp/src 原文+静态 import 真源模块，
 * domainColorAxis/themeLinkage 同径零 jsdom）。
 *
 * 输入:  webapp/src 全域源文（.ts/.tsx/.css）+./themeModes 两配置构建器
 *        +MODE_COLORS+../shared/ui/semanticColors 域色三模记录
 * 输出:  六判定面——①暗算法字面收容（暗算法拼接字面仅三主题定义面
 *        〔themeModes.ts+其测试〕可持有，余域零命中）；②退役色板
 *        （C1 暗期+B4 亮期）零复入（三主题定义面两文件）；③global.css
 *        三主题块轴自持键逐模冻结（gold/gold-soft 恒值+scrollbar-hover
 *        派生三值+soft/canvas/shadow===MODE_COLORS）+规则体深底 hex 零
 *        命中+全 src v4 旧轴键零残留（b1 并轴改名完备性）；④内联
 *        暗值文件清单逐文件零命中（D5 实测集）+R2/R3 锚；⑤prefers-
 *        color-scheme 媒体查询零基线（手动切换制）；⑥域色三模冻结
 *        （domainCssVarsFor 逐模===DOMAIN_COLORS+设计稿值）。
 *
 * 形态说明：判定集正则零命中+冻结锚——暗算法字面在断言侧以
 *   ["dark","Algorithm"].join("") 拼接构造（防本文件自匹配伪红）。
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { THEME_MODES, type ThemeMode } from "../shared/store/themeStore";
import {
  DOMAIN_COLORS,
  domainCssVarsFor,
} from "../shared/ui/semanticColors";
import { MODE_COLORS } from "./themeModes";

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

/** 行内注释剥除（//与块注释——lum 扫描与字面判定的注释甄别面）。 */
function stripComments(text: string): string {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|\s)\/\/.*$/gm, "$1")
    .split(/\r?\n/)
    .filter((line) => !/^\s*\*/.test(line))
    .join("\n");
}

/** RGB 简单亮度（深底 hex=<0.35——D6③ 判定口径沿承）。 */
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

/** 指定主题块内 --wp-* 声明抽取 → Map（themeLinkage.test 同式）。 */
function parseThemeVars(css: string, mode: ThemeMode): Map<string, string> {
  const noComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const selector =
    mode === "light" ? ":root" : `html[data-theme="${mode}"]`;
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const block =
    noComments.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`))?.[1] ?? "";
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
const cssVars: Record<ThemeMode, Map<string, string>> = {
  light: parseThemeVars(globalCss, "light"),
  warm: parseThemeVars(globalCss, "warm"),
  dark: parseThemeVars(globalCss, "dark"),
};

/** 三主题定义面（暗算法/全量色板字面唯一合法居所）。 */
const THEME_DEF_FILES = new Set(["app/themeModes.ts", "app/themeModes.test.ts"]);

describe("三主题基线·判定面①：暗算法字面收容", () => {
  it("src 全域零 dark+Algorithm 拼接串（拼接构造防本件自匹配；三主题定义面豁免）", () => {
    const needle = ["dark", "Algorithm"].join("");
    const hits = srcFiles.filter(
      (rel) => !THEME_DEF_FILES.has(rel) && readSrc(rel).includes(needle),
    );
    expect(hits, `暗算法字面越界：${hits.join(", ")}`).toEqual([]);
    // 定义面在场自证（收容≠缺失——暗算法必须在 themeModes 使用）
    expect(readSrc("app/themeModes.ts").includes(needle)).toBe(true);
  });
});

describe("判定面②：退役色板（C1 暗期+B4 亮期）零复入（三主题定义面）", () => {
  it("themeModes.ts+providers.tsx 零退役色板字面", () => {
    // C1 暗期值+B4 亮期值（三主题稿值整体替换退役——复入=漂移）
    const retiredLiterals = [
      // C1 暗期（方向 A）
      "#3d8bfd", "#7ab2ff", "#0b1526", "#12213a", "#1a2d4d",
      "#243a5e", "#1b2c49", "#e8eef7", "#9db0c9", "#5d7290",
      "#3ddc97", "#f5b544", "#ff6b6b", "#0a1220", "#d9a94a",
      "#16263f", "#1c2f52", "rgba(130, 170, 246", "rgba(130,170,246",
      // B4 亮期（工程蓝 AC+分层白——稿青绿操作色整体替换）
      "#1677ff", "#f5f6f8", "#fafbfc", "#eceff3", "#f0f2f5",
      "#d6d9de", "#e8eaed", "#1f2329", "#646a73", "#8a93a0",
      "#2e7d32", "#8a6100", "#b3261e",
    ];
    for (const rel of ["app/themeModes.ts", "app/providers.tsx"]) {
      const hits = retiredLiterals.filter((lit) => readSrc(rel).includes(lit));
      expect(hits, `${rel} 退役色板残留：${hits.join(", ")}`).toEqual([]);
    }
  });
});

describe("判定面③：global.css 轴自持键逐模冻结+深底/旧轴键零命中", () => {
  it("轴自持键逐模：gold 恒值+scrollbar-hover 派生三值+soft/canvas/shadow===MODE_COLORS", () => {
    for (const mode of THEME_MODES) {
      const vars = cssVars[mode];
      const c = MODE_COLORS[mode];
      // gold 族：稿无鎏金（开放问题 5 裁决前恒值——装饰金面单源=本轴）
      expect(vars.get("--wp-gold"), `${mode} gold`).toBe("#8a6100");
      expect(vars.get("--wp-gold-soft"), `${mode} gold-soft`).toBe(
        "rgba(138, 97, 0, 0.32)",
      );
      // scrollbar-hover：稿无此键=border 档派生（亮/暖深一档、暗浅一档）
      const scrollbarHover = {
        light: "#c3c9d2",
        warm: "#beb49e",
        dark: "#4a5751",
      } as const;
      expect(vars.get("--wp-scrollbar-hover"), `${mode} scrollbar-hover`).toBe(
        scrollbarHover[mode],
      );
      // 稿自持键（无 antd 槽位）与 JS 色板记录同值
      expect(vars.get("--wp-accent-soft"), `${mode} accent-soft`).toBe(
        c.accentSoft.toLowerCase(),
      );
      expect(vars.get("--wp-success-soft"), `${mode} success-soft`).toBe(
        c.successSoft.toLowerCase(),
      );
      expect(vars.get("--wp-warning-soft"), `${mode} warning-soft`).toBe(
        c.warningSoft.toLowerCase(),
      );
      expect(vars.get("--wp-error-soft"), `${mode} error-soft`).toBe(
        c.errorSoft.toLowerCase(),
      );
      expect(vars.get("--wp-canvas"), `${mode} canvas`).toBe(
        c.canvas.toLowerCase(),
      );
      expect(vars.get("--wp-shadow"), `${mode} shadow`).toBe(
        c.shadow.toLowerCase(),
      );
    }
  });

  it("全文件深底 hex 零命中（规则体 background 族声明——注释剥除后；主题块为自定义属性非 background 声明不入判定）", () => {
    const code = stripComments(globalCss);
    const darkHits: string[] = [];
    for (const m of code.matchAll(
      /background(?:-color)?\s*:\s*([^;]*#[0-9a-fA-F]{3,6}[^;]*);/g,
    )) {
      const decl = m[1] ?? "";
      if (decl.includes("gradient")) continue;
      for (const h of decl.matchAll(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g)) {
        const lum = rgbLuminance(h[1] ?? "");
        if (lum !== null && lum < 0.35) darkHits.push(`#${h[1]}`);
      }
    }
    expect(darkHits, `深底 hex 残留：${[...new Set(darkHits)].join(", ")}`).toEqual([]);
  });

  it("全 src v4 旧轴键零残留（b1 并轴改名完备性——六键并入 --wp-* 轴；拼接构造防本件自匹配）", () => {
    const needle = ["--wpv", "4-"].join("");
    const hits = srcFiles.filter((rel) => readSrc(rel).includes(needle));
    expect(hits, `旧轴键残留：${hits.join(", ")}`).toEqual([]);
  });
});

describe("判定面④：内联暗值文件清单逐文件零命中（D5 实测集+R-G3 派生面）", () => {
  it("各文件旧暗期字面量零残留（含注释——注释面同步改写）", () => {
    const inlineDark: Record<string, string[]> = {
      "features/params/components/AssumptionsPanel.tsx": [
        "rgba(27, 44, 73", "rgba(27,44,73", "#8c8c8c",
      ],
      "features/params/components/ParamForm.tsx": [
        "rgba(27, 44, 73", "rgba(27,44,73",
        "rgba(61, 139, 253", "rgba(61,139,253", "#7ab2ff",
      ],
      "features/viewer3d/components/Scene.tsx": ["#0e2415", "#0b1526"],
      "features/viewer3d/components/GroundStage.tsx": [
        "#1b2c49", "#2e5239", "#3d619c",
      ],
      "features/viewer3d/components/Annotations.tsx": [
        "#e8eef7", "#0a1220", "#1f1f1f",
      ],
      "features/solutions/lib/jointCharts.ts": ["#bfbfbf"],
      "features/siteplan/lib/canvasDisplay.ts": ["#1f2933", "#2c2c2c"],
      "features/siteplan/components/SiteCanvas.tsx": ["#141414", "#c3ccd6"],
      "features/canvas/lib/unitGlyph.ts": [
        "rgba(77, 163, 255", "rgba(77,163,255", "#7ab2ff",
        "rgba(53, 201, 176", "rgba(53,201,176", "#52d8c2",
        "rgba(154, 168, 184", "rgba(154,168,184", "#b8c6d6", "#d4a273",
      ],
    };
    for (const [rel, literals] of Object.entries(inlineDark)) {
      const text = readSrc(rel);
      const hits = literals.filter((lit) => text.includes(lit));
      expect(hits, `${rel} 暗期字面残留：${hits.join(", ")}`).toEqual([]);
    }
  });

  it("R2 暗基 rgb 家族零命中（三族非测试源面零残留）", () => {
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

  it("R2 值点冻结锚（视觉验收残面处方值——v1 转正批收缩至在位件）", () => {
    const gate = readSrc(
      "features/viewer3d/components/FirstFrameGate.tsx",
    );
    expect(gate).toContain("rgba(245, 246, 248, 0.92)"); // 首帧遮罩亮底
    expect(gate).toContain("#646a73"); // 前景深字（fallback 同翻）
  });

  it("R3 锚：.wp-gold-edge/.wp-lib-hit/.wp-dotgrid/.wp-scroll-tabs 段零复入", () => {
    for (const legacyClass of ["wp-gold-edge", "wp-lib-hit", "wp-dotgrid"]) {
      expect(
        globalCss.includes(legacyClass),
        `${legacyClass} 段复辟`,
      ).toBe(false);
    }
    expect(globalCss.includes("wp-scroll-tabs"), "wp-scroll-tabs 段复辟").toBe(false);
  });
});

describe("判定面⑤：系统配色偏好媒体查询零基线", () => {
  it("src 全域零该媒体查询面（手动三态制——拼接构造防本件自匹配）", () => {
    const needle = ["prefers", "color", "scheme"].join("-");
    const hits = srcFiles.filter((rel) => readSrc(rel).includes(needle));
    expect(hits, `媒体查询残留：${hits.join(", ")}`).toEqual([]);
  });
});

describe("判定面⑥：域色三模冻结（b1——稿域色三态入 DOMAIN_COLORS）", () => {
  it("domainCssVarsFor 逐模===DOMAIN_COLORS 且=设计稿域色三态字面", () => {
    const draftDomains = {
      light: { water: "#286b86", sludge: "#7d573e", mine: "#3f7d6a", convey: "#64788a" },
      warm: { water: "#456a72", sludge: "#765239", mine: "#65775c", convey: "#77766e" },
      dark: { water: "#78acc0", sludge: "#c09a78", mine: "#83b49c", convey: "#9aabb9" },
    } as const;
    for (const mode of THEME_MODES) {
      const vars = domainCssVarsFor(mode);
      expect(Object.keys(vars).sort()).toEqual(
        ["--wp-convey", "--wp-mine", "--wp-sludge", "--wp-water"].sort(),
      );
      for (const [key, value] of Object.entries(draftDomains[mode])) {
        expect(vars[`--wp-${key}` as keyof typeof vars], `${mode} ${key}`).toBe(
          value,
        );
        expect(
          DOMAIN_COLORS[mode][key as keyof (typeof DOMAIN_COLORS)["light"]],
          `${mode} DOMAIN_COLORS.${key}`,
        ).toBe(value);
      }
    }
    // neutral 三模恒值（稿无中性键——回退灰沿承）
    for (const mode of THEME_MODES) {
      expect(DOMAIN_COLORS[mode].neutral).toBe("#595959");
    }
  });
});
