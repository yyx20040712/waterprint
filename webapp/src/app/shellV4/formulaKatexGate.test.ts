/**
 * registry 全公式 KaTeX 零错门（B6 计算说明批 §二.⑤ DoD 硬闸——
 * 「抽样全公式」=全量承载：fixture 451 条 renderToString 全量断言）。
 *
 * 输入:  __fixtures__/formula-latex.fixture.json（{formula_id, latex}[]——
 *        tools/gen_formula_fixture.py 产出入库；对账机检=core pytest
 *        test_formula_fixture.py 重生成逐字节比对）+reportDoc.tsx 源面
 * 输出:  断言族：①fixture 形状（451 条/升序全序/latex 非空）②katex
 *        renderToString 全量零 throw+输出含 katex-html（KaTeX 渲染
 *        真走查——报告 md 数学块渲染面的真源覆盖）③KaTeX CSS import
 *        在场（防漏引致裸公式串——读 reportDoc.tsx 源断言）
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import katex from "katex";
import { describe, expect, it } from "vitest";

/** fixture 行形（生成器契约——{formula_id, latex}）。 */
type FixtureRow = { formula_id: string; latex: string };

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE_PATH = join(HERE, "__fixtures__", "formula-latex.fixture.json");
const REPORT_DOC_PATH = join(HERE, "reportDoc.tsx");

// registry 全量基数（core 侧 test_formula_printers 同源计数——业务线
// 扩充时两侧同步；对账半边保证 fixture 恰为此基数）
const EXPECTED_FORMULAS = 451;

const rows: FixtureRow[] = JSON.parse(
  readFileSync(FIXTURE_PATH, "utf-8"),
) as FixtureRow[];

describe("公式 KaTeX 全量门·fixture 形状", () => {
  it("恰 451 条+formula_id 升序全序+latex 逐条非空", () => {
    expect(rows.length).toBe(EXPECTED_FORMULAS);
    const ids = rows.map((row) => row.formula_id);
    expect(ids).toEqual([...ids].sort());
    expect(new Set(ids).size).toBe(ids.length);
    for (const row of rows) {
      expect(row.latex.length, row.formula_id).toBeGreaterThan(0);
    }
  });
});

describe("公式 KaTeX 全量门·renderToString 零错", () => {
  it("451 条全量渲染零 throw+输出含 katex-html（display 形）", () => {
    const failures: string[] = [];
    let withoutHtml = 0;
    for (const row of rows) {
      try {
        const html = katex.renderToString(row.latex, {
          displayMode: true,
          throwOnError: true,
          strict: "ignore",
        });
        if (!html.includes("katex-html")) {
          withoutHtml += 1;
          failures.push(`${row.formula_id}: 输出缺 katex-html`);
        }
      } catch (error) {
        failures.push(
          `${row.formula_id}: ${error instanceof Error ? error.message : String(error)}`,
        );
      }
    }
    expect(withoutHtml).toBe(0);
    expect(failures, failures.slice(0, 10).join("\n")).toEqual([]);
  });

  it("inline 形（displayMode:false）同样全量零 throw", () => {
    const failures: string[] = [];
    for (const row of rows) {
      try {
        katex.renderToString(row.latex, {
          displayMode: false,
          throwOnError: true,
          strict: "ignore",
        });
      } catch (error) {
        failures.push(
          `${row.formula_id}: ${error instanceof Error ? error.message : String(error)}`,
        );
      }
    }
    expect(failures, failures.slice(0, 10).join("\n")).toEqual([]);
  });
});

describe("公式 KaTeX 全量门·CSS 入口在场", () => {
  it("reportDoc.tsx 含 katex/dist/katex.min.css import（防漏引致裸公式串）", () => {
    const source = readFileSync(REPORT_DOC_PATH, "utf-8");
    expect(source).toContain('import "katex/dist/katex.min.css"');
  });
});
