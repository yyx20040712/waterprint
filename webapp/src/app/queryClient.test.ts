/**
 * app 地基纯函数单测：queryClient retry 策略（D3 领域错误口径）+
 * errorReportPayload 上报结构（D4 结构化日志最小面）。
 *
 * 输入:  queryClient.ts（retryPolicy/createQueryClient）与 ErrorBoundary.tsx
 *        的 errorReportPayload（node 环境——零 DOM 依赖直测纯函数）
 * 输出:  断言：领域错误任意 count 不重试/网络族重试恰 1 次/默认项
 *        staleTime 0+refetchOnWindowFocus false/上报恰四字段/缺 stack 容错
 *
 * 规格说明（FE3 批 6b 段一，D6-①③）：
 *   - D3 retry 口径：WaterprintApiError=服务端已组织错误体（4xx 主集合，
 *     含 404 无结果集指引/422 校验）重试无益一律不重试；非领域错误
 *     （TypeError 网络族等）最多重试 1 次（count<1）——规格头原措辞
 *     "retry 1（4xx 不重试）"按领域错误口径实现的差异记档；
 *   - errorReportPayload 组与 queryClient 组同住本文件：白名单恰 11 文件
 *     限定测试文件两件，D6 三组纯函数面在此归置（ErrorBoundary 本体无
 *     独立测试文件——payload 已从类拆出为可直测纯函数）；
 *   - 默认项断言直读 QueryClient.getDefaultOptions()（providers 实装唯一
 *     消费面，组件外模块级单例的工厂即实装面本身）。
 */
import { describe, expect, it } from "vitest";

import { WaterprintApiError } from "../shared/api/http";
import { errorReportPayload } from "./ErrorBoundary";
import { createQueryClient, retryPolicy } from "./queryClient";

describe("retryPolicy（D3 领域错误口径）", () => {
  it("WaterprintApiError 领域错误任意 count 均不重试（404 指引语义立即呈现）", () => {
    const error = new WaterprintApiError(
      "ResultNotFoundError",
      "项目 'x' 无已完成结果集",
    );
    expect(retryPolicy(0, error)).toBe(false);
    expect(retryPolicy(1, error)).toBe(false);
    expect(retryPolicy(2, error)).toBe(false);
  });

  it("非领域错误重试恰 1 次：count 0 放行/count 1 拒绝（TypeError 网络族）", () => {
    expect(retryPolicy(0, new TypeError("Failed to fetch"))).toBe(true);
    expect(retryPolicy(1, new TypeError("Failed to fetch"))).toBe(false);
    expect(retryPolicy(0, new Error("网络中断"))).toBe(true);
    expect(retryPolicy(1, new Error("网络中断"))).toBe(false);
  });

  it("QueryClient 默认项：staleTime 0+refetchOnWindowFocus false+retry=策略函数", () => {
    const defaults = createQueryClient().getDefaultOptions().queries;
    expect(defaults?.staleTime).toBe(0);
    expect(defaults?.refetchOnWindowFocus).toBe(false);
    expect(defaults?.retry).toBe(retryPolicy);
  });
});

describe("errorReportPayload（D4 结构化上报）", () => {
  it("结构恰四字段：feature/message/stack/componentStack（含路由名可反查）", () => {
    const error = new Error("场景投影失败");
    error.stack = "Error: 场景投影失败\n    at Scene";
    const payload = errorReportPayload("三维视图", error, "at Viewer3dPane");
    expect(Object.keys(payload).sort()).toEqual([
      "componentStack",
      "feature",
      "message",
      "stack",
    ]);
    expect(payload.feature).toBe("三维视图");
    expect(payload.message).toBe("场景投影失败");
    expect(payload.stack).toContain("at Scene");
    expect(payload.componentStack).toBe("at Viewer3dPane");
  });

  it("非 Error 输入：message=String(error)、stack/componentStack=null", () => {
    const payload = errorReportPayload("画布", "裸字符串异常", null);
    expect(payload.message).toBe("裸字符串异常");
    expect(payload.stack).toBeNull();
    expect(payload.componentStack).toBeNull();
  });

  it("Error 但 stack 缺失：stack=null 不抛错（缺 stack 容错）", () => {
    const error = new Error("无栈错误");
    error.stack = undefined;
    const payload = errorReportPayload("三维视图", error, null);
    expect(payload.message).toBe("无栈错误");
    expect(payload.stack).toBeNull();
  });
});
