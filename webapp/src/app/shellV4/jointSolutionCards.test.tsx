/**
 * @vitest-environment jsdom
 *
 * v4 联合方案卡测试（B2 R1 回炉 R1b——d1-B1/k2-W3：apply 序列 ?task= 回写
 * 重读×kind 门=卡列塌空；修复=粘滞 joint 视图（?task= 深链语义保留给
 * dock 聚焦）+部分失败错误面（d1-W4）+非法载荷错误面（W-失败面族））。
 *
 * 输入:  JointSolutionCards（任务状态/apply 两 hook 模块替身——?task= 随
 *        URL 实况切换返回 recalc/joint 两态）+联合枚举夹具（combos 2）
 * 输出:  断言族：①卡面（J 编号/★首位/摘要）②apply 序列逐单元
 *        mutateAsync+末任务 ?task= 回写+TASK_EVENT ③R1b 修复面：?task=
 *        已变 recalc（kind 门失守源）后卡列仍在场可连点 ④部分失败=错误
 *        面（wp-v4-joint-error）+重试重发 ⑤非法载荷=错误面非伪空态
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { JointSolutionCards } from "./jointSolutionCards";
import { TASK_EVENT } from "../../shared/events";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  /** 任务状态按 ?task= 实况返回（joint done / recalc done 两态）。 */
  statusByTask: {} as Record<string, unknown>,
  applySeq: [] as Array<Record<string, unknown>>,
  applyFailAt: -1,
  applied: vi.fn(),
}));

vi.mock("../../shared/api/generated/calc/calc", () => ({
  // 键=hook 实参（发现通道〔?task= URL〕与视图通道〔粘滞 id〕各自取数——
  // 非按 URL 全局返回：粘滞视图语义正在被测）
  useGetTaskStatusApiCalcTasksTaskIdGet: (taskId: string) => ({
    data: taskId ? (gate.statusByTask[taskId] ?? null) : null,
    isError: false,
    error: null,
  }),
  useApplySolutionApiCalcSolutionsApplyPost: () => ({
    mutateAsync: async (input: Record<string, unknown>) => {
      gate.applySeq.push(input);
      const index = gate.applySeq.length - 1;
      if (gate.applyFailAt === index) {
        throw new Error("单元写入失败（锁冲突）");
      }
      return { project_id: "p1", new_hash: "h2", design_changed: true, recalc_task_id: "t-recalc" };
    },
    isError: false,
    error: null,
    isPending: false,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

const JOINT_STATUS = {
  task_id: "t-joint-1",
  kind: "joint_enumerate",
  state: "done",
  progress: 1.0,
  stage: "rows",
  condition_key: null,
  stale: false,
  error: null,
  error_type: null,
  result: {
    combos: [
      {
        params: { municipal_aao: { srt: 14, n: 3 }, municipal_cass: { n: 2 } },
        feasible: true,
        sensitivity_degraded: false,
        failed_conditions: [],
        metrics: { cost_opex_yuan_a: 1.5 },
        score: 1.5,
      },
      {
        params: { municipal_aao: { srt: 16, n: 3 }, municipal_cass: { n: 4 } },
        feasible: true,
        sensitivity_degraded: false,
        failed_conditions: [],
        metrics: { cost_opex_yuan_a: 2.0 },
        score: 2.0,
      },
    ],
    diagnosis: null,
    unit_ids: ["municipal_aao", "municipal_cass"],
  },
  project_id: "p1",
};
/** 空态引导文案（组件内 NO_JOINT_HINT 镜像——断言用）。 */
const NO_JOINT_TEXT = "联合方案在联合枚举后呈现";
const RECALC_STATUS = {
  task_id: "t-recalc",
  kind: "calc",
  state: "done",
  progress: 1.0,
  stage: "done",
  condition_key: null,
  stale: false,
  error: null,
  error_type: null,
  result: { design_hash: "h2" },
  project_id: "p1",
};

function renderCards() {
  return render(
    <QueryClientProvider client={queryClient}>
      <JointSolutionCards projectId="p1" onApplied={gate.applied} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.applySeq = [];
  gate.applyFailAt = -1;
  gate.applied.mockClear();
  gate.statusByTask = { "t-joint-1": JOINT_STATUS };
  window.history.replaceState(null, "", "/?task=t-joint-1&ia=v4");
});
afterEach(cleanup);

describe("联合方案卡·R1b 修复面", () => {
  it("卡面：J 编号+★首位+参数摘要（截断提示——共 N 项显示前 M）", () => {
    const { container } = renderCards();
    const section = container.querySelector('[data-testid="wp-v4-joint-cards"]');
    expect(section?.textContent).toContain("全厂 · 联合方案（联合枚举 2）");
    expect(section?.textContent).toContain("J01");
    expect(section?.textContent).toContain("★");
  });

  it("apply 序列逐单元 mutateAsync+末任务 ?task= 回写（TASK_EVENT 派发）", async () => {
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");
    const { container } = renderCards();
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]')!,
    );
    await vi.waitFor(() => {
      expect(gate.applySeq.length).toBe(2);
    });
    expect(gate.applySeq[0]?.data).toEqual({
      project_id: "p1",
      unit_id: "municipal_aao",
      params: { srt: 14, n: 3 },
    });
    expect(gate.applySeq[1]?.data).toEqual({
      project_id: "p1",
      unit_id: "municipal_cass",
      params: { n: 2 },
    });
    expect(new URLSearchParams(window.location.search).get("task")).toBe(
      "t-recalc",
    );
    expect(dispatchSpy).toHaveBeenCalled();
    dispatchSpy.mockRestore();
  });

  it("R1b 核心：?task= 已变 recalc（kind 门失守源）后卡列仍在场可连点", async () => {
    const { container } = renderCards();
    // 深链 ?task=t-joint-1 → 卡在场
    expect(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
    ).not.toBeNull();
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]')!,
    );
    await vi.waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("task")).toBe(
        "t-recalc",
      );
    });
    gate.statusByTask["t-recalc"] = RECALC_STATUS;
    // 回写+TASK_EVENT 重读后（旧实现 kind 门即塌空）——粘滞视图下卡列仍在
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t-recalc" }));
    await vi.waitFor(() => {
      expect(
        container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
      ).not.toBeNull();
    });
    expect(
      container.querySelector('[data-testid="wp-v4-joint-card-J02"]'),
    ).not.toBeNull();
  });

  it("部分失败=错误面（wp-v4-joint-error）+重试全量重发（apply 幂等）", async () => {
    gate.applyFailAt = 1; // 第二单元失败——首单元已写保留
    const { container } = renderCards();
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]')!,
    );
    await vi.waitFor(() => {
      expect(
        container.querySelector('[data-testid="wp-v4-joint-error"]'),
      ).not.toBeNull();
    });
    expect(
      container.querySelector('[data-testid="wp-v4-joint-error"]')?.textContent,
    ).toContain("失败");
    // 重试：全量重发（apply 幂等——已写单元同参数重写无害）
    gate.applyFailAt = -1;
    fireEvent.click(container.querySelector('[data-testid="wp-v4-joint-retry"]')!);
    await vi.waitFor(() => {
      expect(gate.applySeq.length).toBe(4); // 首轮 2 + 重试 2
    });
    expect(
      container.querySelector('[data-testid="wp-v4-joint-error"]'),
    ).toBeNull();
  });

  it("非法载荷=错误面（非伪空态文案）", () => {
    gate.statusByTask["t-joint-1"] = {
      ...JOINT_STATUS,
      result: { combos: "not-an-array", diagnosis: null, unit_ids: [] },
    };
    const { container } = renderCards();
    const error = container.querySelector('[data-testid="wp-v4-joint-error"]');
    expect(error).not.toBeNull();
    expect(error?.textContent).toContain("载荷");
  });
});

