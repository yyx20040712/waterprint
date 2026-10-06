/**
 * @vitest-environment jsdom
 *
 * ErrorBoundary 错误分级降级面测试（2B5 批 UF-65 范式件——三分级/库言
 * 词典/诊断详情折叠/重试复位语义）。
 *
 * 输入:  ErrorBoundary+崩溃子组件（jsdom 直渲——@testing-library 既有
 *        栈）+gradeClientError 纯函数直测（同文件导出面）
 * 输出:  断言组：①三分级分支（chunk/词典命中/未知——固定摘要文案+非
 *        Error 归一）；②词典模式匹配（正则族子串命中+分级序 chunk 先
 *        于词典）；③折叠结构（raw 不在主面文本+details 在场默认收起）；
 *        ④重试语义（onRetry 转调恰一次+hasError 复位子树重挂载；无
 *        onRetry 同复位）；⑤label 透出+role=alert 保持。
 *
 * 规格说明（2B5 brief D2/D3/D4/D7）：
 *   - 纯函数组（queryClient.test.ts errorReportPayload 既有组零弱化——
 *     上报语义面由该组守卫，本文件只测降级呈现面）；
 *   - 主面=「面板异常（{label}）」+分级摘要+重试钮；raw message/
 *     componentStack 只进原生 details（默认收起，零新依赖）；
 *   - 重试钮语义沿 L84-90 注记口径：onRetry 在场先转调（同一事件批内）
 *     +setState 复位 hasError——子树重挂载（React.lazy 重建先例面）。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ErrorBoundary, gradeClientError } from "./ErrorBoundary";

/** 一次性崩溃子组件（render 期抛出——归一管道组件面实证；显式返回
 *  类型注解=无条件 throw 分支的 void 推断不合 JSX 元件类型）。 */
function Boom({ error }: { error: unknown }): ReactNode {
  throw error;
}

/** 主面文本（剥离 details 子树后——raw 只应存在于诊断折叠区）。 */
function faceWithoutDetails(): string {
  const alert = screen.getByRole("alert");
  const clone = alert.cloneNode(true) as HTMLElement;
  clone.querySelector("details")?.remove();
  return clone.textContent ?? "";
}

describe("gradeClientError 纯函数（D2 三分级+D3 词典）", () => {
  it("chunk 级：动态模块加载失败族三消息→固定摘要（D2 分支①）", () => {
    const summary = "页面模块加载失败——多为网络中断或系统刚更新所致，请重试";
    for (const message of [
      "Loading chunk 12 failed.",
      "Failed to fetch dynamically imported module: http://x/elevationPane.js",
      "Importing a module script failed.",
    ]) {
      const graded = gradeClientError(new Error(message));
      expect(graded.grade).toBe("chunk");
      expect(graded.summary).toBe(summary);
      expect(graded.detail).toBe(message);
    }
  });

  it("词典命中：Minified React error→「界面组件内部错误，请重试」", () => {
    const message =
      "Minified React error #418; visit https://react.dev/errors/418 for full messages.";
    const graded = gradeClientError(new Error(message));
    expect(graded.grade).toBe("dictionary");
    expect(graded.summary).toBe("界面组件内部错误，请重试");
    expect(graded.detail).toBe(message);
  });

  it("词典命中：THREE.WebGLRenderer→「三维渲染环境不可用（显卡/浏览器支持不足）」（M5 前置种子）", () => {
    const message = "THREE.WebGLRenderer: Error creating WebGL context.";
    const graded = gradeClientError(new Error(message));
    expect(graded.grade).toBe("dictionary");
    expect(graded.summary).toBe("三维渲染环境不可用（显卡/浏览器支持不足）");
  });

  it("词典模式匹配=正则子串命中（非全等——长消息内嵌词条亦命中）", () => {
    const graded = gradeClientError(
      new Error("渲染初始化失败：THREE.WebGLRenderer: Error creating WebGL context.（附上下文）"),
    );
    expect(graded.grade).toBe("dictionary");
    expect(graded.summary).toBe("三维渲染环境不可用（显卡/浏览器支持不足）");
  });

  it("未知级：未命中族/词典→兜底摘要（D2 分支③）", () => {
    const graded = gradeClientError(new Error("某处Unexpected崩溃"));
    expect(graded.grade).toBe("unknown");
    expect(graded.summary).toBe(
      "面板发生未预期错误，请重试；若持续出现请展开诊断详情反馈",
    );
    expect(graded.detail).toBe("某处Unexpected崩溃");
  });

  it("非 Error 归一：String(error) 进 detail 同管道（「未知错误」口径沿 errorReportPayload）", () => {
    const graded = gradeClientError("裸字符串异常");
    expect(graded.grade).toBe("unknown");
    expect(graded.detail).toBe("裸字符串异常");
  });

  it("分级序：chunk 族先于词典（消息双命中时归 chunk 级——D2 ①→②→③ 序）", () => {
    const graded = gradeClientError(
      new Error("Importing a module script failed.（THREE.WebGLRenderer 预热段）"),
    );
    expect(graded.grade).toBe("chunk");
  });
});

