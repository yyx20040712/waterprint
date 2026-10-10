/**
 * 零教学性文字门（B7 收口批 2026-10-10——v4 生产树教学性文案零命中
 * 断言：源扫描制式沿 formulaKatexGate.test.ts/uniqueEntryAnchor.test.ts
 * 先例，读源字符串断言，零运行期渲染）。
 *
 * 扫描面定形（B7 预扫实录 .workflow/b7-20261010/red-run-b7.txt U2 节
 * ——import 图可达性计算）：app/shellV4 生产树（*.ts 与 *.tsx，排除
 * *.test.* 及 __fixtures__）。「features 内 v4 专产面」=空集——legacy 物理
 * 删除批未执行期，v4 可达的 110 个 features 面全部与 legacy 树双面共享
 * （共享面=「排除 legacy 面」条款出局）；legacy 删除批落地后如有 features
 * 面转为 v4 专产，本扫描面头注与实现须同批扩面（主控裁量）。
 *
 * 白名单（功能微文案豁免——预扫实证与禁词族零交叠）：空态引导（「尚未
 * 选择项目——在「项目」区打开或新建」族）/错误提示（「…失败」族）/
 * stale 原因（「旧」Tag）/校验结论（「校验…」族）/挂起说明（「规划中
 * （未实装）」族——networkZone 诚实文案，非教学性）。白名单实现形态=
 * 禁词族与白名单词零交叠的词表定形（预扫实录承载），非行号锚定——
 * 行号随源演进漂移，词表交叠检查为不变量。
 *
 * 输入:  app/shellV4 生产源树（node:fs 读源——零渲染零 jsdom）
 * 输出:  断言族：①教学性禁词族（22 模式）命中数恰 0（现况 0 命中=绿
 *        出生；注入自证红实录在批档）②扫描面非空守卫（扫描根漂移/
 *        通配失效导致零文件扫描=静默绿防线——恰 20 件〔B7 时点〕）
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCAN_DIR = HERE;

/** 教学性禁词族（B7 任务书 §二.U2 列举+执行者补全——预扫 22 模式全零
 *  命中实录定形，零误报；增词=预扫复跑实证后同步批档）。 */
const BANNED_PATTERNS: readonly RegExp[] = [
  /点击即可/,
  /点击.{0,12}即可/,
  /操作步骤/,
  /使用说明/,
  /教程/,
  /帮助你/,
  /如何使用/,
  /请参考手册/,
  /新手/,
  /引导你/,
  /step\s*\d/i,
  /示例[：:]\s*演示/,
  /快速上手/,
  /上手指南/,
  /入门/,
  /向导/,
  /wizard/i,
  /\bguide\b/i,
  /tutorial/i,
  /how to/i,
  /操作指南/,
  /小贴士/,
];

/** 生产源扫描（*.ts 与 *.tsx；排除面：*.test.* 与 __fixtures__）。 */
function scanShellV4Sources(dir: string): { rel: string; text: string }[] {
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
          rel: entry.name,
          text: readFileSync(full, "utf8"),
        });
      }
    }
  };
  walk(dir);
  return out;
}

describe("零教学性文字门（B7——v4 生产树禁词族命中恰 0）", () => {
  it("教学性禁词族（22 模式）命中数恰 0（白名单=空态引导/错误提示/stale 原因/校验结论——预扫实证零交叠）", () => {
    const sources = scanShellV4Sources(SCAN_DIR);
    const hits: string[] = [];
    for (const source of sources) {
      for (const line of source.text.split(/\r?\n/)) {
        for (const pattern of BANNED_PATTERNS) {
          if (pattern.test(line)) {
            hits.push(`${source.rel}: 「${pattern.source}」 ← ${line.trim().slice(0, 60)}`);
          }
        }
      }
    }
    expect(hits).toEqual([]);
  });

  it("扫描面非空守卫：shellV4 生产件恰 20 件（扫描根漂移=静默绿防线）", () => {
    const sources = scanShellV4Sources(SCAN_DIR);
    expect(sources.length).toBe(20);
    expect(sources.map((s) => s.rel).sort()).toEqual(
      [
        "analysisPane.tsx",
        "analysisView.ts",
        "backfillSection.tsx",
        "designZone.tsx",
        "dockBar.tsx",
        "draftingZone.tsx",
        "enumerateModal.tsx",
        "hierarchicalCatalog.tsx",
        "jointSolutionCards.tsx",
        "networkZone.tsx",
        "projectsZone.tsx",
        "reportDoc.tsx",
        "reportZone.tsx",
        "settingsSelfHeal.ts",
        "shellV4.tsx",
        "solutionCards.tsx",
        "solutionDeviation.ts",
        "thumbnailFlow.tsx",
        "viewer3dZone.tsx",
        "zoneBand.tsx",
      ].sort(),
    );
  });
});
