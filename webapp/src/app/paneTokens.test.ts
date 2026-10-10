/**
 * 列宽令牌落地测试（M1 批——tokens-2b3 §A 物理落地纪律=定义与消费同步；
 * themeLinkage 模式：node:fs 读 CSS/App 源文断言，node 直测零 jsdom）。
 *
 * 输入:  ./global.css 原文+./legacyShell.tsx+./App.tsx 双件源文
 *        （readFileSync——B7 拆件随迁+R1 回炉双件读：原读 App.tsx 单源
 *        〔M1 期唯一消费点〕→B7 收口批拆件迁 legacyShell.tsx 单源→
 *        R1-B 复宽〔k2-N-2+d1-N2〕：拆件后消费面横跨两件，单一读源
 *        任一侧再迁/删除即漏防——改双件拼接读源）
 * 输出:  断言组：①:root 定义面——--wp-pane-left: 232px/
 *        --wp-pane-right: 420px（tokens-2b3 §A 冻结值逐字）；②消费面——
 *        legacyShell.tsx〔主消费点——aside 列宽〕+App.tsx〔overlays
 *        编排留守面〕拼接源上 var(--wp-pane-left)/var(--wp-pane-right)
 *        消费在场（定义与消费同步机检——A2-N-06 零消费死变量防线：
 *        并集在场断言——两件消费面同时消失即红；实测 App.tsx 现况零
 *        wp-pane 串〔overlays=Modal 浮层无列宽消费〕，legacy 面删除批
 *        若不清消费面本断言即红=防残留死变量；B7 拆件随迁+R1-B 双读）
 *        ；③预算代数
 * 自检（值自 CSS 抽取）——左+右 ≤/＝652（tokens-2b3 §A 总预算
 *        规则；任一侧改值即红）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");
// B7 拆件随迁：消费面读源 App.tsx→legacyShell.tsx（aside var() 消费随
// legacy 壳 JSX 主体迁移——2026-10-10 主控裁量）；R1-B 复宽改双件读：
// legacyShell.tsx（主消费点）+App.tsx（overlays 留守面——现况零 var()
// 消费，并集在场断言两件同失消费即红——防拆件后单源读漏防）
const shellSource = readFileSync(join(__dirname, "legacyShell.tsx"), "utf-8");
const appSource = readFileSync(join(__dirname, "App.tsx"), "utf-8");

/** :root 块内单键声明抽取（themeLinkage parseRootVars 同款口径——先剥
 *  注释防伪块，值侧 trim 归一）。 */
function rootVar(name: string): string {
  const noComments = globalCss.replace(/\/\*[\s\S]*?\*\//g, "");
  const block = noComments.match(/:root\s*\{([^}]*)\}/)?.[1] ?? "";
  const match = block.match(new RegExp(`${name}\\s*:\\s*([^;]+);`));
  return (match?.[1] ?? "").trim();
}

describe("列宽令牌物理落地（tokens-2b3 §A——定义与消费同步）", () => {
  it(":root 定义面：--wp-pane-left=232px+--wp-pane-right=420px（冻结默认值）", () => {
    expect(rootVar("--wp-pane-left")).toBe("232px");
    expect(rootVar("--wp-pane-right")).toBe("420px");
  });

  it("消费面在场（双件读）：legacyShell.tsx+App.tsx 拼接源含 var(--wp-pane-left)/var(--wp-pane-right)（A2-N-06 防死变量——B7 拆件随迁+R1-B 复宽双读）", () => {
    // R1-B（k2-N-2+d1-N2）：legacyShell=主消费点；App=overlays 留守面
    // ——拼接读源=并集在场断言（两件消费面同时消失即红）
    const consumptionFace = shellSource + appSource;
    expect(consumptionFace).toContain("var(--wp-pane-left)");
    expect(consumptionFace).toContain("var(--wp-pane-right)");
  });

  it("预算代数自检（值自 CSS 抽取）：左+右=652（总预算恒等——任一侧改值即红）", () => {
    expect(
      parseInt(rootVar("--wp-pane-left")) + parseInt(rootVar("--wp-pane-right")),
    ).toBe(652);
  });
});
