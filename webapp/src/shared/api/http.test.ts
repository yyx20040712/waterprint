/**
 * http.ts 请求实例单测：路径锁定（C1 双前缀防回归）+错误归一两面（非 2xx/2xx 解析失败）。
 *
 * 输入:  customInstance+token.ts 三函数（mock fetch——node 环境 Response
 *        全局，零真实 HTTP；localStorage/window 经 vi.stubGlobal 注入）
 * 输出:  请求路径与错误语义断言（R2 C1/M3 防回归锁）+R2-A 批2 三面：
 *        token 存取往返（node 守卫）/Bearer 注入（空=零注入）/401 先派发
 *        AUTH_EVENT 再归一化 throw（非 401 零派发）
 *
 * 规格说明（R2 二审闭合；R2-A 批2 扩 D1/D3/D4 面）：
 *   - C1（Critical）：orval 生成 url 已含 /api 前缀（openapi path 键面）
 *     ——最终请求路径必须恰 "/api/…" 形态，禁二次前拼（曾致 18 端点全 404）；
 *   - M3：成功路径 2xx 非 JSON 体归一 WaterprintApiError（与非 2xx 路径对称）；
 *   - 服务端统一错误体 {detail, error_type} → code=error_type/message=detail；
 *   - R2-A 批2：token 空=零 Authorization 注入零行为变化；token 非空=
 *     Bearer 头注入；401 先派发 AUTH_EVENT（"wp:auth"）再走既有 throw
 *     （错误语义零变化；次序锁 R 轮 G1-04——dispatch/throw 时序标记
 *     断言）；非 401 零派发；node 无 localStorage 视同未配置。
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { AUTH_EVENT } from "../events";
import { WaterprintApiError, customInstance } from "./http";
import { clearApiToken, getApiToken, setApiToken } from "./token";

type FetchMock = ReturnType<typeof vi.fn>;

function stubFetch(response: Response): FetchMock {
  const mock = vi.fn(async () => response);
  vi.stubGlobal("fetch", mock);
  return mock;
}

/** 最小 localStorage 形态（node 环境无原生——Map 薄壳足量三函数面）。 */
function stubLocalStorage(): Map<string, string> {
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
    removeItem: (key: string) => void store.delete(key),
  });
  return store;
}

/** 最小 window 形态（node 环境无原生——dispatchEvent spy 面）。 */
function stubWindow(): ReturnType<typeof vi.fn> {
  const dispatchEvent = vi.fn(() => true);
  vi.stubGlobal("window", { dispatchEvent });
  return dispatchEvent;
}

/** 断言辅助：取 mock fetch 首调 headers（RequestInit.headers 面）。 */
function sentHeaders(mock: FetchMock): Record<string, string> {
  const init = mock.mock.calls[0]?.[1] as RequestInit | undefined;
  return (init?.headers ?? {}) as Record<string, string>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("customInstance 路径锁定（C1 防回归）", () => {
  it("请求 url 恰 /api/scene/{id}——无 /api 双前缀", async () => {
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({ url: "/api/scene/p1", method: "GET" });
    expect(mock).toHaveBeenCalledOnce();
    expect(mock.mock.calls[0]?.[0]).toBe("/api/scene/p1");
  });

  it("params 拼接后仍无双前缀（查询串保序）", async () => {
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
      params: { condition_key: "design" },
    });
    expect(mock.mock.calls[0]?.[0]).toBe("/api/scene/p1?condition_key=design");
  });

  it("undefined 可选参数不进查询串（condition_key 缺省=服务端排序首键）", async () => {
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
      params: { condition_key: undefined },
    });
    expect(mock.mock.calls[0]?.[0]).toBe("/api/scene/p1");
  });
});

describe("customInstance 错误归一（M3 对称面）", () => {
  it("非 2xx：code=服务端 error_type，message=统一错误体 detail", async () => {
    stubFetch(
      new Response(
        JSON.stringify({ detail: "项目 'x' 不存在", error_type: "ProjectNotFoundError" }),
        { status: 404 },
      ),
    );
    const caught = await customInstance<unknown>({
      url: "/api/scene/x",
      method: "GET",
    }).then(
      () => null,
      (error: unknown) => error,
    );
    expect(caught).toBeInstanceOf(WaterprintApiError);
    const apiError = caught as WaterprintApiError;
    expect(apiError.code).toBe("ProjectNotFoundError");
    expect(apiError.message).toContain("项目 'x' 不存在");
    expect(apiError.detail).toBeDefined();
  });

  it("非 2xx 无 JSON 体：code=HTTP_<status> 兜底（网关页等）", async () => {
    stubFetch(new Response("Bad Gateway", { status: 502 }));
    const caught = await customInstance<unknown>({
      url: "/api/scene/x",
      method: "GET",
    }).then(
      () => null,
      (error: unknown) => error,
    );
    expect(caught).toBeInstanceOf(WaterprintApiError);
    expect((caught as WaterprintApiError).code).toBe("HTTP_502");
  });

  it("2xx 非 JSON 体：归一 WaterprintApiError（成功路径解析失败面——M3）", async () => {
    stubFetch(
      new Response("<html>not json</html>", {
        status: 200,
        headers: { "content-type": "text/html" },
      }),
    );
    const caught = await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
    }).then(
      () => null,
      (error: unknown) => error,
    );
    expect(caught).toBeInstanceOf(WaterprintApiError);
    const apiError = caught as WaterprintApiError;
    expect(apiError.code).toMatch(/^HTTP_200/);
    expect(apiError.message).toContain("解析失败");
  });

  it("空体 2xx → undefined（204 语义）", async () => {
    stubFetch(new Response(null, { status: 204 }));
    await expect(
      customInstance<unknown>({ url: "/api/projects", method: "PUT" }),
    ).resolves.toBeUndefined();
  });
});

