/**
 * lazyPaneLoader 工厂单测（UF-66 修复批+回炉 R1/R2——chunk 失败
 * cache-bust 重试恢复+风暴冷却窗+chunkHint 归因）。
 *
 * 输入:  lazyPaneLoader 工厂（node 面直测——零 DOM/react 渲染依赖）；
 *        performance 资源时序以 vi.spyOn 假 entry 桩（jsdom/ndjs 环境无
 *        真资源时序）；冷却窗以 vi.spyOn(Date,"now") 受控时钟桩；
 *        bustImport 以注入桩断言 URL 形态与次数参数
 * 输出:  断言组：既有 7 组（brief D4 ①~⑦——成功包装/失败捕获/鉴别
 *        （link 型·非 .js·旧 entry）/bust URL 形态与参数/无性能 API 回落
 *        /bust 失败原样 rethrow+capturedUrl 不变/缺省 bustImport 形态）
 *        +R1 冷却窗组（冷却内回落 loadModule 零 bust+lastBustAt 不更新/
 *        冷却外 bust 且置 lastBustAt/跨冷却递增参数保持+边界 999/1000）
 *        +R2 chunkHint 组（本槽 entry 捕获/他人槽 entry 不捕获回落）
 *
 * 规格说明（UF-66 brief D1/D4+回炉单 R1/R2；红先对回炉前 HEAD 跑红后
 * 实现转绿——red-run-r1.txt 在档）：
 *   - 时序桩=vi.spyOn(performance,"getEntriesByType") 返回受控 entry
 *     数组（name+initiatorType 二字段=工厂观测面同形）；entry 追加时机
 *     在 loadModule 桩内（快照之后），模拟浏览器失败请求落资源时序；
 *     entry name 采用 prod 形态 /assets/<chunkHint>-HASH.js（R2 过滤
 *     面的命中形态）；
 *   - 时钟桩=vi.spyOn(Date,"now") 返回受控 now（advance 推进——冷却
 *     判定 BUST_COOLDOWN_MS=1000 边界 999 拒/1000 行全钉死）；
 *   - 「原样 rethrow」以错误实例同一性（rejects.toBe(failure)）断言——
 *     非消息匹配（防包装错误混入静默通过）；
 *   - 第四参 bustImport=注入面 seam（brief D1：非 API 面）；既有 7 组
 *     单 bust 用例走真实 Date.now（lastBustAt=null 首放行——无冷却阻），
 *     多 bust 用例（⑥）显式控时；
 *   - ⑦ 缺省 bust：node 面 http URL 动态 import 必拒
 *     （ERR_UNSUPPORTED_ESM_URL_SCHEME 族），以「拒绝且非 loadModule
 *     复调」证实缺省真函数在场零真装载。
 */
import type { ComponentType } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { lazyPaneLoader } from "./lazyPaneLoader";

/** 假资源时序 entry（PerformanceResourceTiming 观测面字段子集）。 */
interface FakeEntry {
  name: string;
  initiatorType: string;
}

/** 测试用模块形态（M={Pane}——named export 选件语义）。 */
interface FakePaneModule {
  Pane: ComponentType;
}

/** 主 hint 与 prod 形态 URL（R2 过滤面命中形态 /assets/<hint>-HASH.js）。 */
const HINT = "drawingsPane";
const HINT_URL = "http://x/assets/drawingsPane-Cvc1lnrp.js";

/** pick 桩：named export 选件（as ComponentType 收进 pick 的换形面保真）。 */
function pickPane(m: FakePaneModule): ComponentType {
  return m.Pane;
}

/** 假组件（选件同一性断言用——null 渲染件零 DOM 依赖）。 */
const paneA: ComponentType = () => null;
const paneB: ComponentType = () => null;
const paneC: ComponentType = () => null;

/** 桩化 performance.getEntriesByType：受控 timeline（"resource" 外类型回 []）。 */
function stubResourceTiming(): { timeline: FakeEntry[] } {
  const timeline: FakeEntry[] = [];
  vi.spyOn(performance, "getEntriesByType").mockImplementation(
    (type: string) =>
      (type === "resource" ? [...timeline] : []) as unknown as PerformanceEntry[],
  );
  return { timeline };
}

/** 受控时钟（R1 冷却窗桩——vi.spyOn(Date,"now")，advance 推进模拟重试间隔）。 */
function stubClock(): { advance: (ms: number) => void } {
  let current = 1_000_000;
  vi.spyOn(Date, "now").mockImplementation(() => current);
  return {
    advance: (ms: number) => {
      current += ms;
    },
  };
}

