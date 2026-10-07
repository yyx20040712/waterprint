/**
 * 懒装载器工厂（UF-66 修复批 2026-10-07+回炉 R1/R2——chunk 失败重试
 * cache-bust 恢复+风暴冷却窗+chunkHint 归因）。
 *
 * 输入:  loadModule=动态模块装载器（() => import("./xPane") 形）；
 *        chunkHint=本槽 chunk 归因基名（=specifier 基名，prod 命名形态
 *        /assets/<chunkHint>-HASH.js——R2 并发/多入口误捕防御）；
 *        pick=named export 选件（(m) => m.XPane as ComponentType——as
 *        收进 pick）；bustImport=测试注入口（缺省=(url) => import(url)
 *        ——@vite-ignore 注释在场防构建期静态改写；第 4 参为 jsdom/ndjs
 *        面单测 seam，非公开 API 面）
 * 输出:  React.lazy 兼容装载器 () => Promise<{ default: ComponentType }>：
 *        attempt 1 走 loadModule，失败时经 performance 资源时序差分+hint
 *        过滤捕获本槽入口 chunk URL；attempt ≥2 且捕获在场且冷却窗外→
 *        bustImport(url+"?wpRetry="+attempt) 以新模块图键破除失败占位；
 *        冷却窗内（R1——距上次 bust < BUST_COOLDOWN_MS）→回落 loadModule
 *        复调（同 URL 模块图缓存拒绝=零网络——G3 未提交渲染重调风暴限速）；
 *        捕获缺场（无资源时序环境——jsdom/node）→回落 loadModule 复调
 *        （=UF-66 前现行语义，消费面行为零变）；失败一律原样 rethrow
 *        （ErrorBoundary 分级与上报面语义不变）
 *
 * 规格说明（UF-66 预裁决 M1 主案+回炉单 R1/R2；探针档
 * .workflow/tmp/uf66-mech-probe/；G3 证据=g2-evidence/diag-g3*.cjs——
 * 诊断依据 diag-uf65.json 三重实证在 .workflow/2b5-20261007/）：
 *   - 背景：失败的动态 import 在真实 Chromium 模块图记 null 占位——同
 *     URL 重建 lazy 重调 load 零新网络请求直接拒绝；追加 ?wpRetry=N
 *     查询串=新模块图键，浏览器发真网络请求重新装载；
 *   - R1 冷却窗（G3 风暴处置）：React 19 对拒绝后的 lazy 在未提交渲染
 *     通道可高频重调 ctor（实测 142~187 次/数秒）——修复后每次重调=新
 *     bust URL=真网络请求=无界风暴。冷却窗 BUST_COOLDOWN_MS=1000（模块
 *     级常量）：attempt≥2 且捕获在场时距上次 bust ≥1000ms 才 bust；
 *     lastBustAt 实例态（null 起），bust 决策点唯一置位（无论成败），
 *     回落路径不更新；冷却内回落 loadModule=同 URL 模块图缓存拒绝零
 *     网络（旧码静默语义）。用户重试点击天然 >1s 间隔→冷却后 bust
 *     恢复语义保持（门二断言）；驱动源 React 层根治另立 UF-67 登记；
 *   - R2 chunkHint 归因（并发/多入口误捕防御）：资源时序差分在时序
 *     交错下可误捕他人槽 chunk URL→bust 死锁。捕获过滤增
 *     entry.name.includes("/"+chunkHint+"-")（prod 命名形态锚定；dev
 *     .tsx 尾本就被 .js 过滤在捕获面外）；hint 失配=null 捕获走回落
 *     语义，不抛错；
 *   - URL 捕获=资源时序差分：import 前快照 entry name 集，失败后新
 *     出现 entry 中取首个 initiatorType==='script'（动态 import 入口
 *     chunk 特征——modulepreload 依赖为 'link' 可鉴别）且 name 以 .js
 *     结尾且含 /chunkHint- 者；无匹配或无性能 API→capturedUrl 维持
 *     null（回落管道）；attempt ≥2 bust 失败不更新 capturedUrl（基
 *     URL 稳定，bust 参数随次数递增）；
 *   - getEntriesByType 存在性守卫：缺性能 API 环境=快照 null 同回落
 *     管道（jsdom/ndjs 行为零变）；performance/Date.now 逐调用读取
 *     （非模块加载期缓存——测试桩可注入）；
 *   - 捕获逻辑挂 loadModule 失败管道（attempt 1 与回落复调同管道）：
 *     消费面可见行为=原样 rethrow 不变，仅闭包内 capturedUrl 记账——
 *     回落路径若真实发出网络请求并失败，同样可被差分捕获（机制一致；
 *     R2 后捕获仅本槽 URL 可入——重捕安全）。
 */
import type { ComponentType } from "react";

/** bust 冷却窗（R1——毫秒；距上次 bust 不足此值回落 loadModule 零网络）。 */
const BUST_COOLDOWN_MS = 1000;

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

/** 差分捕获：快照后新出现的本槽入口 chunk entry（script 型+.js 尾+
 *  /chunkHint- 锚定）首个 URL——hint 失配=不捕获（R2 归因）。 */
function captureChunkUrl(before: Set<string> | null, chunkHint: string): string | null {
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
      entry.name.endsWith(".js") &&
      entry.name.includes(`/${chunkHint}-`)
    ) {
      return entry.name;
    }
  }
  return null;
}

/** loadModule 管道：import 前快照，失败时差分捕获本槽入口 chunk URL 后原样 rethrow。 */
function loadModuleWithCapture<M>(
  loadModule: () => Promise<M>,
  chunkHint: string,
  remember: (url: string) => void,
): Promise<M> {
  const before = snapshotResourceNames();
  return loadModule().catch((error: unknown) => {
    const url = captureChunkUrl(before, chunkHint);
    if (url !== null) {
      remember(url);
    }
    throw error;
  });
}

/** 懒装载器工厂（模块头契约——UF-66 cache-bust 重试恢复+R1 冷却+R2 归因）。 */
export function lazyPaneLoader<M>(
  loadModule: () => Promise<M>,
  chunkHint: string,
  pick: (m: M) => ComponentType,
  bustImport?: (url: string) => Promise<M>,
): () => Promise<{ default: ComponentType }> {
  // 缺省 bustImport：@vite-ignore 注释必须在场（缺注会被 Vite 构建期静态
  // 改写——动态 URL 形须留给运行时真 import）
  const bust =
    bustImport ?? ((url: string) => import(/* @vite-ignore */ url) as Promise<M>);
  let attempt = 0;
  let capturedUrl: string | null = null;
  let lastBustAt: number | null = null;
  const remember = (url: string): void => {
    capturedUrl = url;
  };
  return () => {
    attempt += 1;
    const now = Date.now();
    let load: Promise<M>;
    if (attempt >= 2 && capturedUrl !== null) {
      if (lastBustAt === null || now - lastBustAt >= BUST_COOLDOWN_MS) {
        // R1：lastBustAt 唯一置点（bust 决策点——无论成败；回落路径不更新）
        lastBustAt = now;
        load = bust(`${capturedUrl}?wpRetry=${attempt}`);
      } else {
        // R1 冷却内：回落 loadModule 复调（同 URL 模块图缓存拒绝=零网络——
        // G3 未提交渲染重调风暴限速兜底）
        load = loadModuleWithCapture(loadModule, chunkHint, remember);
      }
    } else {
      load = loadModuleWithCapture(loadModule, chunkHint, remember);
    }
    return load.then((module) => ({ default: pick(module) }));
  };
}
