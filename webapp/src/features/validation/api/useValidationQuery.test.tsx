/**
 * @vitest-environment jsdom
 *
 * useValidationQuery 封装绑定测试（T3 回炉顺手项——接线测试 mock 整个
 * hook 模块，未覆盖封装内真实 select=narrowValidationObservation 绑定；
 * 本件仅替身取数面 customInstance，orval hook+select 走真路径）。
 *
 * 输入:  useValidationQuery +customInstance 替身（受控响应体——合法/非法
 *        两态）+每用例独立 QueryClientProvider wrapper
 * 输出:  断言族：①合法响应→data=窄化产物（真 select 收口字段面）②非法
 *        形状〔warnings 含 null 行〕→查询 error 态=ValidationViewError
 *        （禁 data 带病）③projectId=null=禁用零取数（enabled 守卫——
 *        customInstance 调用计数为 0）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ValidationViewError } from "../lib/validationView";
import { useValidationQuery } from "./useValidationQuery";

/** 取数面替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const fetchGate = vi.hoisted(() => ({
  response: undefined as unknown,
  calls: 0,
}));

vi.mock("../../../shared/api/http", () => ({
  // 仅替身取数面：url/init 不消费（断言面=调用计数+响应体投影）
  customInstance: async () => {
    fetchGate.calls += 1;
    return fetchGate.response;
  },
}));

/** 合法响应体（顶层 11 键+单聚合行——服务端冻结 schema 形）。 */
const HEALTHY_RESPONSE = {
  project_id: "p1",
  task_id: "t1",
  stale: false,
  design_hash: "h1",
  engine_version: "e1",
  data_version: "d1",
  kb_injected: null,
  validation_available: true,
  conditions: ["avg", "design"],
  nodes: [],
  warnings: [
    {
      code: "kb.aao.n_band",
      param_key: "n",
      scope: "municipal_aao",
      message: "N=28 越门：kb.aao.n_band——n 违反 n<=25",
      condition_keys: ["avg", "design"],
      severity: "ERROR",
    },
  ],
};

/** 独立 wrapper（每用例新 QueryClient——键缓存零串扰）。 */
function wrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  fetchGate.response = undefined;
  fetchGate.calls = 0;
});

describe("useValidationQuery 封装绑定（真 select 路径）", () => {
  it("合法响应→data=窄化产物（select=narrowValidationObservation 真绑定）", async () => {
    fetchGate.response = HEALTHY_RESPONSE;
    const { result } = renderHook(() => useValidationQuery("p1"), {
      wrapper: wrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.validation_available).toBe(true);
    expect(result.current.data?.warnings).toHaveLength(1);
    expect(result.current.data?.warnings[0]?.condition_keys).toEqual([
      "avg",
      "design",
    ]);
    expect(fetchGate.calls).toBe(1); // 单键单取数
  });

  it("非法形状→查询 error 态=ValidationViewError（非 data 带病）", async () => {
    fetchGate.response = { ...HEALTHY_RESPONSE, warnings: [null] };
    const { result } = renderHook(() => useValidationQuery("p1"), {
      wrapper: wrapper(),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ValidationViewError);
    expect(result.current.error?.message).toContain("warnings[0]");
    expect(result.current.data).toBeUndefined();
  });

  it("projectId=null=禁用零取数（enabled 守卫——空态省请求）", async () => {
    fetchGate.response = HEALTHY_RESPONSE;
    const { result } = renderHook(() => useValidationQuery(null), {
      wrapper: wrapper(),
    });
    // 禁用态：pending（未取数）且 customInstance 零调用
    expect(result.current.isPending).toBe(true);
    expect(fetchGate.calls).toBe(0);
  });
});
