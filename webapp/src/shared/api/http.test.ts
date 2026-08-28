/**
 * http.ts 请求实例单测：路径锁定（C1 双前缀防回归）+错误归一两面（非 2xx/2xx 解析失败）。
 *
 * 输入:  customInstance（mock fetch——node 环境 Response 全局，零真实 HTTP）
 * 输出:  请求路径与错误语义断言（R2 C1/M3 防回归锁）
 *
 * 规格说明（R2 二审闭合）：
 *   - C1（Critical）：orval 生成 url 已含 /api 前缀（openapi path 键面）
 *     ——最终请求路径必须恰 "/api/…" 形态，禁二次前拼（曾致 18 端点全 404）；
 *   - M3：成功路径 2xx 非 JSON 体归一 WaterprintApiError（与非 2xx 路径对称）；
 *   - 服务端统一错误体 {detail, error_type} → code=error_type/message=detail。
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { WaterprintApiError, customInstance } from "./http";

type FetchMock = ReturnType<typeof vi.fn>;

function stubFetch(response: Response): FetchMock {
  const mock = vi.fn(async () => response);
  vi.stubGlobal("fetch", mock);
  return mock;
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