/** 失败装载桩：模拟浏览器行为——先落资源时序 entry（script 型 chunk）再拒。 */
function failingLoad(
  timeline: FakeEntry[],
  url: string,
  failure: Error,
): () => Promise<FakePaneModule> {
  return async () => {
    timeline.push({ name: url, initiatorType: "script" });
    throw failure;
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("lazyPaneLoader（UF-66 cache-bust 重试恢复——换形与捕获）", () => {
  it("① attempt1 成功：走 loadModule+pick 包装——default=选件，bustImport 零调用", async () => {
    const loadModule = vi.fn(async () => ({ Pane: paneA }));
    const pick = vi.fn(pickPane);
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, HINT, pick, bustImport);
    const wrapped = await loader();
    expect(wrapped.default).toBe(paneA);
    expect(loadModule).toHaveBeenCalledTimes(1);
    expect(pick).toHaveBeenCalledTimes(1);
    expect(bustImport).not.toHaveBeenCalled();
  });

  it("② attempt1 失败捕获：快照后新出现的 script 型 .js entry→capturedUrl（attempt2 bust URL 证实）", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error(
      `Failed to fetch dynamically imported module: ${HINT_URL}`,
    );
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure));
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // 原样 rethrow
    await loader(); // attempt2（lastBustAt=null 首放行——无冷却阻）
    expect(bustImport).toHaveBeenCalledTimes(1);
    expect(bustImport).toHaveBeenCalledWith(`${HINT_URL}?wpRetry=2`);
  });

  it("③ 鉴别：link 型/非 .js 尾/快照旧 entry 均不捕获→attempt2 回落 loadModule 复调", async () => {
    // 三形态共享断言管道：attempt1 失败+attempt2 仍走 loadModule（bust 零调用）
    const assertNotCaptured = async (
      push: (timeline: FakeEntry[]) => void,
      seed: FakeEntry[] = [],
    ): Promise<void> => {
      const { timeline } = stubResourceTiming();
      timeline.push(...seed);
      const failure = new Error("Loading chunk 5 failed.");
      const loadModule = vi.fn(async (): Promise<FakePaneModule> => {
        push(timeline);
        throw failure;
      });
      const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
      const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
      await expect(loader()).rejects.toBe(failure);
      await expect(loader()).rejects.toBe(failure); // 回落复调再失败（同错误实例）
      expect(bustImport).not.toHaveBeenCalled();
      expect(loadModule).toHaveBeenCalledTimes(2);
    };
    // link 型（modulepreload 依赖特征——非动态 import 入口；hint 形态名）
    await assertNotCaptured((timeline) => {
      timeline.push({ name: "http://x/assets/drawingsPane-pre.js", initiatorType: "link" });
    });
    // script 型但非 .js 尾（样式/其他资源；hint 形态名）
    await assertNotCaptured((timeline) => {
      timeline.push({ name: "http://x/assets/drawingsPane-style.css", initiatorType: "script" });
    });
    // 旧 entry（快照已含同名——失败未产生新 entry）
    await assertNotCaptured(() => undefined, [
      { name: "http://x/assets/drawingsPane-old.js", initiatorType: "script" },
    ]);
  });

  it("④ attempt2 走 bustImport(url+\"?wpRetry=2\")：URL 形态与次数参数+pick 包装", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error("Loading chunk 3 failed.");
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure));
    const bustImport = vi.fn(async (url: string): Promise<FakePaneModule> => {
      expect(url).toBe(`${HINT_URL}?wpRetry=2`); // 次数参数=attempt 2
      return { Pane: paneB };
    });
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure);
    const wrapped = await loader(); // attempt2：bust 成功
    expect(wrapped.default).toBe(paneB); // 同 pick 包装
    expect(bustImport).toHaveBeenCalledTimes(1);
    expect(loadModule).toHaveBeenCalledTimes(1); // attempt2 不再走 loadModule
  });

  it("⑤ capturedUrl 空（无性能 API/零 entry）→attempt2 回落 loadModule 复调=现行语义", async () => {
    // (a) API 在场但零资源 entry（jsdom/ndjs 现实形态——差分空集不捕获）
    const spy = vi
      .spyOn(performance, "getEntriesByType")
      .mockImplementation(() => [] as unknown as PerformanceEntry[]);
    const failure = new Error("Importing a module script failed.");
    const loadModule = vi
      .fn<() => Promise<FakePaneModule>>()
      .mockRejectedValueOnce(failure)
      .mockResolvedValueOnce({ Pane: paneB });
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneC }));
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure);
    const wrapped = await loader(); // attempt2 回落复调（本次成功）
    expect(wrapped.default).toBe(paneB);
    expect(bustImport).not.toHaveBeenCalled();
    expect(loadModule).toHaveBeenCalledTimes(2);
    spy.mockRestore();

    // (b) getEntriesByType 缺席（存在性守卫分支——快照 null 同回落管道）
    const descriptor = Object.getOwnPropertyDescriptor(performance, "getEntriesByType");
    Object.defineProperty(performance, "getEntriesByType", {
      configurable: true,
      value: undefined,
    });
    try {
      const failure2 = new Error("Importing a module script failed.");
      const loadModule2 = vi
        .fn<() => Promise<FakePaneModule>>()
        .mockRejectedValueOnce(failure2)
        .mockResolvedValueOnce({ Pane: paneC });
      const bustImport2 = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneA }));
      const loader2 = lazyPaneLoader(loadModule2, HINT, pickPane, bustImport2);
      await expect(loader2()).rejects.toBe(failure2);
      const wrapped2 = await loader2();
      expect(wrapped2.default).toBe(paneC);
      expect(bustImport2).not.toHaveBeenCalled();
      expect(loadModule2).toHaveBeenCalledTimes(2);
    } finally {
      if (descriptor) {
        Object.defineProperty(performance, "getEntriesByType", descriptor);
      } else {
        delete (performance as { getEntriesByType?: unknown }).getEntriesByType;
      }
    }
  });

  it("⑥ attempt2 bust 失败原样 rethrow+capturedUrl 不变→attempt3 bust 参数递增 3（跨冷却控时）", async () => {
    const { timeline } = stubResourceTiming();
    const { advance } = stubClock();
    const failure1 = new Error(
      `Failed to fetch dynamically imported module: ${HINT_URL}`,
    );
    const failure2 = new Error(`Failed to fetch ${HINT_URL}?wpRetry=2`);
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure1));
    const bustImport = vi
      .fn(async (): Promise<FakePaneModule> => ({ Pane: paneA }))
      .mockRejectedValueOnce(failure2)
      .mockResolvedValueOnce({ Pane: paneC });
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure1); // attempt1
    await expect(loader()).rejects.toBe(failure2); // attempt2 bust 失败=原样 rethrow
    advance(1000); // 冷却窗外（1000>=1000 边界）
    const wrapped = await loader(); // attempt3
    expect(bustImport).toHaveBeenNthCalledWith(1, `${HINT_URL}?wpRetry=2`);
    expect(bustImport).toHaveBeenNthCalledWith(2, `${HINT_URL}?wpRetry=3`); // 基 URL 不变+参数递增
    expect(bustImport).toHaveBeenCalledTimes(2);
    expect(wrapped.default).toBe(paneC);
  });

  it("⑦ 缺省 bustImport 形态：真函数在场（node 面不能真 import http URL——拒绝即证，零真装载）", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error("Importing a module script failed.");
    const loadModule = vi.fn(
      failingLoad(timeline, "http://127.0.0.1:4200/assets/drawingsPane-abc.js", failure),
    );
    const loader = lazyPaneLoader(loadModule, HINT, pickPane); // 第四参缺省
    await expect(loader()).rejects.toBe(failure);
    // attempt2：capturedUrl 在场→缺省 bust（真函数）被调——node 面 http URL
    // 动态 import 必拒（模块面无法真装载）；loadModule 不复调=证缺省路径
    const caught = await loader().then(
      () => null,
      (error: unknown) => error,
    );
    expect(caught).toBeInstanceOf(Error);
    expect(caught).not.toBe(failure); // 拒绝源=缺省 bust 的真 import，非 loadModule 复调
    expect(loadModule).toHaveBeenCalledTimes(1);
  });
});

