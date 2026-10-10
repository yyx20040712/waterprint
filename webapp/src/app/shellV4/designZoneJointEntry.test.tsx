/**
 * @vitest-environment jsdom
 *
 * v4 联合枚举入口组件测试（B3 任务书 §三.U5——designZone jointEntry 流：
 * 全厂页→wp-v4-joint-open→Modal 开+JointSubmitForm 在场〔生成钩子替身〕
 * →提交流→TASK_EVENT 派发+Modal 关）。
 *
 * 输入:  DesignZone（子面/取数面全替身——枚举 Modal/方案卡/画布/dock 等
 *        stub 零渲染）+JointSubmitForm 真件（生成钩子+两查询替身——
 *        mutate 即触发 onSuccess 模拟成功回合）
 * 输出:  断言族：①全厂页 wp-v4-joint-open 在场+点击→wp-v4-joint-modal
 *        开+JointSubmitForm 在场（Select+提交钮 disabled 零选态）②选
 *        两单元→提交→mutate 载荷 {project_id,unit_ids}+TASK_EVENT 派发
 *        （detail=task_id）+Modal 关（jsdom 无 transition 事件——离场
 *        motion 类为开态翻转证）③无项目态=入口钮 disabled（⟳ 钮同款
 *        守卫 parity）
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TASK_EVENT } from "../../shared/events";
import { DesignZone } from "./designZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** localStorage 存根（本环境 jsdom 面无原生方法族——designZone 侧栏宽度
 *  持久读+tokenSettings 令牌回显消费；Map 薄壳足量三函数面，沿
 *  useExportArtifact.test 先例）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
});

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
  joint: {
    config: null as {
      mutation?: { onSuccess?: (response: { task_id: string }) => void };
    } | null,
    mutateCalls: [] as unknown[],
  },
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
// designZone 子面 stub（本测面=右栏联合入口+Modal——其余面零渲染）
vi.mock("../../features/params/components/AssumptionsPanel", () => ({
  AssumptionsPanel: () => null,
}));
vi.mock("../../features/params/components/ParamForm", () => ({
  ParamForm: () => null,
}));
vi.mock("./thumbnailFlow", () => ({ ThumbnailFlow: () => null }));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("./analysisPane", () => ({ AnalysisPane: () => null }));
vi.mock("./solutionCards", () => ({ SolutionCards: () => null }));
vi.mock("./jointSolutionCards", () => ({ JointSolutionCards: () => null }));
vi.mock("./backfillSection", () => ({ BackfillSection: () => null }));
vi.mock("./dockBar", () => ({ DockBar: () => null }));
// JointSubmitForm 依赖面（生成钩子替身——mutate 即 onSuccess 成功回合）
vi.mock("../../features/solutions/api/useProjectUnits", () => ({
  useProjectUnits: () => ({
    data: [
      { unitId: "municipal_aao", kind: null },
      { unitId: "municipal_cass", kind: null },
    ],
    isLoading: false,
    isError: false,
    error: null,
  }),
}));
vi.mock("../../features/params/api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({
    data: {
      units: [
        {
          unit_id: "municipal_aao",
          name_zh: "AAO 生物池",
          params: [{ field_id: "n", grid: [2, 3, 4] }],
        },
        {
          unit_id: "municipal_cass",
          name_zh: "CASS 生物池",
          params: [{ field_id: "n", grid: [2, 4] }],
        },
      ],
    },
    isLoading: false,
    isError: false,
    error: null,
  }),
}));
vi.mock("../../shared/api/generated/solution/solution", () => ({
  useRunJointEnumerationApiSolutionJointEnumeratePost: (config: unknown) => {
    gate.joint.config = config as typeof gate.joint.config;
    return {
      mutate: (variables: unknown) => {
        gate.joint.mutateCalls.push(variables);
        gate.joint.config?.mutation?.onSuccess?.({ task_id: "t-joint-b3" });
      },
      isPending: false,
      isError: false,
      error: null,
    };
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderDesign() {
  return render(
    <QueryClientProvider client={queryClient}>
      <DesignZone
        target={{ zone: "design", subpage: "canvas" }}
        selectedUnitId="municipal_aao"
        onSelectedUnitChange={() => {}}
        onSubpageChange={() => {}}
        onDockNavigate={() => {}}
      />
    </QueryClientProvider>,
  );
}

/** 全厂页+开联合枚举 Modal（Select 交互沿 FdInlinePanel 先例：mouseDown
 *  .ant-select 开下拉+点 option 文本）。 */
