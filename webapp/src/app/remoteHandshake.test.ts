/**
 * 远程握手探测 vitest（联机架构第六批 2026-11-19——node 直测：版本比对
 * 纯函数+performHandshake fetch 替身四态）。
 *
 * 输入:  remoteHandshake（compareServerVersions/performHandshake——
 *        fetch 全局替身受控：meta/projects 两探测面）
 * 输出:  断言三组：①版本比对（全等放行/api 先判/data 后判+双方值并陈）
 *        ②探测四态（ok/token_invalid/version_mismatch/unreachable——
 *        401 面、网络抛、非 2xx、载荷畸形）③探测请求面（Bearer 通道/
 *        匿名零头——与运行期 http.ts 同通道）
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  EXPECTED_API_VERSION,
  EXPECTED_DATA_VERSION,
} from "../shared/api/clientProtocol";
import type { MetaInfo } from "../shared/api/generated/model";
import { compareServerVersions, performHandshake } from "./remoteHandshake";

const MATCHED_META: MetaInfo = {
  app_version: "waterprint-server 0.1.0",
  data_version: EXPECTED_DATA_VERSION,
  api_version: EXPECTED_API_VERSION,
};

/** JSON Response 替身。 */
function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("compareServerVersions（版本比对纯函数——联机第六批）", () => {
  it("全等放行（api+data 同期望）", () => {
    expect(compareServerVersions(MATCHED_META)).toEqual({ ok: true });
  });

  it("api 不匹配先判（data 同改不遮蔽——api 契约面优先呈报）", () => {
    const result = compareServerVersions({
      ...MATCHED_META,
      api_version: "2.0",
      data_version: "other@9",
    });
    expect(result).toEqual({
      ok: false,
      kind: "api",
      expected: EXPECTED_API_VERSION,
      actual: "2.0",
    });
  });

  it("data 不匹配后判（三包聚合串整串比对+双方值并陈）", () => {
    const result = compareServerVersions({
      ...MATCHED_META,
      data_version: "assumptions@1.0.0+coefficients@1.9.0+unit_prices@1.2.0",
    });
    expect(result).toEqual({
      ok: false,
      kind: "data",
      expected: EXPECTED_DATA_VERSION,
      actual: "assumptions@1.0.0+coefficients@1.9.0+unit_prices@1.2.0",
    });
  });
});

describe("performHandshake（探测四态——fetch 替身）", () => {
  it("ok：meta 全等+projects 200 带 Bearer 通道", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/meta")) {
        return jsonResponse(200, MATCHED_META);
      }
      expect(init?.headers).toEqual({ Authorization: "Bearer tok-1234567890" });
      return jsonResponse(200, []);
    });
    vi.stubGlobal("fetch", fetchMock);
    const outcome = await performHandshake("http://127.0.0.1:8100", "tok-1234567890");
    expect(outcome).toEqual({ status: "ok", meta: MATCHED_META });
  });

  it("token_invalid：projects 探针 401（凭据先于版本判）", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string | URL) =>
        String(input).endsWith("/api/meta")
          ? jsonResponse(200, MATCHED_META)
          : jsonResponse(401, { detail: "unauthorized", error_type: "AuthError" }),
      ),
    );
    expect(await performHandshake("http://h", "bad-token")).toEqual({
      status: "token_invalid",
    });
  });

  it("version_mismatch：token 过+版本不匹配（meta 随结果并陈）", async () => {
    const mismatched = { ...MATCHED_META, api_version: "9.9" };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(200, mismatched)),
    );
    const outcome = await performHandshake("http://h", "tok");
    expect(outcome.status).toBe("version_mismatch");
    if (outcome.status === "version_mismatch") {
      expect(outcome.check.kind).toBe("api");
      expect(outcome.meta.api_version).toBe("9.9");
    }
  });

  it("unreachable 三面：meta 网络抛/projects 网络抛/meta 载荷畸形", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    expect(await performHandshake("http://h", "t")).toEqual({
      status: "unreachable",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string | URL) =>
        String(input).endsWith("/api/meta")
          ? jsonResponse(200, MATCHED_META)
          : Promise.reject(new TypeError("network dropped")),
      ),
    );
    expect(await performHandshake("http://h", "t")).toEqual({
      status: "unreachable",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string | URL) =>
        String(input).endsWith("/api/meta")
          ? jsonResponse(200, { hello: "not waterprint" })
          : jsonResponse(200, []),
      ),
    );
    expect(await performHandshake("http://h", "t")).toEqual({
      status: "unreachable",
    });
  });

  it("匿名探测：token 空=零 Authorization 头（远程 standalone 可过）", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/meta")) {
        return jsonResponse(200, MATCHED_META);
      }
      expect(init?.headers).toBeUndefined();
      return jsonResponse(200, []);
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await performHandshake("http://h", "  ")).toEqual({
      status: "ok",
      meta: MATCHED_META,
    });
  });
});
