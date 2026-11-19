/**
 * @vitest-environment jsdom
 *
 * v4 参数方案区测试（b2 壳重组批联合枚举入口流迁入；b3 功能面重涂批
 * 2026-11-19：+对象树选中通道〔点行→onSelectedUnitChange 写 ?node= 同
 * 源〕——稿 parameters.html 左栏语境侧栏语义）。
 *
 * 输入:  ParametersZone（子面/取数面全替身——枚举 Modal/方案卡/参数
 *        面板/回填区 stub 零渲染）+JointSubmitForm 真件（生成钩子+两
 *        查询替身——mutate 即触发 onSuccess 模拟成功回合）
 * 输出:  断言族：①全厂页 wp-v4-joint-open 在场+点击→wp-v4-joint-modal
 *        开+JointSubmitForm 在场（Select+提交钮 disabled 零选态）②选
 *        两单元→提交→mutate 载荷 {project_id,unit_ids}+TASK_EVENT 派发
 *        （detail=task_id）+Modal 关（jsdom 无 transition 事件——离场
 *        motion 类为开态翻转证）③无项目态=入口钮 disabled（⟳ 钮同款
 *        守卫 parity）④分析面入口组跨入口导航（工况对比→compare/
 *        其余→analysis——onOpenCompare/onOpenAnalysis 调用）
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TASK_EVENT } from "../../shared/events";
import { ParametersZone } from "./parametersZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** localStorage 存根（本环境 jsdom 面无原生方法族——侧栏宽度持久读
 *  +tokenSettings 令牌回显消费；Map 薄壳足量三函数面）。 */
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
  openAnalysis: vi.fn(),
  openCompare: vi.fn(),
  openProcess: vi.fn(),
  selectedChange: vi.fn(),
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
// parametersZone 子面 stub（本测面=右栏联合入口+Modal——其余面零渲染）
vi.mock("../../features/params/components/AssumptionsPanel", () => ({
  AssumptionsPanel: () => null,
}));
vi.mock("../../features/params/components/ParamForm", () => ({
  ParamForm: () => null,
}));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("./solutionCards", () => ({ SolutionCards: () => null }));
vi.mock("./jointSolutionCards", () => ({ JointSolutionCards: () => null }));
vi.mock("./backfillSection", () => ({ BackfillSection: () => null }));
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

function renderParameters() {
  return render(
    <QueryClientProvider client={queryClient}>
      <ParametersZone
        selectedUnitId="municipal_aao"
        onSelectedUnitChange={gate.selectedChange}
        onOpenProcess={gate.openProcess}
        onOpenAnalysis={gate.openAnalysis}
        onOpenCompare={gate.openCompare}
      />
    </QueryClientProvider>,
  );
}

/** 全厂页+开联合枚举 Modal（Select 交互沿 FdInlinePanel 先例：mouseDown
 *  .ant-select 开下拉+点 option 文本）。 */
async function openJointModal() {
  const view = renderParameters();
  fireEvent.click(screen.getByRole("button", { name: "全厂联合" }));
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
  gate.openAnalysis.mockClear();
  gate.openCompare.mockClear();
  gate.openProcess.mockClear();
  gate.selectedChange.mockClear();
});
afterEach(cleanup);

describe("联合枚举入口（B3 U2——b2 迁 parametersZone）", () => {
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
      // 下拉 option 域选择器（对象树/pane-head 同名文本并存——Select 选项
      // 专属类域消歧）
      const optionOf = (text: string): HTMLElement => {
        const hit = Array.from(
          document.querySelectorAll<HTMLElement>(".ant-select-item-option-content"),
        ).find((option) => option.textContent?.includes(text));
        if (hit === undefined) {
          throw new Error(`下拉选项缺席：${text}`);
        }
        return hit;
      };
      fireEvent.click(await waitFor(() => optionOf("AAO 生物池")));
      fireEvent.click(await waitFor(() => optionOf("CASS 生物池")));
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
      // 事件桥：TASK_EVENT 派发（detail=task_id——任务条/联合卡承接面）
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
    renderParameters();
    fireEvent.click(screen.getByRole("button", { name: "全厂联合" }));
    const open = screen.getByTestId("wp-v4-joint-open") as HTMLButtonElement;
    expect(open.disabled).toBe(true);
  });
});

describe("工艺对象树（b3——选中通道与画布同源）", () => {
  it("对象树在场：单元行中文名+id 副行；点行=onSelectedUnitChange(unitId)", () => {
    renderParameters();
    const row = document.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-obj-municipal_aao"]',
    );
    expect(row).not.toBeNull();
    expect(row?.textContent).toContain("AAO 生物池");
    expect(row?.textContent).toContain("municipal_aao");
    // 选中态类：选中单元行 .selected
    expect(row?.classList.contains("selected")).toBe(true);
    fireEvent.click(
      document.querySelector<HTMLButtonElement>(
        '[data-testid="wp-v4-obj-municipal_cass"]',
      ) as HTMLButtonElement,
    );
    expect(gate.selectedChange).toHaveBeenCalledWith("municipal_cass");
  });
});

describe("分析面入口组（b2——跨入口导航接线）", () => {
  it("工况对比→onOpenCompare；灵敏度/概算/可信度/高程纵断→onOpenAnalysis", () => {
    renderParameters();
    fireEvent.click(screen.getByRole("button", { name: "全厂联合" }));
    const entries = document.querySelectorAll<HTMLButtonElement>(
      '[data-region="parameters-right"] [data-entry-target]',
    );
    expect(entries.length).toBe(5);
    const byLabel = (label: string): HTMLButtonElement => {
      const hit = Array.from(entries).find((entry) =>
        entry.textContent?.includes(label),
      );
      if (hit === undefined) {
        throw new Error(`入口 ${label} 缺席`);
      }
      return hit;
    };
    fireEvent.click(byLabel("工况对比"));
    expect(gate.openCompare).toHaveBeenCalledTimes(1);
    expect(gate.openAnalysis).not.toHaveBeenCalled();
    fireEvent.click(byLabel("灵敏度"));
    fireEvent.click(byLabel("概算"));
    fireEvent.click(byLabel("可信度"));
    fireEvent.click(byLabel("高程纵断"));
    expect(gate.openAnalysis).toHaveBeenCalledTimes(4);
    expect(gate.openCompare).toHaveBeenCalledTimes(1);
  });
});