describe("token 存取（R2-A 批2 D1——localStorage 三函数+node 守卫）", () => {
  it("node 无 localStorage：getApiToken → null（undefined 视同未配置）", () => {
    expect(getApiToken()).toBeNull();
  });

  it("set/get/clear 往返：单键 waterprint.api_token（命名空间防碰撞）", () => {
    const store = stubLocalStorage();
    expect(getApiToken()).toBeNull(); // 空态=未配置
    setApiToken("t-abc-123");
    expect(store.get("waterprint.api_token")).toBe("t-abc-123");
    expect(getApiToken()).toBe("t-abc-123");
    clearApiToken();
    expect(store.has("waterprint.api_token")).toBe(false);
    expect(getApiToken()).toBeNull();
  });

  it("node 无 localStorage：set/clear 不抛（守卫静默缺省）", () => {
    expect(() => setApiToken("t")).not.toThrow();
    expect(() => clearApiToken()).not.toThrow();
  });
});

describe("Bearer 注入（R2-A 批2 D3——token 空=零注入零行为变化）", () => {
  it("token 空：请求零 Authorization 头（缺省态防回归锁）", async () => {
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({ url: "/api/scene/p1", method: "GET" });
    expect(sentHeaders(mock).Authorization).toBeUndefined();
  });

  it("token 非空：Authorization: Bearer <token> 注入（同步现读即时生效）", async () => {
    stubLocalStorage();
    setApiToken("secret-token-42");
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({ url: "/api/scene/p1", method: "GET" });
    expect(sentHeaders(mock).Authorization).toBe("Bearer secret-token-42");
  });

  it("清除后请求回落零注入（clearApiToken 即时生效面）", async () => {
    stubLocalStorage();
    setApiToken("secret-token-42");
    clearApiToken();
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({ url: "/api/scene/p1", method: "GET" });
    expect(sentHeaders(mock).Authorization).toBeUndefined();
  });

  it("JSON 体请求：Bearer 与 Content-Type 共存（headers 面合并不互斥）", async () => {
    stubLocalStorage();
    setApiToken("t-json");
    const mock = stubFetch(new Response("{}", { status: 200 }));
    await customInstance<unknown>({
      url: "/api/projects",
      method: "POST",
      data: { name: "p" },
    });
    expect(sentHeaders(mock).Authorization).toBe("Bearer t-json");
    expect(sentHeaders(mock)["Content-Type"]).toBe("application/json");
  });
});

describe("401 → AUTH_EVENT 派发（R2-A 批2 D4——先通知再归一化 throw）", () => {
  it("401：先派发 wp:auth 再抛 WaterprintApiError（次序锁 R 轮 G1-04——dispatch 先于 throw）", async () => {
    // 时序标记（G1-04）：派发 mock push "dispatch"、rejection 捕获 push
    // "throw"——次序断言锁 D4「先派发再归一化 throw」核心语义（非仅各自存在）
    const order: string[] = [];
    const dispatchEvent = vi.fn((_event: CustomEvent): boolean => {
      order.push("dispatch");
      return true;
    });
    vi.stubGlobal("window", { dispatchEvent });
    stubFetch(
      new Response(JSON.stringify({ detail: "token 缺失或不符", error_type: "AuthError" }), {
        status: 401,
      }),
    );
    const caught = await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
    }).then(
      () => null,
      (error: unknown) => {
        order.push("throw");
        return error;
      },
    );
    expect(order).toEqual(["dispatch", "throw"]); // 次序锁：派发先于 throw
    expect(dispatchEvent).toHaveBeenCalledOnce();
    const event = dispatchEvent.mock.calls[0]?.[0] as CustomEvent;
    expect(event.type).toBe(AUTH_EVENT);
    expect(event.type).toBe("wp:auth");
    expect(caught).toBeInstanceOf(WaterprintApiError);
    expect((caught as WaterprintApiError).code).toBe("AuthError");
    expect((caught as WaterprintApiError).message).toContain("token 缺失或不符");
  });

  it("非 401（502）：零 AUTH_EVENT 派发（通知面不扩大）", async () => {
    const dispatchEvent = stubWindow();
    stubFetch(new Response("Bad Gateway", { status: 502 }));
    // 归一化 throw 语义既有——本例只断言零派发（拒绝面吞掉）
    await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
    }).catch(() => undefined);
    expect(dispatchEvent).not.toHaveBeenCalled();
  });

  it("node 无 window：401 归一化 throw 正常、零派发不崩（守卫面）", async () => {
    stubFetch(new Response("Unauthorized", { status: 401 }));
    const caught = await customInstance<unknown>({
      url: "/api/scene/p1",
      method: "GET",
    }).then(
      () => null,
      (error: unknown) => error,
    );
    expect(caught).toBeInstanceOf(WaterprintApiError);
    expect((caught as WaterprintApiError).code).toBe("HTTP_401");
  });
});
