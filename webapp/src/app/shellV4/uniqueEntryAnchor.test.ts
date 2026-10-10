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
 *        触发）——多源/零源即红（提交通道旁路防回归）；⑤AUTH_EVENT
 *        消费面第五锚（B7 收口批 U6——裁决 R-1 预案形态：**代码形态
 *        匹配非裸串**——正则四选一〔import 解构/add(Event)?Listener/
 *        removeEventListener/dispatchEvent 与 AUTH_EVENT 组合〕，注释面
 *        4 件同含 AUTH_EVENT 串〔dockBar/shellV4/statusBar/
 *        tokenSettingsModal 头注与 JSDoc——B3 迁移留痕〕裸串锚出生即红
 *        ——代码形态锚对注释自然出局）：命中恰=[app/App.tsx〔legacy
 *        冻结监听〕, app/shellV4/settingsSelfHeal.ts, shared/api/http.ts
 *        〔派发侧〕]——第二消费监听出现即红。B7 R1 回炉硬化
 *        （k2-W-1+d1-C3/W3 2026-10-10）三改：①listener 两支+dispatch 支
 *        `(` 后空白容差（`\s*`——换行/缩进调用形态不逃锚）；②匹配形态
 *        改**全文件整体匹配**（原逐行 split——多行 import/调用形态逃锚
 *        面；行定位仅报告用不参与判定）；③新增字面串支 `"wp:auth"`
 *        （事件名字面形态——d1-W3 绕过面：不 import 常量直用字面即第二
 *        消费面）：该支期望恰=[shared/events.ts]（常量定义处="wp:auth"
 *        字面全树唯一在场——定义面恰一处的自证，期望集更新+本注申报）。
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

  it("AUTH_EVENT 消费面第五锚（B7——代码形态匹配非裸串+字面串支）：全文件整体匹配命中恰=[app/App.tsx, app/shellV4/settingsSelfHeal.ts, shared/api/http.ts]+字面支恰=[shared/events.ts]", () => {
    // 裁决 R-1 预案形态逐字实现（任务书 §二.U6）+B7 R1 回炉三改
    // （k2-W-1+d1-C3/W3）：①正则=import 解构/add(Event)?Listener/
    // removeEventListener/dispatchEvent 与 AUTH_EVENT 组合四选一，listener
    // 两支与 dispatch 支 `(` 后 `\s*` 空白容差（换行/缩进调用形态不逃锚
    // ——注入样本自证见批档 red-run-b7.txt R1 节）；②**全文件整体匹配**
    // 非逐行（多行 import/跨行调用形态覆盖；行定位仅报告用不参与判定）
    // ——注释面 4 件（dockBar/shellV4/statusBar/tokenSettingsModal 头注
    // JSDoc 迁移留痕）同含 AUTH_EVENT 裸串但不匹配代码形态自然出局；
    // ③字面串支 "wp:auth"（事件名字面——d1-W3 绕过面：不 import 常量
    // 直用字面绕代码形态锚），双引号/单引号两形同收（prettier 双引号
    // 常态+单引号旁路同锚）：期望恰=[shared/events.ts]（const 定义处=
    // "wp:auth" 字面全树唯一在场——定义面恰一处的自证）。第二消费监听
    // 出现（新 import/新监听/新派发/字面直用）即红——自愈回路单消费面锁。
    // B7 R1 主控补笔（k2-delta-W1）：四支 \b 词边界（AUTH_EVENT_V2 类兄弟
    // 标识符子串误命中=假绿方向收口）。残余面声明（d1-delta-K1 主控裁定
    // =本锚定位「防回归」非「防规避」）：命名空间访问/动态 import 解构/
    // 别名 const/模板串与拼接字面=蓄意规避形态不在锚内——内部防误用
    // 锚语义，规避级防护=代码评审面承载。
    const AUTH_CODE_FORM =
      /import\s*\{[^}]*\bAUTH_EVENT\b|add(Event)?Listener\(\s*\bAUTH_EVENT\b|removeEventListener\(\s*\bAUTH_EVENT\b|dispatchEvent\(\s*[^)]*\bAUTH_EVENT\b/;
    const codeHits = scanProductionSources(SRC_DIR)
      .filter((source) => AUTH_CODE_FORM.test(source.text)) // R1：整文件施正则
      .map((source) => source.rel)
      .sort(); // 跨目录枚举序平台差异归一（命中集=集合语义）
    expect(codeHits).toEqual([
      "app/App.tsx",
      "app/shellV4/settingsSelfHeal.ts",
      "shared/api/http.ts",
    ]);
    const AUTH_LITERAL_FORM = /["']wp:auth["']/;
    const literalHits = scanProductionSources(SRC_DIR)
      .filter((source) => AUTH_LITERAL_FORM.test(source.text))
      .map((source) => source.rel)
      .sort();
    expect(literalHits).toEqual(["shared/events.ts"]);
  });
});
