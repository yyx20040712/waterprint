/**
 * semanticColors 真源表测试：键集冻结+逐键值+兜底+三导出（SC1 D3）。
 *
 * 输入:  semanticColors.ts 三导出（SEMANTIC_COLORS/FALLBACK_COLOR/
 *        semanticColor）+批6n 注入导出（installDomainColorAxis）+b1 三模
 *        域色导出（DOMAIN_COLORS/domainCssVarsFor）
 * 输出:  五断言面（34 键字面清单 toEqual+逐键值 toBe+兜底回退+导出
 *        存在性+UF-53 双轴归一值面组〔b1 三模扩面：CSS 轴四键键集逐模/
 *        双轴同值逐键===domain_* 键/注入契约 stub document 按模/缺席
 *        守卫〕——CSS 侧文件面守卫〔退役+接线〕在 app 层
 *        domainColorAxis.test〔同层读 global.css/providers.tsx——门一
 *        回炉 d1-W5 反向耦合处置〕；美感抛光批 #10 增三维材质键按模
 *        取值面〔MATERIAL_COLORS 四键三模〕）
 *
 * 键集 34 键（SC1 迁移 24 键全数原值零漂移+SPC2 boundary_error+B3-b
 * domain_* 五键〔同值搬家——unitGlyph/LEGEND_LINES 收编〕）——
 * 本测试即键集冻结锚：任何增删键/改值必须同步本文件字面清单（键集
 * 反推法同款纪律）。批6n（UF-53 双轴归一）：值面冻结锚扩 CSS 轴——
 * 注入轴四键与 domain_* 键机器断言同值（CSS 侧漂移防线=
 * 值面+global.css 声明面守卫〔app 层 domainColorAxis.test〕；全仓任意
 * 形态域色复现扫描=欠账，见登记册 UF-53 行）。
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DOMAIN_COLORS,
  FALLBACK_COLOR,
  MATERIAL_COLORS,
  SEMANTIC_COLORS,
  domainCssVarsFor,
  installDomainColorAxis,
  semanticColor,
} from "./semanticColors";

describe("semanticColors 语义色真源表", () => {
  it("键集冻结：恰 34 键（3D 图元 12+2D 场面 7+2D 单点 6+管廊 2[C2-3d]+剖切帽盖 1[C2VD]+检修占位 1[S11]+域色 5[B3-b]）", () => {
    expect(Object.keys(SEMANTIC_COLORS).sort()).toEqual(
      [
        // 3D 图元色族（12）
        "pool_wall", "partition", "channel", "ground",
        "water_surface", "sludge", "aerator", "paddle",
        "media", "gate", "pipe", "decant",
        // C2-3d 管廊两色制（2——与画布域色轴同值）
        "pipe_water", "pipe_sludge",
        // C2VD V1 剖切帽盖（1——缩略图半剖剖面封盖灰）
        "section_cap",
        // 2D 场景色族（7）
        "road", "boundary",
        "corridor_water", "corridor_power", "corridor_gas",
        "corridor_comm", "corridor_fallback",
        // 2D 单点彩色语义族（6——SPC2 +boundary_error 红线越界）
        "selected", "pending", "measure", "spacing_warn", "spacing_error",
        "boundary_error",
        // S11 检修缺位占位（1——viewer3d 警示面）
        "maintenance",
        // B3-b 四域色+中性 JS 面（5——unitGlyph/stream 色/图例线色收编）
        "domain_water", "domain_sludge", "domain_mine", "domain_convey",
        "domain_neutral",
      ].sort(),
    );
  });

  it("逐键值冻结：字面 hex 逐键锚（B4 亮底重定值后值面——3D/2D 图元族保持原值）", () => {
    expect(SEMANTIC_COLORS.pool_wall).toBe("#a3a9ad"); // 批3 首族视觉验收迭代调灰
    expect(SEMANTIC_COLORS.partition).toBe("#8f9599");
    expect(SEMANTIC_COLORS.channel).toBe("#7f8a93");
    expect(SEMANTIC_COLORS.ground).toBe("#cfd6dc");
    expect(SEMANTIC_COLORS.water_surface).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.sludge).toBe("#8c5a2b");
    expect(SEMANTIC_COLORS.aerator).toBe("#d48806");
    expect(SEMANTIC_COLORS.paddle).toBe("#d48806");
    expect(SEMANTIC_COLORS.media).toBe("#6a7f5a");
    expect(SEMANTIC_COLORS.gate).toBe("#5b8db8");
    expect(SEMANTIC_COLORS.pipe).toBe("#5b8db8");
    expect(SEMANTIC_COLORS.decant).toBe("#5b8db8");
    // C2-3d 管廊：水/泥域色（--wp-water/--wp-sludge 轴同值——domain_* 单源引用）
    expect(SEMANTIC_COLORS.pipe_water).toBe("#286b86");
    expect(SEMANTIC_COLORS.pipe_sludge).toBe("#7d573e");
    // B3-b 四域色+中性（JS 面单源——unitGlyph/domainColorOf 与 streamColorOf
    // 及 CanvasFlow LEGEND_LINES 同值搬家；global.css --wp-* 轴同步义务=
    // UF-53。b1 主题地基批：值换为已批准设计稿亮档域色〔JS 面冻结
    // light 档——SVG/Canvas 消费面三态随画布重涂批〕）
    expect(SEMANTIC_COLORS.domain_water).toBe("#286b86");
    expect(SEMANTIC_COLORS.domain_sludge).toBe("#7d573e");
    expect(SEMANTIC_COLORS.domain_mine).toBe("#3f7d6a");
    expect(SEMANTIC_COLORS.domain_convey).toBe("#64788a");
    expect(SEMANTIC_COLORS.domain_neutral).toBe("#595959");
    // 管廊键与域色键同值单源（DOMAIN_COLORS 引用——漂移即红）
    expect(SEMANTIC_COLORS.pipe_water).toBe(SEMANTIC_COLORS.domain_water);
    expect(SEMANTIC_COLORS.pipe_sludge).toBe(SEMANTIC_COLORS.domain_sludge);
    // C2VD V1 剖切帽盖：pool_wall 与 ground 之间档剖面灰
    expect(SEMANTIC_COLORS.section_cap).toBe("#a8b4c2");
    expect(SEMANTIC_COLORS.road).toBe("#6b6f76");
    expect(SEMANTIC_COLORS.boundary).toBe("#d4380d");
    expect(SEMANTIC_COLORS.corridor_water).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.corridor_power).toBe("#f2a93b");
    expect(SEMANTIC_COLORS.corridor_gas).toBe("#3fa34d");
    expect(SEMANTIC_COLORS.corridor_comm).toBe("#9a6dd7");
    expect(SEMANTIC_COLORS.corridor_fallback).toBe("#8c8c8c");
    expect(SEMANTIC_COLORS.selected).toBe("#1668dc");
    // B4 亮底复核（D4）：pending 文本级消费面→#8a6100；spacing_warn/
    // maintenance 图形级→#ad6800/#d46b08（白底对比度实录=批档
    // contrast-b4.txt；暗值断言→亮值断言=同步，语义不弱化）
    expect(SEMANTIC_COLORS.pending).toBe("#8a6100");
    expect(SEMANTIC_COLORS.measure).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.spacing_warn).toBe("#ad6800");
    expect(SEMANTIC_COLORS.spacing_error).toBe("#ff4d4f");
    expect(SEMANTIC_COLORS.boundary_error).toBe("#fa541c");
    // S11 检修缺位占位警示橙（B4 亮底重定值档）
    expect(SEMANTIC_COLORS.maintenance).toBe("#d46b08");
  });

  it("兜底：未登记语义回退 FALLBACK_COLOR（禁抛错打断渲染）", () => {
    expect(semanticColor("__nope__")).toBe(FALLBACK_COLOR);
  });

  it("域派生键按模取值（b4 三态收口——installDomainColorAxis 记录当前模后 semanticColor 读 DOMAIN_COLORS 对应档；静态表=light 参照锚不动）", () => {
    // 基线=light（模块缺省模）
    expect(semanticColor("pipe_water")).toBe(DOMAIN_COLORS.light.water);
    expect(semanticColor("pipe_sludge")).toBe(DOMAIN_COLORS.light.sludge);
    expect(semanticColor("domain_neutral")).toBe(DOMAIN_COLORS.light.neutral);
    // 切 dark（document 缺席的 node 面=只记录模不注入 CSS——JS 面语义仍生效）
    installDomainColorAxis("dark");
    expect(semanticColor("pipe_water")).toBe(DOMAIN_COLORS.dark.water);
    expect(semanticColor("pipe_sludge")).toBe(DOMAIN_COLORS.dark.sludge);
    expect(semanticColor("domain_mine")).toBe(DOMAIN_COLORS.dark.mine);
    // 切 warm 后回落；非派生键不受模影响
    installDomainColorAxis("warm");
    expect(semanticColor("pipe_water")).toBe(DOMAIN_COLORS.warm.water);
    expect(semanticColor("water_surface")).toBe(SEMANTIC_COLORS.water_surface);
    // 复位 light（后续用例基线稳定）
    installDomainColorAxis("light");
    expect(semanticColor("pipe_water")).toBe(DOMAIN_COLORS.light.water);
  });

  it("三维材质键按模取值（美感抛光批 #10——pool_wall/partition/channel/ground 查 MATERIAL_COLORS 对应档；light 档=静态表同值像素零漂移锚）", () => {
    // 基线=light：派生值与静态表（light 参照锚）同值
    for (const key of ["pool_wall", "partition", "channel", "ground"] as const) {
      expect(semanticColor(key)).toBe(SEMANTIC_COLORS[key]);
      expect(semanticColor(key)).toBe(MATERIAL_COLORS.light[key]);
    }
    installDomainColorAxis("dark");
    expect(semanticColor("pool_wall")).toBe(MATERIAL_COLORS.dark.pool_wall);
    expect(semanticColor("partition")).toBe(MATERIAL_COLORS.dark.partition);
    expect(semanticColor("channel")).toBe(MATERIAL_COLORS.dark.channel);
    expect(semanticColor("ground")).toBe(MATERIAL_COLORS.dark.ground);
    installDomainColorAxis("warm");
    expect(semanticColor("pool_wall")).toBe(MATERIAL_COLORS.warm.pool_wall);
    expect(semanticColor("ground")).toBe(MATERIAL_COLORS.warm.ground);
    // 复位 light（后续用例基线稳定）
    installDomainColorAxis("light");
    expect(semanticColor("pool_wall")).toBe(MATERIAL_COLORS.light.pool_wall);
  });

  it("三导出存在性：SEMANTIC_COLORS/semanticColor/FALLBACK_COLOR", () => {
    expect(typeof SEMANTIC_COLORS).toBe("object");
    expect(semanticColor).toBeTypeOf("function");
    expect(FALLBACK_COLOR).toBeTypeOf("string");
  });
});

describe("UF-53 域色双轴归一（批6n：CSS 轴注入契约——b1 三模扩面）", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("CSS 轴键集冻结：domainCssVarsFor 逐模恰 --wp- 四键（water/sludge/mine/convey——实际 CSS 消费面；neutral 零 var() 消费方不入轴〔A2-N-06〕）", () => {
    for (const mode of ["light", "warm", "dark"] as const) {
      expect(Object.keys(domainCssVarsFor(mode)).sort()).toEqual(
        ["--wp-convey", "--wp-mine", "--wp-sludge", "--wp-water"].sort(),
      );
    }
  });

  it("双轴同值机器断言：CSS 轴 light 档逐键===domain_* 键（JS 面冻结 light 档——漂移即红）", () => {
    // 期望值不引 DOMAIN_COLORS 字面（防自证）——对冻结的 34 键表逐键横断
    // （b1：亮档值=设计稿域色）
    const light = domainCssVarsFor("light");
    expect(light["--wp-water"]).toBe(SEMANTIC_COLORS.domain_water);
    expect(light["--wp-water"]).toBe("#286b86");
    expect(light["--wp-sludge"]).toBe(SEMANTIC_COLORS.domain_sludge);
    expect(light["--wp-sludge"]).toBe("#7d573e");
    expect(light["--wp-mine"]).toBe(SEMANTIC_COLORS.domain_mine);
    expect(light["--wp-mine"]).toBe("#3f7d6a");
    expect(light["--wp-convey"]).toBe(SEMANTIC_COLORS.domain_convey);
    expect(light["--wp-convey"]).toBe("#64788a");
  });

  it("注入契约：documentElement.style 逐键 setProperty（stub document——按模注入）", () => {
    const setProperty = vi.fn();
    vi.stubGlobal("document", {
      documentElement: { style: { setProperty } },
    });
    installDomainColorAxis("dark");
    const calls = setProperty.mock.calls
      .map(([name, value]) => `${String(name)}=${String(value)}`)
      .sort();
    expect(calls).toEqual(
      [
        "--wp-water=#78acc0",
        "--wp-sludge=#c09a78",
        "--wp-mine=#83b49c",
        "--wp-convey=#9aabb9",
      ].sort(),
    );
    // 缺省参=light 档（向后兼容面——providers 装载期无模调用守卫）
    setProperty.mockClear();
    installDomainColorAxis();
    expect(setProperty.mock.calls.map(([n]) => String(n)).sort()).toEqual(
      ["--wp-convey", "--wp-mine", "--wp-sludge", "--wp-water"].sort(),
    );
  });

  it("document 缺席守卫：no-op 不抛错（SSR/纯 node 测试环境）", () => {
    vi.stubGlobal("document", undefined);
    expect(() => installDomainColorAxis("warm")).not.toThrow();
  });
});
