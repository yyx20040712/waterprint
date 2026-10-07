/**
 * @vitest-environment jsdom
 *
 * 席位任务分页测试（M7 批 2026-10-07——面板轨接线复刻旧 solutionsPane：
 * 双轨初值+TASK_EVENT 重读（同值早退）+切项目守卫+connection 重置+SSE 终态
 * 二段刷新+opsdebug 三件入席折叠段）。
 *
 * 输入:  SeatTaskPage（URL 经 history.replaceState 摆位——真 useProjectId/
 *        真 projectParam 消费；vi.mock 边界沿 paneDomainGate 纪律=feature
 *        api 模块面〔useTaskFeed/useOpsChainQuery〕+generated 面无害空数据，
 *        禁 mock react-query 内部/antd——TaskPanel/OpsChainView 原件真渲染
 *        =零改消费实证；QueryClientProvider 每用例新 client retry:false，
 *        invalidateQueries 经 vi.spyOn 观测）
 * 输出:  断言组：①双轨初值（task 优先/缺省回落 enum）；②空态引导+TaskPanel
 *        不挂载；③TASK_EVENT 重读新值生效；④同值早退（useTaskFeed taskId
 *        调用序列零新增）；⑤切项目守卫（初挂载早退保深链+切项目置 null）；
 *        ⑥SSE 终态回调=invalidate `/api/calc/tasks/{id}`+再派发 TASK_EVENT
 *        （AUDIT2-R R3 二段刷新）+ops-chain 键失效；⑦connection 态随任务
 *        变更重置；⑧ops 折叠段在场默认收拢+展开三态（空态/error 404 分级
 *        引导/loading/OpsChainView）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SeatTaskPage } from "./seatTaskPage";
import { PROJECT_EVENT, TASK_EVENT } from "../shared/events";
import { WaterprintApiError } from "../shared/api/http";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写；react-query v5 常读
 *  字段族沿 paneDomainGate D4 口径补齐：pending 语义=data undefined）。 */
const gate = vi.hoisted(() => {
  const idle = () => ({
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
    isPending: true,
    isLoading: true,
    isFetching: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  });
  return {
    status: idle(),
    ops: idle(),
    taskFeedTaskIds: [] as (string | null)[],
    onTerminal: null as ((state: string) => void) | null,
    onConnection: null as ((state: "reconnecting" | "probing" | "ok" | "polling") => void) | null,
  };
});

vi.mock("../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: (
    taskId: string | null,
    onTerminal?: (state: string) => void,
    onConnection?: (state: "reconnecting" | "probing" | "ok" | "polling") => void,
  ) => {
    gate.taskFeedTaskIds.push(taskId);
    gate.onTerminal = onTerminal ?? null;
    gate.onConnection = onConnection ?? null;
    return null;
  },
}));
vi.mock("../features/opsdebug/api/useOpsChainQuery", () => ({
  useOpsChainQuery: () => gate.ops,
}));
vi.mock("../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => gate.status,
  useCancelTaskApiCalcTasksTaskIdCancelPost: () => ({
    mutate: () => {},
    isPending: false,
  }),
}));
vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isPending: true,
    isLoading: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  }),
}));

