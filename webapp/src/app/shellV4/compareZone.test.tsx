/**
 * @vitest-environment jsdom
 *
 * v4 工况区测试（b4 功能面重涂 II 批——稿 compare.html 两栏重制）：
 * 左栏工况与基准〔活动工况列开关+锁定基准视图态〕+右栏矩阵面板〔单元
 * 筛选+CompareMatrix 接线〕；数据面全替身（compare 查询/项目/单元目录
 * /StaleBanner），CompareMatrix 真件渲染（矩阵消费面契约）。
 *
 * 输入:  CompareZone（useCompareQuery/useProjectId/units hook/StaleBanner
 *        模块替身）+双工况双单元夹具报告
 * 输出:  断言族：①锁定为基准=视图态接线（钮→pinned ★ 在场+左栏锁定
 *        区条目+hash 副行）②活动工况行点击=列移出（列头缺席）再点
 *        恢复 ③单元筛选=行过滤（select 变更后另一单元行缺席）④重算
 *        后 hash 变化=「基准已过期」徽标（isPinStale 视图态语义）
 *        ⑤解除锁定=★ 清空回未锁定空态
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CompareZone } from "./compareZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** antd responsive observer 存根（projectsZone.test 同先例）。 */
window.matchMedia =
  window.matchMedia ??
  ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as MediaQueryList);

/** 夹具报告（双工况双单元——列开关/单元筛选两轴可断言）。 */
const reportOf = (designHash: string) => ({
  project_id: "p1",
  task_id: "t1-c0ffee",
  stale: false,
  design_hash: designHash,
  engine_version: "e",
  data_version: "d",
  condition_keys: ["avg", "design"],
  metrics: [
    {
      unit_id: "municipal_aao",
      field_id: "v_o",
      label_zh: "好氧区容积",
      dim: "V",
      values: { avg: 15568, design: 19460 },
    },
    {
      unit_id: "municipal_erchunchi",
      field_id: "q_surf",
      label_zh: "表面负荷",
      dim: "Q",
      values: { avg: 1.1, design: 1.4 },
    },
  ],
  warnings: [
    { unit_id: "municipal_aao", counts: { avg: 1, design: 1 } },
  ],
});

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写；report 初值 beforeEach 填）。 */
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
  report: null as { design_hash: string } | null,
  queryError: null as unknown,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
vi.mock("../../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => ({
    data: gate.report,
    isError: gate.queryError !== null,
    error: gate.queryError,
  }),
}));
vi.mock("../../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: { municipal_aao: "AAO 生物池", municipal_erchunchi: "辐流二沉池" },
  }),
}));
vi.mock("./analysisPane", () => ({
  StaleBanner: () => <div data-testid="wp-v4-stale-stub" />,
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function mountZone() {
  return render(
    <QueryClientProvider client={queryClient}>
      <CompareZone />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.projectId = "p1";
  gate.report = reportOf("hash-1");
  gate.queryError = null;
});
afterEach(cleanup);

describe("锁定基准（视图态接线——稿「锁定是视图操作」语义）", () => {
  it("锁定为基准：★ 在场+左栏锁定区条目（工况名+hash 副行）", () => {
    const { container, getByTestId } = mountZone();
    expect(getByTestId("wp-v4-compare-pin-empty").textContent).toContain("未锁定");
    fireEvent.click(getByTestId("wp-v4-compare-pin-set"));
    // 矩阵列头 ★（CompareMatrix 真件——两工况列均锁定）
    const headers = container.querySelectorAll("thead th");
    const headerText = [...headers].map((th) => th.textContent ?? "").join("|");
    expect(headerText).toContain("平均日 ★");
    expect(headerText).toContain("最高日最高时 ★");
    // 左栏锁定区条目（filterLivePins live 面——hash 副行截 8 位）
    const region = container.querySelector('[data-region="compare-conditions"]');
    expect(region?.textContent).toContain("hash-1");
    expect(region?.textContent).toContain("仍有效");
  });

  it("解除锁定=★ 清空回未锁定空态", () => {
    const { container, getByTestId } = mountZone();
    fireEvent.click(getByTestId("wp-v4-compare-pin-set"));
    fireEvent.click(getByTestId("wp-v4-compare-pin-clear"));
    expect(getByTestId("wp-v4-compare-pin-empty").textContent).toContain("未锁定");
    const headers = container.querySelectorAll("thead th");
    expect([...headers].map((th) => th.textContent ?? "").join("|")).not.toContain("★");
  });

  it("重算后 hash 变化=「基准已过期」徽标（isPinStale 视图态语义）", () => {
    const { getByTestId, rerender } = mountZone();
    fireEvent.click(getByTestId("wp-v4-compare-pin-set"));
    // 模拟重算完成：报告 hash 变化（同 task 键数据刷新）
    gate.report = reportOf("hash-2");
    rerender(
      <QueryClientProvider client={queryClient}>
        <CompareZone />
      </QueryClientProvider>,
    );
    const region = getByTestId("wp-v4-compare-plant");
    expect(region.textContent).toContain("基准已过期");
    expect(region.textContent).toContain("已过期");
  });
});

describe("活动工况列开关（客户端视图过滤）", () => {
  it("点击工况行=该列移出矩阵（列头缺席），再点恢复", () => {
    const { container, getByTestId } = mountZone();
    const headerText = () =>
      [...container.querySelectorAll("thead th")].map((th) => th.textContent ?? "").join("|");
    expect(headerText()).toContain("平均日");
    fireEvent.click(getByTestId("wp-v4-compare-cond-avg"));
    expect(headerText()).not.toContain("平均日");
    expect(headerText()).toContain("最高日最高时");
    fireEvent.click(getByTestId("wp-v4-compare-cond-avg"));
    expect(headerText()).toContain("平均日");
  });

  it("全列移出=锁定钮禁用（disabled 属性）", () => {
    const { getByTestId } = mountZone();
    fireEvent.click(getByTestId("wp-v4-compare-cond-avg"));
    fireEvent.click(getByTestId("wp-v4-compare-cond-design"));
    expect(getByTestId("wp-v4-compare-pin-set").hasAttribute("disabled")).toBe(true);
  });
});

describe("单元筛选（metrics unit_id 集数据驱动）", () => {
  it("筛选 AAO=二沉池行缺席；回全部单元恢复", () => {
    const { container, getByTestId } = mountZone();
    const bodyText = () => container.querySelector("tbody")?.textContent ?? "";
    expect(bodyText()).toContain("辐流二沉池");
    fireEvent.change(getByTestId("wp-v4-compare-unit-filter"), {
      target: { value: "municipal_aao" },
    });
    expect(bodyText()).toContain("好氧区容积");
    expect(bodyText()).not.toContain("辐流二沉池");
    fireEvent.change(getByTestId("wp-v4-compare-unit-filter"), {
      target: { value: "" },
    });
    expect(bodyText()).toContain("辐流二沉池");
  });
});
