/**
 * 产物下载 hook 可测核测试：fetchExportFile（手写 fetch GET——node 环境
 * 零 DOM 红线，断言面=返回值与 fetch 调用形态；saveBlob DOM 薄壳不测
 * 〔总控修正②，Kimi D5① anchor 断言不可行——vitest 全套 node 环境〕）。
 *
 * 输入:  useExportDownload 导出面 fetchExportFile（fetch stub）
 * 输出:  六面断言（EXPD 简报 DoD 6：成功/非 2xx/Bearer 注入/空态不注入/
 *        文件名编码/网络错——先红后绿：module 未建=import 解析红）
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { WaterprintApiError } from "../../../shared/api/http";
import { fetchExportFile } from "./useExportDownload";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** fetch 替身类型（useExportBatch.test 同款——calls 索引面宽松形态）。 */
type FetchMock = ReturnType<typeof vi.fn>;

/** token 存根（getApiToken→localStorage 真源：node 环境无原生——非空注入面）。 */
function stubToken(token: string): void {
  vi.stubGlobal("localStorage", {
    getItem: () => token,
    setItem: vi.fn(),
    removeItem: vi.fn(),
  });
}

describe("fetchExportFile 下载可测核", () => {
  it("成功：GET 形态+blob 返回+Content-Disposition 文件名优先（缺省回落入参）", async () => {
    const payload = "DXF-BYTES";
    const mock: FetchMock = vi.fn(
      async () =>
        new Response(payload, {
          status: 200,
          headers: {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'attachment; filename="p1-dxf-design-0123456789.dxf"',
          },
        }),
    );
    vi.stubGlobal("fetch", mock);
    const artifact = await fetchExportFile("p1-dxf-design-aaaaaaaaaa.dxf");
    expect(mock.mock.calls[0]?.[0]).toBe("/api/exports/p1-dxf-design-aaaaaaaaaa.dxf");
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("GET");
    expect(await artifact.blob.text()).toBe(payload);
    expect(artifact.fileName).toBe("p1-dxf-design-0123456789.dxf"); // 服务端文件名真源
    // 缺省面：无 Content-Disposition → ?? fileName 兜底
    vi.stubGlobal("fetch", vi.fn(async () => new Response("x", { status: 200 })));
    const fallback = await fetchExportFile("p1-ifc-design-0123456789.ifc");
    expect(fallback.fileName).toBe("p1-ifc-design-0123456789.ifc");
  });

  it("非 2xx：统一错误体 → WaterprintApiError（code=error_type）", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: "导出产物不存在：'p1-dxf-c-0123456789.dxf'（不在册）",
              error_type: "ExportFileNotFoundError",
            }),
            { status: 404 },
          ),
      ),
    );
    let caught: unknown = null;
    try {
      await fetchExportFile("p1-dxf-c-0123456789.dxf");
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(WaterprintApiError);
    expect((caught as WaterprintApiError).code).toBe("ExportFileNotFoundError");
    expect((caught as WaterprintApiError).message).toContain("不在册");
  });

  it("Bearer 注入：token 非空 → Authorization 头携带", async () => {
    stubToken("tok-1234567890abcdef");
    const mock: FetchMock = vi.fn(async () => new Response("x", { status: 200 }));
    vi.stubGlobal("fetch", mock);
    await fetchExportFile("p1-dxf-design-0123456789.dxf");
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer tok-1234567890abcdef");
  });

  it("空态不注入：token 未配置 → 无 Authorization 头（不发空头）", async () => {
    const mock: FetchMock = vi.fn(async () => new Response("x", { status: 200 }));
    vi.stubGlobal("fetch", mock);
    await fetchExportFile("p1-dxf-design-0123456789.dxf");
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBeNull(); // 空头不发送（auth.py 行为未冻结面）
  });

  it("文件名编码：特殊字符 → encodeURIComponent 路径段", async () => {
    const mock: FetchMock = vi.fn(async () => new Response("x", { status: 200 }));
    vi.stubGlobal("fetch", mock);
    await fetchExportFile("p 1+dxf.dxf");
    expect(mock.mock.calls[0]?.[0]).toBe("/api/exports/p%201%2Bdxf.dxf");
  });

  it("网络错：fetch 拒绝原样上抛（不吞不饰）", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    await expect(fetchExportFile("p1-dxf-design-0123456789.dxf")).rejects.toThrow(
      "fetch failed",
    );
  });
});
