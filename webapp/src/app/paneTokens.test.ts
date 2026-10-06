/**
 * 列宽令牌落地测试（M1 批——tokens-2b3 §A 物理落地纪律=定义与消费同步；
 * themeLinkage 模式：node:fs 读 CSS/App 源文断言，node 直测零 jsdom）。
 *
 * 输入:  ./global.css 原文+./App.tsx 源文（readFileSync）
 * 输出:  断言组：①:root 定义面——--wp-pane-left: 232px/
 *        --wp-pane-right: 420px（tokens-2b3 §A 冻结值逐字）；②消费面——
 *        App.tsx 源面 var(--wp-pane-left)/var(--wp-pane-right) 消费在场
 *        （定义与消费同步机检——A2-N-06 零消费死变量防线）；③预算代数
 *        自检（值自 CSS 抽取）——左+右 ≤/＝652（tokens-2b3 §A 总预算
 *        规则；任一侧改值即红）。
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const globalCss = readFileSync(join(__dirname, "global.css"), "utf-8");
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

  it("App.tsx 消费面在场：var(--wp-pane-left)/var(--wp-pane-right)（A2-N-06 防死变量）", () => {
    expect(appSource).toContain("var(--wp-pane-left)");
    expect(appSource).toContain("var(--wp-pane-right)");
  });

  it("预算代数自检（值自 CSS 抽取）：左+右=652（总预算恒等——任一侧改值即红）", () => {
    expect(
      parseInt(rootVar("--wp-pane-left")) + parseInt(rootVar("--wp-pane-right")),
    ).toBe(652);
  });
});
