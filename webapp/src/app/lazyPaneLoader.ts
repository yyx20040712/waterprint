/**
 * 懒装载器工厂（UF-66 修复批 2026-10-07——chunk 失败重试 cache-bust 恢复）。
 *
 * 输入:  loadModule=动态模块装载器（() => import("./xPane") 形）；pick=
 *        named export 选件（(m) => m.XPane as ComponentType——as 收进
 *        pick）；bustImport=测试注入口（缺省=(url) => import(url)——
 *        @vite-ignore 注释在场防构建期静态改写；第三参为 jsdom/ndjs 面
 *        单测 seam，非公开 API 面）
 * 输出:  React.lazy 兼容装载器 () => Promise<{ default: ComponentType }>：
 *        attempt 1 走 loadModule，失败时经 performance 资源时序差分捕获
 *        入口 chunk URL；attempt ≥2 且捕获在场→bustImport(url+"?wpRetry=
 *        "+attempt) 以新模块图键破除失败占位；捕获缺场（无资源时序环境
 *        ——jsdom/node）→回落 loadModule 复调（=UF-66 前现行语义，消费
 *        面行为零变）；失败一律原样 rethrow（ErrorBoundary 分级与上报面
 *        语义不变）
 *
 * 规格说明（UF-66 预裁决 M1 主案——机制经主控临时探针四项实证，探针档
 * .workflow/tmp/uf66-mech-probe/；证据=2b5-20261007/g2-evidence/
 * diag-uf65.json 三重实证）：
 *   - 背景：失败的动态 import 在真实 Chromium 模块图记 null 占位——同
 *     URL 重建 lazy 重调 load 零新网络请求直接拒绝（LazyPane onRetry 链
 *     机制正确执行但对用户无效，仅 reload 可恢复）；追加 ?wpRetry=N
 *     查询串=新模块图键，浏览器发真网络请求重新装载（探针④完整回路）；
 *   - URL 捕获=资源时序差分：import 前快照 entry name 集，失败后新出现
 *     entry 中取首个 initiatorType==='script'（动态 import 入口 chunk
 *     特征——modulepreload 依赖为 'link' 可鉴别）且 name 以 .js 结尾者；
 *     无匹配或无性能 API→capturedUrl 维持 null（回落管道）；attempt ≥2
 *     bust 失败不更新 capturedUrl（基 URL 稳定，bust 参数随次数递增）；
 *   - getEntriesByType 存在性守卫：缺性能 API 环境=快照 null 同回落
 *     管道（jsdom/ndjs 行为零变）；performance 逐调用读取（非模块加载
 *     期缓存——测试桩可注入）；
 *   - 捕获逻辑挂 loadModule 失败管道（attempt 1 与回落复调同管道）：
 *     消费面可见行为=原样 rethrow 不变，仅闭包内 capturedUrl 记账——
 *     回落路径若真实发出网络请求并失败，同样可被差分捕获（机制一致）。
 */
import type { ComponentType } from "react";

/** 资源时序 entry 观测面（PerformanceResourceTiming 字段子集——测试桩同形）。 */
interface ResourceTimingEntryLike {
  name: string;
  initiatorType: string;
}

/** performance 观测面（存在性守卫——缺性能 API 环境返回 null 走回落管道）。 */
function resourceTimingScope(): {
  getEntriesByType: (type: string) => ResourceTimingEntryLike[];
} | null {
  const perf = (globalThis as { performance?: unknown }).performance;
  if (
    typeof perf !== "object" ||
    perf === null ||
    typeof (perf as { getEntriesByType?: unknown }).getEntriesByType !==
      "function"
  ) {
    return null;
  }
  return perf as {
    getEntriesByType: (type: string) => ResourceTimingEntryLike[];
  };
}

/** import 前快照：资源时序 name 集（差分基线——null=无资源时序环境）。 */
function snapshotResourceNames(): Set<string> | null {
  const scope = resourceTimingScope();
  if (scope === null) {
    return null;
  }
  return new Set(scope.getEntriesByType("resource").map((entry) => entry.name));
}

/** 差分捕获：快照后新出现的入口 chunk entry（script 型+.js 尾）首个 URL。 */
function captureChunkUrl(before: Set<string> | null): string | null {
  if (before === null) {
    return null;
  }
  const scope = resourceTimingScope();
  if (scope === null) {
    return null;
  }
  for (const entry of scope.getEntriesByType("resource")) {
    if (
      !before.has(entry.name) &&
      entry.initiatorType === "script" &&
      entry.name.endsWith(".js")
    ) {
      return entry.name;
    }
  }
  return null;
}

/** loadModule 管道：import 前快照，失败时差分捕获入口 chunk URL 后原样 rethrow。 */
function loadModuleWithCapture<M>(
  loadModule: () => Promise<M>,
  remember: (url: string) => void,
): Promise<M> {
  const before = snapshotResourceNames();
  return loadModule().catch((error: unknown) => {
    const url = captureChunkUrl(before);
    if (url !== null) {
      remember(url);
    }
    throw error;
  });
}

/** 懒装载器工厂（模块头契约——UF-66 cache-bust 重试恢复）。 */
export function lazyPaneLoader<M>(
  loadModule: () => Promise<M>,
  pick: (m: M) => ComponentType,
  bustImport?: (url: string) => Promise<M>,
): () => Promise<{ default: ComponentType }> {
  // 缺省 bustImport：@vite-ignore 注释必须在场（缺注会被 Vite 构建期静态
  // 改写——动态 URL 形须留给运行时真 import）
  const bust =
    bustImport ?? ((url: string) => import(/* @vite-ignore */ url) as Promise<M>);
  let attempt = 0;
  let capturedUrl: string | null = null;
  return () => {
    attempt += 1;
    const load: Promise<M> =
      attempt >= 2 && capturedUrl !== null
        ? bust(`${capturedUrl}?wpRetry=${attempt}`)
        : loadModuleWithCapture(loadModule, (url) => {
            capturedUrl = url;
          });
    return load.then((module) => ({ default: pick(module) }));
  };
}
