/**
 * 缩略图 PNG-first 源（spec.md §11 S9 降级链——批3 主体）。
 *
 * 输入:  场景单元集+registry（status=ready 条目的 thumb 路径）
 * 输出:  resolvePngThumbs（PNG 批取——成功=dataURL 直用；失败[404/网络]
 *        =缺席→实时后备队列）+probe 计数（window.__probe.
 *        thumbnailFallbacks——PNG 命中/404/转实时三计数可观测）
 *
 * 规格说明（S9：PNG 失败→C2-thumb 实时后备；降级队列并发上限 ≤2——
 *   ThumbnailStage 顺序队列恒 1 ≤2 合规；超限直落 UnitGlyph=实时队列
 *   本身即逐单元产出，无并发堆积面；probe 增降级计数）。
 */

import { familyForUnit, isReady } from "./registry";
import type { FallbackEntry } from "./fallbackLog";

/** S9 probe 计数器（window.__probe.viewer3d.thumbnailFallbacks 位）。 */
export type ThumbnailFallbackCounters = {
  pngHits: number;
  pngMisses: number;
  realtimeSwitches: number;
};

export const thumbnailCounters: ThumbnailFallbackCounters = {
  pngHits: 0,
  pngMisses: 0,
  realtimeSwitches: 0,
};

/** 测试复位。 */
export function resetThumbnailCounters(): void {
  thumbnailCounters.pngHits = 0;
  thumbnailCounters.pngMisses = 0;
  thumbnailCounters.realtimeSwitches = 0;
}

/** 场景内具 ready 模板族的单元（PNG-first 候选集）。 */
export function templateThumbUnits(unitIds: readonly string[]): ReadonlySet<string> {
  const set = new Set<string>();
  for (const unitId of unitIds) {
    const entry = familyForUnit(unitId);
    if (entry !== null && isReady(entry)) {
      set.add(unitId);
    }
  }
  return set;
}

/**
 * PNG 批取（并发不限——纯 fetch 轻载；S9 的 ≤2 限的是实时渲染队列）。
 * 成功→dataURL；失败→计数 pngMisses+realtimeSwitches（转实时后备）。
 */
export async function resolvePngThumbs(
  unitIds: readonly string[],
): Promise<Map<string, string>> {
  const results = new Map<string, string>();
  await Promise.all(
    [...templateThumbUnits(unitIds)].map(async (unitId) => {
      const entry = familyForUnit(unitId);
      if (entry === null) {
        return;
      }
      try {
        const response = await fetch(entry.thumb);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const blob = await response.blob();
        results.set(unitId, await blobToDataUrl(blob));
        thumbnailCounters.pngHits += 1;
      } catch {
        thumbnailCounters.pngMisses += 1;
        thumbnailCounters.realtimeSwitches += 1; // →C2-thumb 实时后备（S9 链）
      }
    }),
  );
  return results;
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

/** fallbackLog 兼容导出位（probe 聚合面消费——类型锚）。 */
export type { FallbackEntry };
