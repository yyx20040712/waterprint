/**
 * TaskPanel connection 提示行测试（B7 D4）：两态 warning 文案渲染+ok/null/
 * 缺省零渲染。
 *
 * 输入:  TaskPanel（taskId/view/status/statusError 必需面+connection 提示面）
 * 输出:  reconnecting=「连接中断，自动重连中…」/probing=「连接中断，每 60
 *        秒重试一次…」行内渲染；ok/null/缺省=零渲染（无「连接中断」文案）
 *
 * 形态说明（沿 WindRose.test.tsx 组件测试先例的零 jsdom 红线；直调元素树
 * 对本件不适用——TaskPanel 含 useState/useMutation hook，无渲染器直调必抛
 * Invalid hook call——改经 react-dom/server renderToString 服务端渲染真
 * antd 树（node 可用零 DOM），queryByText 等价=HTML 串包含断言）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TaskPanel } from "./TaskPanel";

/** SSR 渲染壳（QueryClientProvider——useCancelTask mutation 上下文需求）。 */
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

/** 渲染 TaskPanel 至 HTML 串（connection 提示面单变量——其余必需 props 恒定）。 */
function renderTaskPanel(
  connection?: "reconnecting" | "probing" | "ok" | null,
): string {
  return renderToString(
    <QueryClientProvider client={queryClient}>
      <TaskPanel
        taskId="task-b7-panel"
        view={null}
        status={null}
        statusError={null}
        connection={connection}
      />
    </QueryClientProvider>,
  );
}

describe("TaskPanel connection 提示行（B7 D4）", () => {
  it("reconnecting=「连接中断，自动重连中…」warning 行内渲染", () => {
    const html = renderTaskPanel("reconnecting");
    expect(html).toContain("连接中断，自动重连中…");
    // G1-03/G2-02：warning 形态锚（type="warning" 误改 danger/层级漂移可捕获）
    expect(html).toContain("ant-typography-warning");
  });

  it("probing=「连接中断，每 60 秒重试一次…」warning 行内渲染", () => {
    const html = renderTaskPanel("probing");
    expect(html).toContain("连接中断，每 60 秒重试一次…");
    expect(html).toContain("ant-typography-warning");
  });

  it("ok/null/缺省=零渲染（无连接中断文案——queryByText null 等价断言）", () => {
    expect(renderTaskPanel("ok")).not.toContain("连接中断");
    expect(renderTaskPanel(null)).not.toContain("连接中断");
    expect(renderTaskPanel()).not.toContain("连接中断");
    expect(renderTaskPanel(null)).not.toContain("ant-typography-warning");
  });
});
