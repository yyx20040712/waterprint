/**
 * @vitest-environment jsdom
 *
 * 项目名 hook 测试（v2-20261015 笔3——useProjectName 新建+rawProjectName
 * 自 reportZone 71-81 迁入单源；状态条项目名消费面的行为冻结）。
 *
 * 输入:  useProjectName（useProjectId+生成项目读 hook 模块替身——
 *        reportZone.test 制式）+rawProjectName 纯函数直测
 * 输出:  断言族：①未选项目=null（enabled=false 门——不发起取数）②有
 *        项目=raw 名直出③pending/失败/空白名/缺名=「未命名项目」回退
 *        ④rawProjectName 纯函数宽容取名（非对象/缺 view/非串/空白→null/
 *        合法名去空白）
 */
import { cleanup, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { rawProjectName, useProjectName } from "./useProjectName";

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
  projectRaw: undefined as unknown,
  lastCall: null as { id: string; enabled: boolean } | null,
}));

vi.mock("./useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
vi.mock("../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: (id: string, opts?: { query?: { enabled?: boolean } }) => {
    gate.lastCall = { id, enabled: opts?.query?.enabled ?? true };
    return { data: gate.projectRaw, isLoading: gate.projectRaw === undefined };
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function mountHook() {
  return renderHook(() => useProjectName(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

beforeEach(() => {
  gate.projectId = "p1";
  gate.projectRaw = undefined;
  gate.lastCall = null;
});
afterEach(cleanup);

describe("useProjectName·hook 面（D3）", () => {
  it("未选项目=返回 null（enabled=false 门——不发起取数）", () => {
    gate.projectId = null;
    const { result } = mountHook();
    expect(result.current).toBeNull();
    expect(gate.lastCall?.id).toBe("");
    expect(gate.lastCall?.enabled).toBe(false);
  });

  it("有项目=raw 名直出（enabled 门开——zoneBand 90-92 同制）", () => {
    gate.projectRaw = { project_id: "p1", view: { name: "城南污水处理厂扩建工程" } };
    const { result } = mountHook();
    expect(result.current).toBe("城南污水处理厂扩建工程");
    expect(gate.lastCall?.id).toBe("p1");
    expect(gate.lastCall?.enabled).toBe(true);
  });

  it("取数未就绪（pending）=「未命名项目」回退", () => {
    gate.projectRaw = undefined;
    const { result } = mountHook();
    expect(result.current).toBe("未命名项目");
  });

  it("空白名/缺 view=「未命名项目」回退（不裸露 id 前缀）", () => {
    gate.projectRaw = { project_id: "p1", view: { name: "   " } };
    expect(mountHook().result.current).toBe("未命名项目");
    cleanup();
    gate.projectRaw = { project_id: "p1" };
    expect(mountHook().result.current).toBe("未命名项目");
  });
});

describe("rawProjectName·纯函数面（reportZone 71-81 迁入零漂移）", () => {
  it("非对象/缺 view/view 非对象= null", () => {
    expect(rawProjectName(undefined)).toBeNull();
    expect(rawProjectName(null)).toBeNull();
    expect(rawProjectName("str")).toBeNull();
    expect(rawProjectName({ project_id: "p1" })).toBeNull();
    expect(rawProjectName({ view: "flat" })).toBeNull();
  });

  it("name 非串/空白串=null；合法名=trim 直出", () => {
    expect(rawProjectName({ view: { name: 42 } })).toBeNull();
    expect(rawProjectName({ view: { name: "" } })).toBeNull();
    expect(rawProjectName({ view: { name: "  " } })).toBeNull();
    expect(rawProjectName({ view: { name: "  城南厂  " } })).toBe("城南厂");
  });
});
