/**
 * @vitest-environment jsdom
 *
 * 布置编辑器组装件测试（V4 P3 待摆/已摆中文化——uiglobal A3=in-register
 * A4）：SiteplanPane 真件渲染（取数面模块替身），断言=待摆区/选中侧栏
 * 单元显示名走 catalog name_zh 单源（查表键=kind ?? unitId——
 * thumbnailFlow metaByUnit 同口径），悬浮 title=原 id。
 *
 * 输入:  SiteplanPane（useSiteData/保存 hook/间距 hook/目录 hook 模块
 *        替身+GOLDEN 夹具〔inlet→kind=municipal_input 已摆+aao1→kind=
 *        municipal_aao 待摆〕；siteplanStore 真件）
 * 输出:  断言族：①待摆列表条目=中文名（市政输入已摆不在列）+title=原
 *        unit_id②已摆面（选中侧栏头+间距行对端）同映射③查表键口径：
 *        kind 命中 catalog（inlet≠municipal_input——键归 kind）
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { useSiteplanStore } from "../store/siteplanStore";
import { SiteplanPane } from "./SiteplanPane";

/** golden 夹具（vi.hoisted——mock 工厂闭包同源）：inlet（kind=
 *  municipal_input）已摆+aao1（kind=municipal_aao）待摆——查表键=kind
 *  口径的实证面（节点 id ≠ catalog 键）。 */
const GOLDEN_RAW = vi.hoisted(() => ({
  project_id: "p1",
  design: {
    nodes: {
      inlet: { kind: "municipal_input", q_avg_daily: 50000 },
      aao1: { kind: "municipal_aao" },
    },
    site: {
      structures: {
        inlet: { x: 10, y: 20, rotation: 0, ground_elevation: null },
      },
      roads: [],
      corridors: [],
      options: {},
    },
  },
}));

vi.mock("../api/useSiteData", () => ({
  useSiteData: () => ({
    projectQuery: { data: GOLDEN_RAW, isError: false },
    sceneQuery: { data: null, isError: false, isSuccess: false },
  }),
}));
vi.mock("../../../shared/api/generated/projects/projects", () => ({
  useSaveProjectApiProjectsProjectIdPut: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
}));
vi.mock("../../../shared/api/generated/site/site", () => ({
  useGetSpacingApiSiteSpacingGet: () => ({ data: null }),
}));
// P3 目录替身（select=unitNameIndex 投影后形态——catalog name_zh 单源）
vi.mock("../../../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: { municipal_input: "市政输入", municipal_aao: "AAO 生物池" },
  }),
}));

beforeEach(() => {
  useSiteplanStore.getState().setSelection(null);
  useSiteplanStore.getState().setTool("select");
});
afterEach(cleanup);

/** 挂载（QueryClient 供给——useQueryClient 消费面；reportZone.test 同制）。 */
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
function mountPane() {
  return render(
    <QueryClientProvider client={queryClient}>
      <SiteplanPane projectId="p1" />
    </QueryClientProvider>,
  );
}

describe("布置编辑器·V4 待摆列表中文化（P3）", () => {
  it("待摆条目=中文名+悬浮 title=原 unit_id（拖拽载荷仍=id）", () => {
    const { container } = mountPane();
    const items = Array.from(
      container.querySelectorAll<HTMLElement>("aside > div[draggable]"),
    );
    expect(items.length).toBe(1); // inlet 已摆——仅 aao1 待摆
    expect(items[0]?.textContent).toContain("AAO 生物池");
    expect(items[0]?.textContent).not.toContain("aao1");
    expect(items[0]?.getAttribute("title")).toBe("aao1"); // 悬浮=原 id
  });

  it("查表键=kind ?? unitId：inlet→municipal_input→市政输入（已摆面同映射）", () => {
    useSiteplanStore.getState().setSelection({ kind: "structure", id: "inlet" });
    const { container } = mountPane();
    const sidebar = Array.from(container.querySelectorAll("aside")).find((aside) =>
      aside.textContent?.includes("选中构筑物"),
    );
    expect(sidebar).not.toBeNull();
    const nameLine = sidebar?.querySelector<HTMLElement>("div[title]");
    expect(nameLine?.textContent).toContain("市政输入"); // kind 命中 catalog 键
    expect(nameLine?.getAttribute("title")).toBe("inlet"); // 悬浮=原 id
  });
});