/** URL 摆位+每用例新 QueryClient（invalidate 经 spy 观测）。 */
function renderTaskPage(search: string) {
  window.history.replaceState(null, "", search === "" ? "/" : `/?${search}`);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const invalidateSpy = vi.spyOn(client, "invalidateQueries");
  const view = render(<SeatTaskPage />, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
  return { view, invalidateSpy };
}

/** 最小合法 OpsChainReport（窄化产物形态——tasks 空+latest_calc null）。 */
function minimalOpsReport() {
  return {
    project_id: "p1",
    tasks: [],
    latest_calc: null,
  };
}

beforeEach(() => {
  gate.taskFeedTaskIds.length = 0;
  gate.onTerminal = null;
  gate.onConnection = null;
  gate.ops = {
    data: undefined,
    isError: false,
    error: null,
    isPending: true,
    isLoading: true,
    isFetching: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  };
  window.history.replaceState(null, "", "/");
});
afterEach(cleanup);

describe("面板轨双轨初值（复刻旧 solutionsPane L145-148）", () => {
  it("task 优先：?task=&?enum= 并存→TaskPanel 挂 task 轨值", () => {
    renderTaskPage("project=p1&task=t1&enum=e1");
    expect(screen.getByText(/任务 t1…/)).toBeTruthy();
    expect(screen.queryByText(/任务 e1…/)).toBeNull();
  });

  it("缺省回落 enum：仅 ?enum=e1→面板挂 e1", () => {
    renderTaskPage("project=p1&enum=e1");
    expect(screen.getByText(/任务 e1…/)).toBeTruthy();
  });

  it("空态引导：无 task/enum→引导文案在场+TaskPanel 不挂载", () => {
    renderTaskPage("project=p1");
    expect(
      screen.getByText(
        "尚未跟踪任务——顶部『提交计算』/枚举提交后，进度与终态在此呈现",
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/任务 .+…/)).toBeNull();
  });
});

describe("TASK_EVENT 重读（复刻 L173-186——URL 单一真相重读比对）", () => {
  it("URL 写新 task 后派发→面板挂新值（运行期轨道跟随）", async () => {
    renderTaskPage("project=p1&task=t1");
    expect(screen.getByText(/任务 t1…/)).toBeTruthy();
    window.history.replaceState(null, "", "/?project=p1&task=t2");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t2" }));
    await waitFor(() => {
      expect(screen.getByText(/任务 t2…/)).toBeTruthy();
    });
  });

  it("同值早退：URL 未变派发→useTaskFeed taskId 序列零新增（零扰动）", () => {
    renderTaskPage("project=p1&task=t1");
    const callsBefore = gate.taskFeedTaskIds.length;
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t1" }));
    expect(gate.taskFeedTaskIds.length).toBe(callsBefore);
    expect(gate.taskFeedTaskIds[gate.taskFeedTaskIds.length - 1]).toBe("t1");
  });
});

describe("切项目守卫（复刻 L176-190——prevProject 初挂载早退+切项目重置）", () => {
  it("初挂载早退保深链初值：渲染即挂 t1（守卫不误清）", () => {
    renderTaskPage("project=p1&task=t1");
    expect(screen.getByText(/任务 t1…/)).toBeTruthy();
  });

  it("切项目→panelTaskId 置 null：空态文案回场（withProjectParam 剔除 task/enum 语义）", async () => {
    renderTaskPage("project=p1&task=t1");
    window.history.replaceState(null, "", "/?project=p2");
    window.dispatchEvent(new CustomEvent(PROJECT_EVENT, { detail: "p2" }));
    await waitFor(() => {
      expect(
        screen.getByText(
          "尚未跟踪任务——顶部『提交计算』/枚举提交后，进度与终态在此呈现",
        ),
      ).toBeTruthy();
    });
  });
});

describe("SSE 面板轨（复刻 L205-235——终态二段刷新+connection 重置）", () => {
  it("onTerminal=invalidate `/api/calc/tasks/{id}` 快照+再派发 TASK_EVENT+ops-chain 键失效", async () => {
    const { invalidateSpy } = renderTaskPage("project=p1&task=t1");
    expect(gate.onTerminal).not.toBeNull();
    let reDispatched = 0;
    const onReDispatch = () => {
      reDispatched += 1;
    };
    window.addEventListener(TASK_EVENT, onReDispatch);
    try {
      (gate.onTerminal as (state: string) => void)("done");
    } finally {
      window.removeEventListener(TASK_EVENT, onReDispatch);
    }
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ["/api/calc/tasks/t1"],
      });
    });
    expect(reDispatched).toBe(1);
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["/api/debug/ops-chain/p1"],
    });
  });

  it("connection 态随 panelTaskId 变更重置：中断提示随任务切换退场", async () => {
    renderTaskPage("project=p1&task=t1");
    // onConnection→setConnection：中断提示行在场（TaskPanel 呈现）
    (gate.onConnection as (s: "reconnecting") => void)("reconnecting");
    await waitFor(() => {
      expect(screen.getByText("连接中断，自动重连中…")).toBeTruthy();
    });
    // 任务切换（URL 新值+TASK_EVENT）→connection 置 null→提示退场
    window.history.replaceState(null, "", "/?project=p1&task=t2");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t2" }));
    await waitFor(() => {
      expect(screen.queryByText("连接中断，自动重连中…")).toBeNull();
    });
    expect(screen.getByText(/任务 t2…/)).toBeTruthy();
  });
});

describe("opsdebug 三件入席折叠段（装配复刻旧 opsDebugPane）", () => {
  it("折叠段在场+默认收拢：wp-seat-ops+「操作链诊断」header 在场，内容未挂载", () => {
    renderTaskPage("project=p1&task=t1");
    expect(screen.getByTestId("wp-seat-ops")).toBeTruthy();
    expect(screen.getByText("操作链诊断")).toBeTruthy();
    expect(screen.queryByTestId("wp-ops-chain-view")).toBeNull();
    expect(screen.queryByText("正在加载操作链观测面…")).toBeNull();
  });

  it("展开后 projectId null→空态提示（诊断面针对项目装配）", () => {
    renderTaskPage("");
    fireEvent.click(screen.getByText("操作链诊断"));
    expect(screen.getByText("尚未选择项目——请先在画布槽选择项目")).toBeTruthy();
  });

  it("展开后查询 loading→加载文案在场", () => {
    renderTaskPage("project=p1");
    fireEvent.click(screen.getByText("操作链诊断"));
    expect(screen.getByText("正在加载操作链观测面…")).toBeTruthy();
  });

  it("展开后 404（WaterprintApiError code=ProjectNotFoundError）→错误段+「检查项目」引导在场", () => {
    gate.ops = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError("ProjectNotFoundError", "项目不存在"),
      isPending: false,
      isLoading: false,
      isFetching: false,
      status: "error",
      refetch: () => Promise.resolve({}),
    };
    renderTaskPage("project=p1");
    fireEvent.click(screen.getByText("操作链诊断"));
    expect(screen.getByText(/操作链观测面取数失败：项目不存在/)).toBeTruthy();
    expect(screen.getByText(/项目不存在，请检查当前项目是否已被删除或改名/)).toBeTruthy();
  });

  it("展开后网络错（非 404 code）→错误段在场不挂「检查项目」引导", () => {
    gate.ops = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError("NetworkError", "网络中断探针"),
      isPending: false,
      isLoading: false,
      isFetching: false,
      status: "error",
      refetch: () => Promise.resolve({}),
    };
    renderTaskPage("project=p1");
    fireEvent.click(screen.getByText("操作链诊断"));
    expect(screen.getByText(/操作链观测面取数失败：网络中断探针/)).toBeTruthy();
    expect(screen.queryByText(/请检查当前项目是否已被删除或改名/)).toBeNull();
  });

  it("展开后数据就绪→OpsChainView 挂载（零改原件消费）", () => {
    gate.ops = {
      data: minimalOpsReport(),
      isError: false,
      error: null,
      isPending: false,
      isLoading: false,
      isFetching: false,
      status: "success",
      refetch: () => Promise.resolve({}),
    };
    renderTaskPage("project=p1");
    fireEvent.click(screen.getByText("操作链诊断"));
    expect(screen.getByTestId("wp-ops-chain-view")).toBeTruthy();
  });
});
