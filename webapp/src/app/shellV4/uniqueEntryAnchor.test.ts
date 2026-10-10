/**
 * ⟳枚举=唯一提交入口结构锚（B3 任务书 §三.U4——源扫描制式沿
 * formulaKatexGate.test.ts 先例：读源文件字符串断言，零运行期渲染）。
 *
 * 输入:  shellV4 生产源树（*.ts/*.tsx 排除 *.test.*——v4 面）+app 生产源
 *        树（jointSolutions.tsx=JointSubmitForm 复用件承载面在 app 层）
 * 输出:  断言族：①单元枚举 hook（useRunEnumerationApiCalcEnumeratePost）
 *        v4 树内消费面恰=enumerateModal.tsx（EnumerateBar 承载件）一源
 *        ②wp-v4-reenumerate v4 树内恰=solutionCards.tsx 一源（开枚举
 *        Modal 唯一触发）③联合枚举 hook（useRunJointEnumerationApi
 *        SolutionJointEnumeratePost 全名锚——注释提及不误中）app 树内
 *        消费面恰=jointSolutions.tsx（JointSubmitForm 承载件）一源
 *        ④wp-v4-joint-open v4 树内恰=designZone.tsx 一源（联合提交
 *        唯一触发）——多源/零源即红（提交通道旁路防回归）。
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const HERE = dirname(fileURLToPath(import.meta.url));
const V4_DIR = HERE; // webapp/src/app/shellV4
const APP_DIR = join(HERE, ".."); // webapp/src/app

/** 生产源扫描（*.ts/*.tsx；*.test.* 与 __fixtures__ 排除——测试/夹具非锚面）。 */
function scanProductionSources(dir: string): { rel: string; text: string }[] {
  const out: { rel: string; text: string }[] = [];
  const walk = (current: string) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const full = join(current, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "__fixtures__") {
          continue;
        }
        walk(full);
      } else if (
        /\.(ts|tsx)$/.test(entry.name) &&
        !/\.test\./.test(entry.name)
      ) {
        out.push({
          rel: relative(APP_DIR, full).replace(/\\/g, "/"),
          text: readFileSync(full, "utf8"),
        });
      }
    }
  };
  walk(dir);
  return out;
}

/** 含锚串的生产文件清单（相对 app 目录 posix 形）。 */
function filesContaining(dir: string, needle: string): string[] {
  return scanProductionSources(dir)
    .filter((source) => source.text.includes(needle))
    .map((source) => source.rel);
}

describe("⟳枚举=唯一提交入口·结构锚（源扫描）", () => {
  it("单元枚举 hook：v4 树内消费面恰=enumerateModal.tsx（EnumerateBar 承载件）一源", () => {
    // legacy ribbon.tsx 亦消费（冻结面）——本锚辖 v4 树；v4 内第二消费
    // 面（绕过 EnumerateBar 直发）即红
    const hits = filesContaining(V4_DIR, "useRunEnumerationApiCalcEnumeratePost");
    expect(hits).toEqual(["shellV4/enumerateModal.tsx"]);
  });

  it("wp-v4-reenumerate：v4 树内恰=solutionCards.tsx 一源（开枚举 Modal 唯一触发）", () => {
    const hits = filesContaining(V4_DIR, 'wp-v4-reenumerate');
    expect(hits).toEqual(["shellV4/solutionCards.tsx"]);
  });

  it("联合枚举 hook：app 树内消费面恰=jointSolutions.tsx（JointSubmitForm 承载件）一源", () => {
    // 全名锚（注释中缀提及不误中）——v4 树内出现（绕过 JointSubmitForm
    // 直发）即红
    const hits = filesContaining(
      APP_DIR,
      "useRunJointEnumerationApiSolutionJointEnumeratePost",
    );
    expect(hits).toEqual(["jointSolutions.tsx"]);
  });

  it("wp-v4-joint-open：v4 树内恰=designZone.tsx 一源（联合提交唯一触发）", () => {
    const hits = filesContaining(V4_DIR, "wp-v4-joint-open");
    expect(hits).toEqual(["shellV4/designZone.tsx"]);
  });
});
