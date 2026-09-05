/**
 * 产物导出可测核测试：exportArtifact Bearer 条件注入（B3 D 件授权回修
 * ——POST fetch headers 面）。
 *
 * 输入:  useExportArtifact 导出面 exportArtifact（fetch stub——错误路响应
 *        409+JSON 错误体：fetch 已携 headers 且导出抛 WaterprintApiError，
 *        断言全程零 DOM 依赖）
 * 输出:  Bearer 两例（token 非空→Authorization 携带/未配置→不携带不发
 *        空头——useExportDownload.test.ts:82-99 同款断言形态）
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { WaterprintApiError } from "../../../shared/api/http";
import { exportArtifact } from "./useExportArtifact";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** fetch 替身类型（useExportDownload.test 同款——calls 索引面宽松形态）。 */
type FetchMock = ReturnType<typeof vi.fn>;

/** token 存根（getApiToken→localStorage 真源：node 环境无原生——非空注入面）。 */
function stubToken(token: string): void {
  vi.stubGlobal("localStorage", {
    getItem: () => token,
    setItem: vi.fn(),
    removeItem: vi.fn(),
  });
}

/** 错误路 fetch 存根（409 stale 错误体——fetch 调用形态已定且导出抛错，零 DOM 面）。 */
function stubStaleFetch(): FetchMock {
  const mock: FetchMock = vi.fn(
    async () =>
      new Response(
        JSON.stringify({ detail: "结果已过期", error_type: "StaleExportError" }),
        { status: 409 },
      ),
  );
  vi.stubGlobal("fetch", mock);
  return mock;
}

const INPUT = { projectId: "p1", unitId: "u1", conditionKey: "design" };

describe("exportArtifact Bearer 条件注入（B3 D 件）", () => {
  it("token 非空 → Authorization 头携带（Content-Type 并存）", async () => {
    stubToken("tok-1234567890abcdef");
    const mock = stubStaleFetch();
    await expect(exportArtifact("dxf", INPUT)).rejects.toBeInstanceOf(
      WaterprintApiError,
    );
    expect(mock.mock.calls[0]?.[0]).toBe("/api/exports/dxf");
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer tok-1234567890abcdef");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("空态不注入：token 未配置 → 无 Authorization 头（不发空头）", async () => {
    const mock = stubStaleFetch();
    await expect(exportArtifact("dxf", INPUT)).rejects.toBeInstanceOf(
      WaterprintApiError,
    );
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBeNull(); // 空头不发送（auth.py 行为未冻结面）
    expect(headers.get("Content-Type")).toBe("application/json");
  });
});