describe("R1 冷却窗（G3 风暴限速——BUST_COOLDOWN_MS=1000+lastBustAt 实例态）", () => {
  it("R1-① 冷却内重调回落 loadModule 零 bust+lastBustAt 不更新（回落不重置冷却零点）", async () => {
    const { timeline } = stubResourceTiming();
    const { advance } = stubClock();
    const failure = new Error(`Failed to fetch dynamically imported module: ${HINT_URL}`);
    const bustFailure = new Error(`Failed to fetch ${HINT_URL}?wpRetry=2`);
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure));
    const bustImport = vi
      .fn(async (): Promise<FakePaneModule> => ({ Pane: paneA }))
      .mockRejectedValueOnce(bustFailure)
      .mockRejectedValueOnce(new Error("bust again"));
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // attempt1（捕获在场）
    await expect(loader()).rejects.toBe(bustFailure); // attempt2：首 bust（lastBustAt=T0）
    advance(400); // 冷却内（400<1000）
    await expect(loader()).rejects.toBe(failure); // attempt3：回落 loadModule 复调（同错误实例——零 bust）
    expect(bustImport).toHaveBeenCalledTimes(1); // 冷却内零 bust
    expect(loadModule).toHaveBeenCalledTimes(2);
    advance(600); // 自 bust 点 T0 累计 1000（若 attempt3 回落误更新 lastBustAt=T0+400 则 600<1000 仍阻）
    await expect(loader()).rejects.toBeInstanceOf(Error); // attempt4：bust 放行=证 lastBustAt 未在回落路径更新
    expect(bustImport).toHaveBeenCalledTimes(2);
    expect(bustImport).toHaveBeenNthCalledWith(2, `${HINT_URL}?wpRetry=4`);
  });

  it("R1-② 冷却外 bust 且置 lastBustAt（随后冷却内重调回落证置点在场）", async () => {
    const { timeline } = stubResourceTiming();
    const { advance } = stubClock();
    const failure = new Error("Loading chunk 8 failed.");
    const bustFailure = new Error("bust reject");
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure));
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => {
      throw bustFailure;
    });
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // attempt1
    advance(2000); // 冷却外（首 bust 本就放行——lastBustAt=null；此处亦证冷却外语义）
    await expect(loader()).rejects.toBe(bustFailure); // attempt2：bust 放行且置 lastBustAt
    expect(bustImport).toHaveBeenCalledTimes(1);
    expect(bustImport).toHaveBeenNthCalledWith(1, `${HINT_URL}?wpRetry=2`);
    await expect(loader()).rejects.toBe(failure); // attempt3：紧随（同刻 0<1000）回落 loadModule=置点已在
    expect(bustImport).toHaveBeenCalledTimes(1); // 仍零新 bust
    expect(loadModule).toHaveBeenCalledTimes(2);
  });

  it("R1-③ 两次 bust 间隔跨冷却的递增参数保持（999 拒/累计 1000 行边界）", async () => {
    const { timeline } = stubResourceTiming();
    const { advance } = stubClock();
    const failure = new Error("Importing a module script failed.");
    const bustFailure = new Error("bust reject 1");
    const loadModule = vi.fn(failingLoad(timeline, HINT_URL, failure));
    const bustImport = vi
      .fn(async (): Promise<FakePaneModule> => ({ Pane: paneA }))
      .mockRejectedValueOnce(bustFailure)
      .mockResolvedValueOnce({ Pane: paneC });
    const loader = lazyPaneLoader(loadModule, HINT, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // attempt1
    await expect(loader()).rejects.toBe(bustFailure); // attempt2 bust（wpRetry=2）
    advance(999); // 999<1000 冷却内
    await expect(loader()).rejects.toBe(failure); // attempt3：回落（bust 仍 1 次）
    expect(bustImport).toHaveBeenCalledTimes(1);
    advance(1); // 累计 1000（自 bust 点）——边界放行
    const wrapped = await loader(); // attempt4：bust 且 wpRetry=4（参数跨冷却递增不回退）
    expect(bustImport).toHaveBeenNthCalledWith(1, `${HINT_URL}?wpRetry=2`);
    expect(bustImport).toHaveBeenNthCalledWith(2, `${HINT_URL}?wpRetry=4`);
    expect(wrapped.default).toBe(paneC);
  });
});