describe("ErrorBoundary 降级面（jsdom——D4 主面+折叠）", () => {
  afterEach(cleanup);

  it("chunk 级崩溃：主面=面板异常（label）+固定摘要；role=alert 保持", () => {
    render(
      <ErrorBoundary label="高程纵断">
        <Boom error={new Error("Loading chunk 7 failed.")} />
      </ErrorBoundary>,
    );
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("面板异常（高程纵断）");
    expect(
      screen.getByText("页面模块加载失败——多为网络中断或系统刚更新所致，请重试"),
    ).toBeTruthy();
  });

  it("词典级崩溃：Minified React error 摘要在场", () => {
    render(
      <ErrorBoundary label="研究">
        <Boom error={new Error("Minified React error #152; visit https://react.dev/…")} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("界面组件内部错误，请重试")).toBeTruthy();
  });

  it("未知级崩溃：兜底摘要在场", () => {
    render(
      <ErrorBoundary label="三维视图">
        <Boom error={new Error("totally unexpected kaboom")} />
      </ErrorBoundary>,
    );
    expect(
      screen.getByText("面板发生未预期错误，请重试；若持续出现请展开诊断详情反馈"),
    ).toBeTruthy();
  });

  it("label 透出：主面前缀逐字含 label", () => {
    render(
      <ErrorBoundary label="厂区布置">
        <Boom error={new Error("x")} />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("alert").textContent).toContain("面板异常（厂区布置）");
  });

  it("折叠结构：details 在场+默认收起；raw message 不在主面文本（只在诊断区）", () => {
    const raw = "THREE.WebGLRenderer: Error creating WebGL context.";
    const { container } = render(
      <ErrorBoundary label="三维视图">
        <Boom error={new Error(raw)} />
      </ErrorBoundary>,
    );
    const details = container.querySelector("details");
    expect(details).toBeTruthy();
    expect((details as HTMLDetailsElement).open).toBe(false);
    expect(details?.textContent).toContain("诊断详情");
    expect(details?.textContent).toContain(raw);
    expect(faceWithoutDetails()).not.toContain(raw);
  });

  it("非 Error 抛出（裸字符串）：归一进诊断区+未知级摘要", () => {
    const { container } = render(
      <ErrorBoundary label="画布">
        <Boom error="裸字符串异常" />
      </ErrorBoundary>,
    );
    expect(
      screen.getByText("面板发生未预期错误，请重试；若持续出现请展开诊断详情反馈"),
    ).toBeTruthy();
    expect(container.querySelector("details")?.textContent).toContain("裸字符串异常");
  });
});

describe("ErrorBoundary 重试语义（R1 口径——onRetry 转调+复位）", () => {
  afterEach(cleanup);

  it("onRetry 在场：转调恰一次+hasError 复位子树重挂载（恢复后 fallback 退场）", () => {
    let detonate = true;
    function Fickle() {
      if (detonate) {
        throw new Error("Loading chunk 9 failed.");
      }
      return <div role="status">已恢复</div>;
    }
    const onRetry = vi.fn();
    render(
      <ErrorBoundary label="高程纵断" onRetry={onRetry}>
        <Fickle />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("alert")).toBeTruthy();
    detonate = false;
    fireEvent.click(screen.getByRole("button", { name: "重试" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("status").textContent).toBe("已恢复");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("onRetry 缺场：复位 hasError 维持（子树重挂载——不转调不抛错）", () => {
    let detonate = true;
    function Fickle() {
      if (detonate) {
        throw new Error("Minified React error #185");
      }
      return <div role="status">已恢复</div>;
    }
    render(
      <ErrorBoundary label="研究">
        <Fickle />
      </ErrorBoundary>,
    );
    detonate = false;
    fireEvent.click(screen.getByRole("button", { name: "重试" }));
    expect(screen.getByRole("status").textContent).toBe("已恢复");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
