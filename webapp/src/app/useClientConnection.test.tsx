/**
 * @vitest-environment jsdom
 *
 * 客户端连接 supervisor vitest（联机架构第六批 2026-11-19——单点驱动面：
 * meta 查询态转移+queryCache 401→token_invalid+success 粘性恢复+本地态
 * 零副作用）。
 *
 * 输入:  useClientConnectionSupervisor（生成 meta hook 模块替身受控四态+
 *        真 QueryClient〔fetchQuery 驱动 queryCache success/error 事件〕+
 *        真 clientConnectionStore〔setState 控 remoteBase 初值〕）
 * 输出:  断言四组：①本地态零副作用（meta 查询 disabled+401 事件不写
 *        状态——单机面零行为变）②meta 查询态四转移（pending→connecting/
 *        error→offline/data 匹配→online/data 不匹配→version_mismatch
 *        携明细）③queryCache error 且 AuthError/HTTP_401→token_invalid
 *        （非鉴权错不转）④token_invalid 后曾 401 查询 success→复核
 *        serverMeta 回 online（豁免端点 success 不恢复——粘性不悬挂）
 */
import { act, cleanup, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { MetaInfo } from "../shared/api/generated/model";
import { WaterprintApiError } from "../shared/api/http";
import { EXPECTED_API_VERSION, EXPECTED_DATA_VERSION } from "../shared/api/clientProtocol";
import { useClientConnectionStore } from "./clientConnectionStore";
import { useClientConnectionSupervisor } from "./useClientConnection";

const MATCHED_META: MetaInfo = {
  app_version: "waterprint-server 0.1.0",
  data_version: EXPECTED_DATA_VERSION,
  api_version: EXPECTED_API_VERSION,
};

/** meta 查询替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  status: "pending" as "pending" | "error" | "data",
  data: undefined as MetaInfo | undefined,
  lastEnabled: true,
}));

vi.mock("../shared/api/generated/meta/meta", () => ({
  useGetMetaApiMetaGet: (opts?: { query?: { enabled?: boolean } }) => {
    gate.lastEnabled = opts?.query?.enabled ?? true;
    return {
      isPending: gate.status === "pending",
      isError: gate.status === "error",
      data: gate.status === "data" ? gate.data : undefined,
      error: null,
    };
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function mountSupervisor() {
  return renderHook(() => useClientConnectionSupervisor(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

/** queryCache 驱动助手（fetchQuery 产 success/error updated 事件）。 */
async function driveQuery(
  key: string,
  fn: () => Promise<unknown>,
): Promise<void> {
  await queryClient.fetchQuery({ queryKey: [key], queryFn: fn }).catch(() => "err");
}

beforeEach(() => {
  gate.status = "pending";
  gate.data = undefined;
  gate.lastEnabled = true;
  useClientConnectionStore.setState({
    phase: "local",
    remoteBase: null,
    serverMeta: null,
    mismatch: null,
  });
});

afterEach(() => {
  cleanup();
  queryClient.clear();
});

describe("useClientConnectionSupervisor（客户端连接驱动面——联机第六批）", () => {
  it("本地态零副作用：meta 查询 disabled+401 事件不写状态（单机零行为变）", async () => {
    mountSupervisor();
    expect(gate.lastEnabled).toBe(false); // remoteBase null → disabled 零请求
    await driveQuery("local-401", () =>
      Promise.reject(new WaterprintApiError("AuthError", "unauthorized")),
    );
    const state = useClientConnectionStore.getState();
    expect(state.phase).toBe("local"); // 两 effect 早退——零状态写入
    expect(state.serverMeta).toBeNull();
  });

  it("meta 查询态四转移：pending→connecting/error→offline/匹配→online/不匹配→version_mismatch", () => {
    act(() => {
      useClientConnectionStore.setState({ remoteBase: "http://127.0.0.1:8100" });
    });
    const { rerender } = mountSupervisor();
    expect(useClientConnectionStore.getState().phase).toBe("connecting");
    gate.status = "error";
    rerender();
    expect(useClientConnectionStore.getState().phase).toBe("offline");
    gate.status = "data";
    gate.data = MATCHED_META;
    rerender();
    expect(useClientConnectionStore.getState()).toMatchObject({
      phase: "online",
      serverMeta: MATCHED_META,
      mismatch: null,
    });
    gate.data = { ...MATCHED_META, api_version: "9.9" };
    rerender();
    expect(useClientConnectionStore.getState()).toMatchObject({
      phase: "version_mismatch",
      mismatch: { kind: "api", expected: EXPECTED_API_VERSION, actual: "9.9" },
    });
  });

  it("queryCache error AuthError→token_invalid；非鉴权错不转（HTTP_500 留 online）", async () => {
    act(() => {
      useClientConnectionStore.setState({ remoteBase: "http://127.0.0.1:8100" });
    });
    gate.status = "data";
    gate.data = MATCHED_META;
    mountSupervisor();
    expect(useClientConnectionStore.getState().phase).toBe("online");
    await driveQuery("auth-401", () =>
      Promise.reject(new WaterprintApiError("AuthError", "unauthorized")),
    );
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // 兜底码面：非统一错误体网关 401（HTTP_401）同转
    act(() => {
      useClientConnectionStore.setState({ phase: "online" });
    });
    await driveQuery("auth-401b", () =>
      Promise.reject(new WaterprintApiError("HTTP_401", "unauthorized")),
    );
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // 非鉴权错不转 token_invalid
    act(() => {
      useClientConnectionStore.setState({ phase: "online" });
    });
    await driveQuery("server-500", () =>
      Promise.reject(new WaterprintApiError("HTTP_500", "boom")),
    );
    expect(useClientConnectionStore.getState().phase).toBe("online");
  });

  it("token_invalid 后曾 401 查询 success→复核 serverMeta 回 online（粘性恢复）；豁免端点 success 不恢复", async () => {
    act(() => {
      useClientConnectionStore.setState({ remoteBase: "http://127.0.0.1:8100" });
    });
    gate.status = "data";
    gate.data = MATCHED_META;
    mountSupervisor();
    await driveQuery("auth-x", () =>
      Promise.reject(new WaterprintApiError("AuthError", "unauthorized")),
    );
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // 豁免端点（units/meta 等——无 token 也 200）的 success 不抵消凭据失效
    await driveQuery("public-units", async () => []);
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // 曾 401 的同一查询键成功=凭据修复证据——复核 serverMeta 恢复 online
    await driveQuery("auth-x", async () => "数据面恢复");
    const state = useClientConnectionStore.getState();
    expect(state.phase).toBe("online"); // serverMeta 复核通过即恢复
    expect(state.serverMeta).toEqual(MATCHED_META);
  });

  it("meta 迟到/后台重取不清 token_invalid（401 后 meta data 到场仍粘性）", async () => {
    act(() => {
      useClientConnectionStore.setState({ remoteBase: "http://127.0.0.1:8100" });
    });
    // meta 尚在途（pending）——受保面先 401
    const { rerender } = mountSupervisor();
    await driveQuery("auth-late", () =>
      Promise.reject(new WaterprintApiError("AuthError", "unauthorized")),
    );
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // meta 数据随后到达（网络次序翻转）——不得清凭据失效态
    gate.status = "data";
    gate.data = MATCHED_META;
    rerender();
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
    // 后台重取（pending 再临）同样粘性
    gate.status = "pending";
    rerender();
    expect(useClientConnectionStore.getState().phase).toBe("token_invalid");
  });
});