describe("R2 chunkHint 归因（并发/多入口误捕防御——entry.name 含 /hint- 才捕获）", () => {
  it("R2-④ 本槽 entry（name 含 /chunkHint-）捕获→attempt2 bust 本槽 URL", async () => {
    const { timeline } = stubResourceTiming();
    const url = "http://x/assets/trustPane-Zz9k1.js"; // hint=trustPane（非主 hint——证参数化）
    const failure = new Error(`Failed to fetch dynamically imported module: ${url}`);
    const loadModule = vi.fn(failingLoad(timeline, url, failure));
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, "trustPane", pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure);
    await loader(); // attempt2
    expect(bustImport).toHaveBeenCalledTimes(1);
    expect(bustImport).toHaveBeenCalledWith(`${url}?wpRetry=2`);
  });

  it("R2-⑤ 他人槽 entry 不捕获（capturedUrl 保持 null→attempt2 回落，hint 失配不抛错）", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error("Loading chunk 6 failed.");
    // 他人槽 chunk（script 型+.js 尾+新 entry——仅 hint 不匹配本槽）
    const loadModule = vi.fn(async (): Promise<FakePaneModule> => {
      timeline.push({ name: "http://x/assets/costPane-Other9.js", initiatorType: "script" });
      throw failure;
    });
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, "drawingsPane", pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // 不抛新错（原样 rethrow）
    await expect(loader()).rejects.toBe(failure); // attempt2：回落 loadModule 复调
    expect(bustImport).not.toHaveBeenCalled(); // 零 bust=无误捕死锁面
    expect(loadModule).toHaveBeenCalledTimes(2);
  });
});