async function openJointModal() {
  const view = renderDesign();
  fireEvent.click(screen.getByRole("button", { name: "全厂" }));
  fireEvent.click(screen.getByTestId("wp-v4-joint-open"));
  const modal = await waitFor(() => {
    const el = document.querySelector('[data-testid="wp-v4-joint-modal"]');
    expect(el).not.toBeNull();
    return el;
  });
  return { view, modal };
}

beforeEach(() => {
  gate.projectId = "p1";
  gate.joint.config = null;
  gate.joint.mutateCalls.length = 0;
});
afterEach(cleanup);

describe("联合枚举入口（B3 U2）", () => {
  it("全厂页→wp-v4-joint-open→Modal 开+JointSubmitForm 在场（零选态提交钮 disabled）", async () => {
    await openJointModal();
    const submit = screen.getByRole("button", { name: "提交联合枚举" });
    expect((submit as HTMLButtonElement).disabled).toBe(true);
    expect(document.querySelector(".ant-select")).not.toBeNull();
    expect(screen.getByText("至少选 2 个可枚举单元（无档位参数项不可选）。")).not.toBeNull();
  });

  it("提交流：选两单元→mutate 载荷+TASK_EVENT 派发（detail=task_id）+Modal 关", async () => {
    const taskSpy = vi.fn();
    window.addEventListener(TASK_EVENT, taskSpy);
    try {
      await openJointModal();
      // antd v6 Select jsdom 交互：根 mouseDown 开下拉+点 option 文本
      // （Modal 门户挂 document.body——Select 查询域=document 非视图容器）
      fireEvent.mouseDown(document.querySelector(".ant-select") as HTMLElement);
      fireEvent.click(await screen.findByText("AAO 生物池"));
      fireEvent.click(await screen.findByText("CASS 生物池"));
      const submit = screen.getByRole("button", { name: "提交联合枚举" });
      expect((submit as HTMLButtonElement).disabled).toBe(false);
      fireEvent.click(submit);
      // 载荷：project_id+两单元（options 判据全可枚举）
      expect(gate.joint.mutateCalls).toEqual([
        {
          data: {
            project_id: "p1",
            unit_ids: ["municipal_aao", "municipal_cass"],
          },
        },
      ]);
      // 事件桥：TASK_EVENT 派发（detail=task_id——v4 任务条/联合卡承接面）
      expect(taskSpy).toHaveBeenCalledTimes(1);
      const firstCall = taskSpy.mock.calls[0] as [CustomEvent<string>] | undefined;
      expect(firstCall?.[0].detail).toBe("t-joint-b3");
      // onSubmitted→Modal 关（jsdom 无 transition 事件——物理卸载不可实测，
      // 以 antd 离场 motion 类为开态翻转证：open=false 即入 leave 态）
      await waitFor(() => {
        expect(
          document.querySelector(
            '[data-testid="wp-v4-joint-modal"] .ant-fade-leave, [data-testid="wp-v4-joint-modal"] .ant-zoom-leave',
          ),
        ).not.toBeNull();
      });
    } finally {
      window.removeEventListener(TASK_EVENT, taskSpy);
    }
  });

  it("无项目态=入口钮 disabled（⟳ 钮同款守卫 parity）", () => {
    gate.projectId = null;
    renderDesign();
    fireEvent.click(screen.getByRole("button", { name: "全厂" }));
    const open = screen.getByTestId("wp-v4-joint-open") as HTMLButtonElement;
    expect(open.disabled).toBe(true);
  });
});