describe("联合方案卡·R2 回炉（粘滞持久/project 守卫/failed 分面）", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("R2a：apply 后 ?task= 已变 recalc→卸载重挂（右栏切页同径）→卡列仍粘滞在场", async () => {
    const first = renderCards();
    fireEvent.click(first.container.querySelector('[data-testid="wp-v4-joint-card-J01"]')!);
    await vi.waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("task")).toBe("t-recalc");
    });
    first.unmount(); // 右栏切「选中工艺」页=卸载（designZone 条件渲染）
    gate.statusByTask["t-recalc"] = RECALC_STATUS;
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t-recalc" }));
    // 切回「全厂」页重挂——?task= 仍指 recalc（非 joint）：粘滞须跨卸载持久
    const second = renderCards();
    await vi.waitFor(() => {
      expect(
        second.container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
      ).not.toBeNull();
    });
    expect(
      second.container.querySelector('[data-testid="wp-v4-joint-card-J02"]'),
    ).not.toBeNull();
    second.unmount();
  });

  it("R2b：发现通道 project_id≠prop 不收养（防跨项目误粘）", () => {
    gate.statusByTask["t-joint-9"] = {
      ...JOINT_STATUS,
      task_id: "t-joint-9",
      project_id: "p9", // 他项目任务——不得收养为本项目粘滞
    };
    window.history.replaceState(null, "", "/?task=t-joint-9");
    const { container } = renderCards();
    expect(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
    ).toBeNull(); // 不出卡（空态面）
    expect(container.textContent).toContain(NO_JOINT_TEXT);
    // 粘滞未收养：sessionStorage 无本项目键
    expect(window.sessionStorage.getItem("wp-v4-joint-sticky-p1")).toBeNull();
  });

  it("R2b：粘滞视图 project_id 漂移（他项目键残留）不渲染且清粘滞", () => {
    // 预置他项目来源的粘滞（跨项目键残留面——守卫须拒）
    window.sessionStorage.setItem("wp-v4-joint-sticky-p1", "t-joint-9");
    gate.statusByTask["t-joint-9"] = {
      ...JOINT_STATUS,
      task_id: "t-joint-9",
      project_id: "p9",
    };
    window.history.replaceState(null, "", "/"); // 无 ?task=——纯粘滞通道
    const { container } = renderCards();
    expect(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
    ).toBeNull();
    expect(container.textContent).toContain(NO_JOINT_TEXT);
  });

  it("R2c：?task= 指向 failed joint 任务=错误面（不得以旧粘滞卡列冒充当前结果）", () => {
    // 先建立粘滞（成功 joint 在册）
    window.history.replaceState(null, "", "/?task=t-joint-1");
    const warm = renderCards();
    expect(
      warm.container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
    ).not.toBeNull();
    warm.unmount();
    // ?task= 切向 failed joint——错误面优先于粘滞卡列
    gate.statusByTask["t-joint-f"] = {
      ...JOINT_STATUS,
      task_id: "t-joint-f",
      state: "failed",
      error: "联合网格超限（>1e6 组合）",
      result: null,
    };
    window.history.replaceState(null, "", "/?task=t-joint-f");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t-joint-f" }));
    const { container } = renderCards();
    const error = container.querySelector('[data-testid="wp-v4-joint-error"]');
    expect(error).not.toBeNull();
    expect(error?.textContent).toContain("联合网格超限");
    // 旧粘滞卡列不冒充当前结果（failed 为当前面）
    expect(
      container.querySelector('[data-testid="wp-v4-joint-card-J01"]'),
    ).toBeNull();
  });
});
