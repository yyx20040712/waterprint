/**
 * lazyPaneLoader 工厂单测（UF-66 修复批——chunk 失败 cache-bust 重试恢复）。
 *
 * 输入:  lazyPaneLoader 工厂（node 面直测——零 DOM/react 渲染依赖）；
 *        performance 资源时序以 vi.spyOn 假 entry 桩（jsdom/ndjs 环境无
 *        真资源时序）；bustImport 以注入桩断言 URL 形态与次数参数
 * 输出:  断言组（brief D4 ①~⑦）：①attempt1 成功=loadModule+pick 包装
 *        （default=选件）；②attempt1 失败捕获（快照后新出现的 script 型
 *        .js entry→capturedUrl）；③鉴别（link 型/非 .js 尾/旧 entry 均
 *        不捕获）；④attempt2=bustImport(url+"?wpRetry=2")+pick 包装；
 *        ⑤capturedUrl 空（无性能 API/零 entry）回落 loadModule 复调=
 *        现行语义；⑥attempt2 bust 失败原样 rethrow+capturedUrl 不变+
 *        attempt3 参数递增 3；⑦缺省 bustImport 形态（真函数——node 面
 *        不能真 import http URL，拒绝即证缺省在场零真装载）
 *
 * 规格说明（UF-66 brief D1/D4；TDD 红先对 HEAD 跑红后实现转绿）：
 *   - 时序桩=vi.spyOn(performance,"getEntriesByType") 返回受控 entry
 *     数组（name+initiatorType 二字段=工厂观测面同形）；entry 追加时机
 *     在 loadModule 桩内（快照之后），模拟浏览器失败请求落资源时序；
 *   - 「原样 rethrow」以错误实例同一性（rejects.toBe(failure)）断言——
 *     非消息匹配（防包装错误混入静默通过）；
 *   - 第三参 bustImport=注入面 seam（brief D1：jsdom 面单测注入口，非
 *     API 面）；⑦ 不注第三参观察缺省——node 面 http URL 动态 import
 *     必拒（ERR_UNSUPPORTED_ESM_URL_SCHEME 族），以「拒绝且非
 *     loadModule 复调」证实缺省真函数在场。
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

describe("lazyPaneLoader（UF-66 cache-bust 重试恢复）", () => {
  it("① attempt1 成功：走 loadModule+pick 包装——default=选件，bustImport 零调用", async () => {
    const loadModule = vi.fn(async () => ({ Pane: paneA }));
    const pick = vi.fn(pickPane);
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, pick, bustImport);
    const wrapped = await loader();
    expect(wrapped.default).toBe(paneA);
    expect(loadModule).toHaveBeenCalledTimes(1);
    expect(pick).toHaveBeenCalledTimes(1);
    expect(bustImport).not.toHaveBeenCalled();
  });

  it("② attempt1 失败捕获：快照后新出现的 script 型 .js entry→capturedUrl（attempt2 bust URL 证实）", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error(
      "Failed to fetch dynamically imported module: http://x/pane-chunk1.js",
    );
    const loadModule = vi.fn(failingLoad(timeline, "http://x/pane-chunk1.js", failure));
    const bustImport = vi.fn(async (): Promise<FakePaneModule> => ({ Pane: paneB }));
    const loader = lazyPaneLoader(loadModule, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure); // 原样 rethrow
    await loader(); // attempt2
    expect(bustImport).toHaveBeenCalledTimes(1);
    expect(bustImport).toHaveBeenCalledWith("http://x/pane-chunk1.js?wpRetry=2");
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
      const loader = lazyPaneLoader(loadModule, pickPane, bustImport);
      await expect(loader()).rejects.toBe(failure);
      await expect(loader()).rejects.toBe(failure); // 回落复调再失败（同错误实例）
      expect(bustImport).not.toHaveBeenCalled();
      expect(loadModule).toHaveBeenCalledTimes(2);
    };
    // link 型（modulepreload 依赖特征——非动态 import 入口）
    await assertNotCaptured((timeline) => {
      timeline.push({ name: "http://x/preload.js", initiatorType: "link" });
    });
    // script 型但非 .js 尾（样式/其他资源）
    await assertNotCaptured((timeline) => {
      timeline.push({ name: "http://x/pane.css", initiatorType: "script" });
    });
    // 旧 entry（快照已含同名——失败未产生新 entry）
    await assertNotCaptured(() => undefined, [
      { name: "http://x/old.js", initiatorType: "script" },
    ]);
  });

  it("④ attempt2 走 bustImport(url+\"?wpRetry=2\")：URL 形态与次数参数+pick 包装", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error("Loading chunk 3 failed.");
    const loadModule = vi.fn(failingLoad(timeline, "http://x/pane-chunk1.js", failure));
    const bustImport = vi.fn(async (url: string): Promise<FakePaneModule> => {
      expect(url).toBe("http://x/pane-chunk1.js?wpRetry=2"); // 次数参数=attempt 2
      return { Pane: paneB };
    });
    const loader = lazyPaneLoader(loadModule, pickPane, bustImport);
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
    const loader = lazyPaneLoader(loadModule, pickPane, bustImport);
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
      const loader2 = lazyPaneLoader(loadModule2, pickPane, bustImport2);
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

  it("⑥ attempt2 bust 失败原样 rethrow+capturedUrl 不变→attempt3 bust 参数递增 3", async () => {
    const { timeline } = stubResourceTiming();
    const failure1 = new Error(
      "Failed to fetch dynamically imported module: http://x/pane.js",
    );
    const failure2 = new Error("Failed to fetch http://x/pane.js?wpRetry=2");
    const loadModule = vi.fn(failingLoad(timeline, "http://x/pane.js", failure1));
    const bustImport = vi
      .fn(async (): Promise<FakePaneModule> => ({ Pane: paneA }))
      .mockRejectedValueOnce(failure2)
      .mockResolvedValueOnce({ Pane: paneC });
    const loader = lazyPaneLoader(loadModule, pickPane, bustImport);
    await expect(loader()).rejects.toBe(failure1); // attempt1
    await expect(loader()).rejects.toBe(failure2); // attempt2 bust 失败=原样 rethrow
    const wrapped = await loader(); // attempt3
    expect(bustImport).toHaveBeenNthCalledWith(1, "http://x/pane.js?wpRetry=2");
    expect(bustImport).toHaveBeenNthCalledWith(2, "http://x/pane.js?wpRetry=3"); // 基 URL 不变+参数递增
    expect(bustImport).toHaveBeenCalledTimes(2);
    expect(wrapped.default).toBe(paneC);
  });

  it("⑦ 缺省 bustImport 形态：真函数在场（node 面不能真 import http URL——拒绝即证，零真装载）", async () => {
    const { timeline } = stubResourceTiming();
    const failure = new Error("Importing a module script failed.");
    const loadModule = vi.fn(
      failingLoad(timeline, "http://127.0.0.1:4200/assets/lazyPane-abc.js", failure),
    );
    const loader = lazyPaneLoader(loadModule, pickPane); // 第三参缺省
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
