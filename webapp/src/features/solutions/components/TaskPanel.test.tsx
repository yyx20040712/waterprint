/**
 * TaskPanel connection 提示行测试（B7 D4）+done 态进度归一（FIX-ACC1①）。
 *
 * 输入:  TaskPanel（taskId/view/status/statusError 必需面+connection 提示面
 *        +view.state/percent 进度面）
 * 输出:  reconnecting=「连接中断，自动重连中…」/probing=「连接中断，每 60
 *        秒重试一次…」行内渲染；ok/null/缺省=零渲染（无「连接中断」文案）；
 *        done 态进度条显示 100%（服务端终值 75% 的显示层归一——三阶段
 *        percent=(index+1)/(total+1) 上界 3/4 且 done 事件不再发射 100%）；
 *        cancelled/failed 保留诚实末值不覆写
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
import type { TaskView } from "../lib/taskFeed";

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

/** 进度面渲染（view 单变量——FIX-ACC1① 断言载体）。 */
function renderTaskPanelView(view: TaskView): string {
  return renderToString(
    <QueryClientProvider client={queryClient}>
      <TaskPanel
        taskId="task-fixacc1"
        view={view}
        status={null}
        statusError={null}
        connection={null}
      />
    </QueryClientProvider>,
  );
}

/** 最小 TaskView 工厂（state/percent 两变量——其余终态缺省）。 */
function viewOf(state: string, percent: number | null): TaskView {
  return { state, percent, stage: "", error: null, stale: false };
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

describe("TaskPanel done 态进度归一（FIX-ACC1①）", () => {
  it("done+末值 75% → 进度条显示 100%（服务端三阶段上界 3/4 的显示层归一）", () => {
    const html = renderTaskPanelView(viewOf("done", 0.75));
    expect(html).toContain("100%");
    expect(html).not.toContain("75%");
  });

  it("running+75% → 保留 75%（在途诚实末值不覆写）", () => {
    const html = renderTaskPanelView(viewOf("running", 0.75));
    expect(html).toContain("75%");
  });

  it("cancelled+75% → 保留 75%（半途语义——终态徽标定性，进度不虚报）", () => {
    const html = renderTaskPanelView(viewOf("cancelled", 0.75));
    expect(html).toContain("75%");
  });

  it("done+percent null → 满格完成态进度条（aria-valuenow=100——任务确已完成非伪造）", () => {
    const html = renderTaskPanelView(viewOf("done", null));
    expect(html).toContain("ant-progress");
    expect(html).toContain('aria-valuenow="100"');
  });
});
