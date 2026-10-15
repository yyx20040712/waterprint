/**
 * R3F Canvas 铺满容器源锚测试（V4 P7——uiglobal B-空带：calc(100vh-220px)
 * 公式制遗留=画布底缘距状态栏恒空带；容器填充制改造的源结构锚面——Canvas
 * 真渲染需 WebGL，jsdom 不承载〔FirstFrameGate.dom 先例——不渲染 Canvas
 * 面〕，锚=?raw 源断言）。
 *
 * 输入:  Scene.tsx 源文（?raw）+viewer3dZone.tsx 源文（?raw——外层 flex
 *        链的 zone 侧半）
 * 输出:  断言族：①canvas 高=容器填充 height:"100%"（公式制 calc(100vh
 *        退役）②CANVAS_MIN_HEIGHT 保底仍在（minHeight 消费锚）③画布
 *        容器 relative div=flex:1+minHeight:0（链中段）④zone 包裹
 *        div=display:flex/flexDirection:column（链首——Fragment 扁平子
 *        的弹性父）
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const sceneSource = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "Scene.tsx"),
  "utf-8",
);
const zoneSource = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../../../app/shellV4/viewer3dZone.tsx"),
  "utf-8",
);

describe("viewer3d·V4 画布铺满容器（P7——公式制→容器填充制）", () => {
  it("canvas 高=height:\"100%\"（calc(100vh 公式退役——空带根因）", () => {
    expect(sceneSource).toContain('height: "100%"');
    expect(sceneSource).not.toContain("calc(100vh");
    expect(sceneSource).not.toContain("CANVAS_HEIGHT"); // 常量随之退役
  });

  it("CANVAS_MIN_HEIGHT 保底保留（minHeight 消费锚——短视口不塌缩）", () => {
    expect(sceneSource).toContain("CANVAS_MIN_HEIGHT = 420");
    expect(sceneSource).toMatch(/minHeight:\s*CANVAS_MIN_HEIGHT/);
  });

  it("画布容器链：relative div flex:1+minHeight:0（中段）+zone 包裹 flex 列（链首）", () => {
    // Scene 侧：Canvas 外层 relative div 承弹性（flex:1/minHeight:0 同排）
    expect(sceneSource).toMatch(/position:\s*"relative",\s*\n\s*flex:\s*1,\s*\n\s*minHeight:\s*0,/);
    // zone 侧：scale 包裹 div 立 flex 列（Fragment 扁平子的弹性父——banners/
    // toolbar/画布三段竖排，画布段吃满余高；flex:1/minHeight:0 弹性沿承）
    expect(zoneSource).toMatch(/minHeight:\s*0,\s*\n\s*display:\s*"flex",\s*\n\s*flexDirection:\s*"column",\s*\n\s*transform:/);
  });
});
