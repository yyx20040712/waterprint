/**
 * ⟳枚举=唯一提交入口结构锚（B3 任务书 §三.U4——源扫描制式沿
 * formulaKatexGate.test.ts 先例：读源文件字符串断言，零运行期渲染）。
 *
 * B3 R1 回炉 R1-W2（k2-W2+d1-W-1）2026-10-10：扫描根=src 全树（原 app
 * 树——提交通道落 features/ 可绕锚的缺口闭合）；排除面={*.test.*，
 * __fixtures__，shared/api/generated（定义面）}。
 *
 * 输入:  webapp/src 生产源树（*.ts/*.tsx——排除测试/夹具/生成面）
 * 输出:  断言族（全树口径——相对 src 的 posix 路径，命中集恰等）：
 *        ①单元枚举 hook（useRunEnumerationApiCalcEnumeratePost）消费面
 *        恰=[app/ribbon.tsx, app/shellV4/enumerateModal.tsx]（ribbon=
 *        legacy 冻结面合法消费——legacy 物理删除批随批更新本锚期望集）
 *        ②wp-v4-reenumerate 恰=[app/shellV4/solutionCards.tsx]（开枚举
 *        Modal 唯一触发）③联合枚举 hook（useRunJointEnumerationApi
 *        SolutionJointEnumeratePost 全名锚——注释中缀提及不误中）恰=
 *        [app/jointSolutions.tsx]（JointSubmitForm 承载件）④
 *        wp-v4-joint-open 恰=[app/shellV4/designZone.tsx]（联合提交唯一
 *        触发）——多源/零源即红（提交通道旁路防回归）。
 *
 * 扫描语义边界声明〔R1-W2 兼收 k2-N2/d1-N1——已知脆性在案〕：本锚=
 * 源文本「串面命中」计数，非 AST「引用面」——注释/字符串字面量中的
 * 锚串会计入命中（全名锚缓解但不根治：动态拼名/重导出绕过不设防）。
 * 锚升级 AST 引用面=后续批裁量（登记非本批缺口）。
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const HERE = dirname(fileURLToPath(import.meta.url));
// R1-W2：扫描根=src 全树（shellV4/ 上溯两级）
const SRC_DIR = join(HERE, "..", "..");

/** 生产源扫描（*.ts/*.tsx；排除面：*.test.* / __fixtures__ /
 *  shared/api/generated〔orval 定义面——锚辖消费面〕）。 */
function scanProductionSources(dir: string): { rel: string; text: string }[] {
  const out: { rel: string; text: string }[] = [];
  const walk = (current: string) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const full = join(current, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "__fixtures__") {
          continue;
        }
        const relDir = relative(SRC_DIR, full).replace(/\\/g, "/");
        if (relDir === "shared/api/generated" || relDir.startsWith("shared/api/generated/")) {
          continue;
        }
        walk(full);
      } else if (
        /\.(ts|tsx)$/.test(entry.name) &&
        !/\.test\./.test(entry.name)
      ) {
        out.push({
          rel: relative(SRC_DIR, full).replace(/\\/g, "/"),
          text: readFileSync(full, "utf8"),
        });
      }
    }
  };
  walk(dir);
  return out;
}

/** 含锚串的生产文件清单（相对 src 目录 posix 形）。 */
function filesContaining(needle: string): string[] {
  return scanProductionSources(SRC_DIR)
    .filter((source) => source.text.includes(needle))
    .map((source) => source.rel);
}

describe("⟳枚举=唯一提交入口·结构锚（源扫描——R1-W2 src 全树口径）", () => {
  it("单元枚举 hook：全树消费面恰=[app/ribbon.tsx, app/shellV4/enumerateModal.tsx]（ribbon=legacy 冻结面合法消费——legacy 删除批随批更新期望集）", () => {
    // v4 面内第二消费面（绕过 EnumerateBar 直发）即红；ribbon=legacy
    // 冻结面（B3 边界裁定零触碰）合法在场，legacy 物理删除批须同批
    // 更新本锚期望集并回读清点账（docs/ui-entry-ledger.md）
    const hits = filesContaining("useRunEnumerationApiCalcEnumeratePost");
    expect(hits).toEqual(["app/ribbon.tsx", "app/shellV4/enumerateModal.tsx"]);
  });

  it("wp-v4-reenumerate：全树恰=[app/shellV4/solutionCards.tsx] 一源（开枚举 Modal 唯一触发）", () => {
    const hits = filesContaining("wp-v4-reenumerate");
    expect(hits).toEqual(["app/shellV4/solutionCards.tsx"]);
  });

  it("联合枚举 hook：全树消费面恰=[app/jointSolutions.tsx]（JointSubmitForm 承载件——全名锚，注释中缀提及不误中）", () => {
    // features/ 树内出现（绕过 JointSubmitForm 直发）即红——R1-W2 扫描面
    // 扩全树的本旨缺口
    const hits = filesContaining(
      "useRunJointEnumerationApiSolutionJointEnumeratePost",
    );
    expect(hits).toEqual(["app/jointSolutions.tsx"]);
  });

  it("wp-v4-joint-open：全树恰=[app/shellV4/designZone.tsx] 一源（联合提交唯一触发）", () => {
    const hits = filesContaining("wp-v4-joint-open");
    expect(hits).toEqual(["app/shellV4/designZone.tsx"]);
  });
});
